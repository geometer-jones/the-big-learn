from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from the_big_learn import repository


TRADITIONAL_HTML = """
<div class="mw-content-ltr mw-parser-output" lang="zh-Hant" dir="ltr">
  <p>前言。</p>
  <p>學問之道。<span>〈注一〉</span>知止而後定。<span>〈注二〉</span>物有本末。<span>〈注三〉</span></p>
</div>
"""

SIMPLIFIED_HTML = """
<div class="mw-content-ltr mw-parser-output" lang="zh-Hans" dir="ltr">
  <p>前言。</p>
  <p>学问之道。<span>〈注一〉</span>知止而后定。<span>〈注二〉</span>物有本末。<span>〈注三〉</span></p>
</div>
"""


def _lookup_spec() -> dict:
    return {
        "work": "demo-work",
        "lookup": {
            "provider": "wikisource-html",
            "traditional_variant": "zh-hant",
            "simplified_variant": "zh-hans",
        },
        "defaults": {
            "source_variant": "demo-source",
            "annotation_profile": "modern-mandarin-reading",
            "provenance": {
                "title": "Demo Source",
                "author": "Demo Author",
                "source_url": "https://example.invalid/demo",
            },
        },
        "lines": [
            {
                "id": "demo-line-001",
                "section": "opening",
                "order": 1,
                "source_locator": {
                    "paragraph_index": 1,
                    "chunk_index": 0,
                },
                "layers": {
                    "zhuyin": "ㄒㄩㄝˊ ㄨㄣˋ ㄓ ㄉㄠˋ。",
                    "pinyin": "xué wèn zhī dào.",
                    "gloss_en": "the way of learning",
                    "translation_en": "The way of learning.",
                },
                "character_glosses_en": ["study", "learning", "of", "way"],
                "segments": [
                    {
                        "id": "demo-line-001-a",
                        "source_start": 0,
                        "source_end": 2,
                        "zhuyin": "ㄒㄩㄝˊ ㄨㄣˋ",
                        "pinyin": "xué wèn",
                        "gloss_en": "learning",
                    }
                ],
                "status": "draft",
            },
            {
                "id": "demo-line-002",
                "section": "opening",
                "order": 2,
                "source_locator": {
                    "paragraph_index": 1,
                    "chunk_index": 1,
                },
                "layers": {
                    "zhuyin": "ㄓ ㄓˇ ㄦˊ ㄏㄡˋ ㄉㄧㄥˋ。",
                    "pinyin": "zhī zhǐ ér hòu dìng.",
                    "gloss_en": "know where to stop, then settle",
                    "translation_en": "Know where to stop, then settle.",
                },
                "status": "draft",
            },
            {
                "id": "demo-line-003",
                "section": "opening",
                "order": 3,
                "source_locator": {
                    "paragraph_index": 1,
                    "chunk_index": 2,
                },
                "layers": {
                    "zhuyin": "ㄨˋ ㄧㄡˇ ㄅㄣˇ ㄇㄛˋ。",
                    "pinyin": "wù yǒu běn mò.",
                    "gloss_en": "things have roots and branches",
                    "translation_en": "Things have roots and branches.",
                },
                "status": "draft",
            },
        ],
    }


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        repository._fetch_variant_html.cache_clear()
        repository._load_variant_paragraph_chunks.cache_clear()

    def test_flashcard_policy_prioritizes_combined_reading_layer(self) -> None:
        policy = repository.load_flashcard_policy()
        prioritized_layers = {
            layer
            for pair in policy["default_priority_pairs"]
            for layer in (pair["prompt_layer"], pair["answer_layer"])
        }

        self.assertIn("reading", policy["supported_layers"])
        self.assertNotIn("zhuyin", policy["supported_layers"])
        self.assertNotIn("pinyin", policy["supported_layers"])
        self.assertIn("reading", prioritized_layers)

    def test_select_lines_by_range_prefers_inline_source_layers(self) -> None:
        spec = _lookup_spec()
        spec["lines"][0]["layers"]["traditional"] = "學問之道。"
        spec["lines"][0]["layers"]["simplified"] = "学问之道。"
        spec["lines"][0]["segments"][0]["traditional"] = "學問"
        spec["lines"][0]["segments"][0]["simplified"] = "学问"
        spec["lines"][1]["layers"]["traditional"] = "知止而後定。"
        spec["lines"][1]["layers"]["simplified"] = "知止而后定。"
        spec["lines"][2]["layers"]["traditional"] = "物有本末。"
        spec["lines"][2]["layers"]["simplified"] = "物有本末。"

        with tempfile.TemporaryDirectory() as tmp:
            lookup_path = Path(tmp) / "starter.annotations.json"
            lookup_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

            def unexpected_fetch(source_url: str, variant: str) -> str:
                raise AssertionError(f"Inline layers should skip fetches: {source_url} {variant}")

            with patch("the_big_learn.repository.annotation_spec_path_for_work", return_value=lookup_path), patch(
                "the_big_learn.repository._fetch_variant_html",
                side_effect=unexpected_fetch,
            ):
                lines = repository.select_lines_by_range("demo-work", start=1, end=1)

        self.assertEqual(lines[0]["layers"]["traditional"], "學問之道。")
        self.assertEqual(lines[0]["layers"]["simplified"], "学问之道。")
        self.assertEqual(lines[0]["character_glosses_en"], ["study", "learning", "of", "way"])
        self.assertEqual(lines[0]["segments"][0]["traditional"], "學問")
        self.assertEqual(lines[0]["segments"][0]["simplified"], "学问")

    def test_select_lines_by_range_hydrates_lookup_backed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lookup_path = Path(tmp) / "starter.annotations.json"
            lookup_path.write_text(json.dumps(_lookup_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

            def fake_fetch(source_url: str, variant: str) -> str:
                self.assertEqual(source_url, "https://example.invalid/demo")
                if variant == "zh-hant":
                    return TRADITIONAL_HTML
                if variant == "zh-hans":
                    return SIMPLIFIED_HTML
                raise AssertionError(f"Unexpected variant: {variant}")

            with patch("the_big_learn.repository.annotation_spec_path_for_work", return_value=lookup_path), patch(
                "the_big_learn.repository._fetch_variant_html",
                side_effect=fake_fetch,
            ):
                lines = repository.select_lines_by_range("demo-work", start=1, end=2)

        self.assertEqual([line["id"] for line in lines], ["demo-line-001", "demo-line-002"])
        self.assertEqual(lines[0]["layers"]["traditional"], "學問之道。")
        self.assertEqual(lines[0]["layers"]["simplified"], "学问之道。")
        self.assertEqual(lines[0]["segments"][0]["traditional"], "學問")
        self.assertEqual(lines[0]["segments"][0]["simplified"], "学问")
        self.assertEqual(lines[1]["layers"]["traditional"], "知止而後定。")
        self.assertEqual(lines[1]["layers"]["simplified"], "知止而后定。")

    def test_select_lines_by_range_reads_existing_source_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lookup_path = Path(tmp) / "starter.annotations.json"
            lookup_path.write_text(json.dumps(_lookup_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
            state_path = Path(tmp) / "state"

            with patch("the_big_learn.repository.annotation_spec_path_for_work", return_value=lookup_path), patch(
                "the_big_learn.repository.state_dir",
                return_value=state_path,
            ):
                repository._variant_store_path("https://example.invalid/demo", "zh-hant").parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                repository._variant_store_path("https://example.invalid/demo", "zh-hant").write_text(
                    TRADITIONAL_HTML,
                    encoding="utf-8",
                )
                repository._variant_store_path("https://example.invalid/demo", "zh-hans").write_text(
                    SIMPLIFIED_HTML,
                    encoding="utf-8",
                )

                with patch(
                    "the_big_learn.repository._download_variant_html",
                    side_effect=AssertionError("Existing source stores should skip downloads."),
                ):
                    lines = repository.select_lines_by_range("demo-work", start=1, end=2)

        self.assertEqual(lines[0]["layers"]["traditional"], "學問之道。")
        self.assertEqual(lines[0]["layers"]["simplified"], "学问之道。")
        self.assertEqual(lines[1]["layers"]["traditional"], "知止而後定。")
        self.assertEqual(lines[1]["layers"]["simplified"], "知止而后定。")

    def test_select_lines_by_range_downloads_and_persists_missing_source_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lookup_path = Path(tmp) / "starter.annotations.json"
            lookup_path.write_text(json.dumps(_lookup_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
            state_path = Path(tmp) / "state"

            def fake_download(source_url: str, variant: str) -> str:
                self.assertEqual(source_url, "https://example.invalid/demo")
                if variant == "zh-hant":
                    return TRADITIONAL_HTML
                if variant == "zh-hans":
                    return SIMPLIFIED_HTML
                raise AssertionError(f"Unexpected variant: {variant}")

            with patch("the_big_learn.repository.annotation_spec_path_for_work", return_value=lookup_path), patch(
                "the_big_learn.repository.state_dir",
                return_value=state_path,
            ), patch(
                "the_big_learn.repository._download_variant_html",
                side_effect=fake_download,
            ) as download_variant_html:
                lines = repository.select_lines_by_range("demo-work", start=1, end=2)
                traditional_store = repository._variant_store_path("https://example.invalid/demo", "zh-hant")
                simplified_store = repository._variant_store_path("https://example.invalid/demo", "zh-hans")
                self.assertTrue(traditional_store.exists())
                self.assertTrue(simplified_store.exists())
                self.assertIn("學問之道。", traditional_store.read_text(encoding="utf-8"))
                self.assertIn("学问之道。", simplified_store.read_text(encoding="utf-8"))

        self.assertEqual(download_variant_html.call_count, 2)
        self.assertEqual(lines[0]["layers"]["traditional"], "學問之道。")
        self.assertEqual(lines[0]["layers"]["simplified"], "学问之道。")


if __name__ == "__main__":
    unittest.main()
