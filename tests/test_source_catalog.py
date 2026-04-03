from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from the_big_learn import flashcards
from the_big_learn import source_catalog
from the_big_learn.bundled_sources import BUNDLED_SOURCES


WIKISOURCE_HTML = """
<html>
  <head>
    <title>四書章句集註/中庸章句 - 維基文庫，自由的圖書館</title>
  </head>
  <body>
    <div class="mw-parser-output">
      <p>版本說明。</p>
      <dd>右第一章。天命之謂性。</dd>
      <p>天命之謂性；率性之謂道；修道之謂教。</p>
      <dd>右第二章。君子中庸。</dd>
      <p>仲尼曰：「君子中庸；小人反中庸。」</p>
    </div>
  </body>
</html>
"""


CTEXT_HTML = """
<html>
  <head>
    <title>四書章句集注 : 大學章句 - Chinese Text Project</title>
  </head>
  <body>
    <table>
      <tr id="n1"><td class="ctext opt">大學章句:</td><td class="ctext">題名</td></tr>
      <tr id="n2"><td class="ctext opt">大學章句:</td><td class="ctext">右經一章，蓋孔子之言。</td></tr>
      <tr id="n3"><td align="right"><a class="popup">1</a></td><td class="ctext opt">大學章句:</td><td class="ctext">大學之道，在明明德，在親民。</td></tr>
      <tr id="n4"><td class="ctext opt">大學章句:</td><td class="ctext">右傳之首章。釋明明德。</td></tr>
      <tr id="n5"><td align="right"><a class="popup">2</a></td><td class="ctext opt">大學章句:</td><td class="ctext">康誥曰：「克明德。」</td></tr>
    </table>
  </body>
</html>
"""

CTEXT_HTML_WITH_CONTROLS = """
<html>
  <head>
    <title>四書章句集注 : 中庸章句 - Chinese Text Project</title>
  </head>
  <body>
    <table>
      <tr id="n1">
        <td align="right"><a title="Jump to dictionary">Jump to dictionary</a></td>
        <td class="ctext opt">中庸章句:</td>
        <td class="ctext">右第一章。天命之謂性。</td>
      </tr>
      <tr id="n2">
        <td align="right"><a class="popup">1</a><a title="Jump to dictionary">Jump to dictionary</a></td>
        <td class="ctext opt"></td>
        <td class="ctext">天命之謂性；率性之謂道；修道之謂教。</td>
      </tr>
    </table>
  </body>
</html>
"""

CTEXT_HTML_WITH_INTERLEAVED_COMMENTARY = """
<html>
  <head>
    <title>四書章句集注 : 中庸章句 - Chinese Text Project</title>
  </head>
  <body>
    <table>
      <tr id="n1">
        <td class="ctext opt">中庸章句:</td>
        <td class="ctext">中者，不偏不倚也。</td>
      </tr>
      <tr id="n2">
        <td align="right"><a class="popup">1</a></td>
        <td class="ctext opt">中庸章句:</td>
        <td class="ctext"><span class="original">天命之謂性，率性之謂道。</span>命，猶令也。<span class="original">脩道之謂教。</span></td>
      </tr>
      <tr id="n3">
        <td class="ctext opt"></td>
        <td class="ctext"><span class="original">右第一章。子思述所傳之意。</span><p class="ctext"></p></td>
      </tr>
      <tr id="n4">
        <td align="right"><a class="popup">2</a></td>
        <td class="ctext opt">中庸章句:</td>
        <td class="ctext"><span class="original">仲尼曰：「君子中庸。」</span>王肅本作反中庸。<span class="original">君子而時中。</span></td>
      </tr>
      <tr id="n5">
        <td class="ctext opt"></td>
        <td class="ctext"><span class="original">右第二章。</span>此下十章，皆論中庸。</td>
      </tr>
    </table>
  </body>
</html>
"""


class SourceCatalogTests(unittest.TestCase):
    def test_source_cache_dir_uses_readable_work_id_for_bundled_sources(self) -> None:
        self.assertEqual(
            source_catalog.source_cache_dir(BUNDLED_SOURCES["lunyu"]["source_url"]).name,
            "lunyu",
        )
        self.assertEqual(
            source_catalog.packaged_source_cache_dir(BUNDLED_SOURCES["lunyu"]["source_url"]).name,
            "lunyu",
        )
        self.assertEqual(
            source_catalog.source_cache_dir("https://ctext.org/demo").name,
            source_catalog._source_store_key("https://ctext.org/demo"),
        )

    def test_build_source_catalog_parses_wikisource_blocks(self) -> None:
        source_url = "https://zh.wikisource.org/wiki/demo"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=WIKISOURCE_HTML,
        ):
            catalog = source_catalog.build_source_catalog(source_url)
            self.assertTrue(Path(catalog["catalog_path"]).exists())

        self.assertEqual(catalog["provider"], "wikisource-html")
        self.assertEqual(catalog["chapter_count"], 2)
        self.assertEqual(catalog["chapters"][0]["title"], "右第一章")
        self.assertEqual(catalog["chapters"][0]["summary"], "天命之謂性")
        self.assertNotIn("text", catalog["chapters"][0])
        self.assertTrue(catalog["chapters"][0]["chapter_path"].endswith("chapter-001.json"))

    def test_build_source_catalog_parses_ctext_rows(self) -> None:
        source_url = "https://ctext.org/demo"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=CTEXT_HTML,
        ):
            catalog = source_catalog.build_source_catalog(source_url)

        self.assertEqual(catalog["provider"], "ctext-html")
        self.assertEqual(catalog["chapter_count"], 2)
        self.assertEqual(catalog["chapters"][0]["title"], "右經一章")
        self.assertEqual(catalog["chapters"][1]["title"], "右傳之首章")
        self.assertNotIn("text", catalog["chapters"][1])
        self.assertTrue(catalog["chapters"][1]["chapter_path"].endswith("chapter-002.json"))

    def test_build_source_catalog_saves_lightweight_catalog_without_chapter_text(self) -> None:
        source_url = "https://ctext.org/demo"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=CTEXT_HTML,
        ):
            catalog = source_catalog.build_source_catalog(source_url)
            saved = json.loads(Path(catalog["catalog_path"]).read_text(encoding="utf-8"))

        self.assertEqual(saved["chapter_count"], 2)
        self.assertNotIn("text", saved["chapters"][0])
        self.assertNotIn("supplemental_text", saved["chapters"][0])
        self.assertEqual(saved["chapters"][0]["reading_unit_count"], 1)
        self.assertTrue(saved["chapters"][0]["chapter_path"].endswith("chapter-001.json"))

    def test_normalized_catalog_payload_rewrites_commentary_paths(self) -> None:
        source_url = "https://ctext.org/demo"
        payload = {
            "provider": "ctext-html",
            "source_url": source_url,
            "title": "Demo",
            "chapter_count": 1,
            "chapters": [
                {
                    "id": "chapter-001",
                    "order": 1,
                    "title": "正文",
                    "summary": "摘要",
                    "character_count": 4,
                    "text": "正文",
                }
            ],
            "commentary_chapter_count": 1,
            "commentary_chapters": [
                {
                    "id": "commentary-introduction",
                    "order": 0,
                    "title": "朱熹序與總說",
                    "summary": "《大學章句》序與經一章總說",
                    "character_count": 10,
                    "commentary_path": "/tmp/old-machine/commentary-introduction.json",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            catalog_file = Path(tmp) / "catalog.json"
            normalized = source_catalog._normalized_catalog_payload(source_url, payload, catalog_file)

        self.assertEqual(normalized["commentary_chapter_count"], 1)
        self.assertEqual(
            normalized["commentary_chapters"][0]["commentary_path"],
            str(Path(tmp) / "commentary" / "commentary-introduction.json"),
        )

    def test_download_source_chapter_saves_selected_chapter_locally(self) -> None:
        source_url = "https://ctext.org/demo"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=CTEXT_HTML,
        ):
            payload = source_catalog.download_source_chapter(source_url, "2")
            saved = json.loads(Path(payload["chapter_path"]).read_text(encoding="utf-8"))
            self.assertTrue(Path(payload["chapter_path"]).exists())

        self.assertEqual(payload["chapter"]["order"], 2)
        self.assertEqual(saved["source_url"], source_url)
        self.assertEqual(saved["chapter"]["title"], "右傳之首章")
        self.assertEqual(saved["schema_version"], 2)
        self.assertEqual(saved["chapter"]["reading_unit_count"], 1)
        self.assertEqual(saved["chapter"]["reading_units"][0]["id"], "chapter-002-line-001")
        self.assertEqual(saved["chapter"]["reading_units"][0]["source_block_order"], 1)

    def test_build_source_reading_pass_splits_saved_chapter_into_lines(self) -> None:
        source_url = "https://ctext.org/demo"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=CTEXT_HTML,
        ):
            reading_pass = source_catalog.build_source_reading_pass(source_url, "2")

        self.assertEqual(reading_pass["mode"], "raw-source")
        self.assertEqual(reading_pass["chapter"]["title"], "右傳之首章")
        self.assertEqual(reading_pass["line_count"], 1)
        self.assertEqual(reading_pass["lines"][0]["id"], "chapter-002-line-001")
        self.assertEqual(reading_pass["lines"][0]["text"], "康誥曰：「克明德。」")
        self.assertEqual(reading_pass["lines"][0]["line_index_in_container"], 1)
        self.assertEqual(reading_pass["lines"][0]["container_line_count"], 1)

    def test_save_source_chapter_generated_annotations_persists_and_reloads_saved_annotations(self) -> None:
        source_url = "https://ctext.org/demo"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=CTEXT_HTML,
        ):
            source_catalog.download_source_chapter(source_url, "1")
            saved = source_catalog.save_source_chapter_generated_annotations(
                source_url,
                "chapter-001",
                [
                    {
                        "line_id": "chapter-001-line-001",
                        "layers": {
                            "pinyin": "dà xué zhī dào, zài míng míng dé, zài qīn mín.",
                            "translation_en": (
                                "The way of great learning lies in manifesting bright virtue and renewing the people."
                            ),
                        },
                        "notes": ["Saved from guided reading."],
                        "character_glosses_en": ["great learning", "way", "bright virtue", "renew the people"],
                    }
                ],
                saved_at=1712345678,
            )
            payload = source_catalog.load_saved_source_chapter(source_url, "chapter-001")
            reading_pass = source_catalog.build_source_reading_pass(source_url, "1")

        self.assertEqual(saved["saved_annotation_count"], 1)
        self.assertEqual(saved["line_ids"], ["chapter-001-line-001"])
        self.assertEqual(reading_pass["saved_annotation_count"], 1)
        self.assertEqual(reading_pass["lines"][0]["annotation_source"], "saved-generated")
        self.assertTrue(reading_pass["lines"][0]["has_saved_generated_annotation"])
        self.assertEqual(
            reading_pass["lines"][0]["layers"]["traditional"],
            "大學之道，在明明德，在親民。",
        )
        self.assertEqual(
            payload["chapter"]["reading_units"][0]["generated_annotation"]["layers"]["pinyin"],
            "dà xué zhī dào, zài míng míng dé, zài qīn mín.",
        )
        self.assertEqual(
            payload["chapter"]["reading_units"][0]["generated_annotation"]["layers"]["translation_en"],
            "The way of great learning lies in manifesting bright virtue and renewing the people.",
        )
        self.assertEqual(
            payload["chapter"]["reading_units"][0]["generated_annotation"]["saved_at"],
            1712345678,
        )
        self.assertEqual(
            reading_pass["lines"][0]["generated_annotation"]["notes"],
            ["Saved from guided reading."],
        )
        self.assertEqual(
            reading_pass["lines"][0]["layers"]["translation_en"],
            "The way of great learning lies in manifesting bright virtue and renewing the people.",
        )

    def test_build_source_reading_pass_can_reconstruct_line_shell_from_character_index(self) -> None:
        source_url = "https://ctext.org/demo-memory"
        chapter_payload = {
            "provider": "ctext-html",
            "source_url": source_url,
            "source_title": "Demo Memory Source",
            "chapter_path": "/tmp/chapter-001.json",
            "chapter": {
                "id": "chapter-001",
                "order": 1,
                "title": "學而第一",
                "character_count": 6,
                "reading_unit_count": 1,
                "reading_units": [
                    {
                        "id": "chapter-001-line-001",
                        "order": 1,
                        "text": "學而時習之。",
                        "character_count": 6,
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog.download_source_chapter",
            return_value=chapter_payload,
        ):
            flashcards.save_character_index_entries(
                "lunyu",
                "chapter-001",
                [
                    {
                        "id": "chapter-001-line-001",
                        "line_index_in_container": 1,
                        "layers": {
                            "traditional": "學而時習之。",
                            "simplified": "学而时习之。",
                            "zhuyin": "ㄒㄩㄝˊ ㄦˊ ㄕˊ ㄒㄧˊ ㄓ。",
                            "pinyin": "xué ér shí xí zhī.",
                            "gloss_en": "study; and; timely; practice; it",
                            "translation_en": "Study it and practice it in season.",
                        },
                        "character_glosses_en": ["study", "and", "timely", "practice", "it"],
                    }
                ],
                source_url=source_url,
            )
            reading_pass = source_catalog.build_source_reading_pass(source_url, "1")

        self.assertEqual(reading_pass["saved_annotation_count"], 0)
        self.assertEqual(reading_pass["saved_character_index_count"], 1)
        self.assertEqual(reading_pass["lines"][0]["annotation_source"], "saved-character-index")
        self.assertTrue(reading_pass["lines"][0]["has_saved_character_index_annotation"])
        self.assertEqual(reading_pass["lines"][0]["layers"]["simplified"], "学而时习之。")
        self.assertEqual(reading_pass["lines"][0]["layers"]["translation_en"], "Study it and practice it in season.")
        self.assertEqual(
            reading_pass["lines"][0]["character_glosses_en"],
            ["study", "and", "timely", "practice", "it"],
        )

    def test_build_source_reading_pass_strips_ctext_control_text(self) -> None:
        source_url = "https://ctext.org/demo-with-controls"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=CTEXT_HTML_WITH_CONTROLS,
        ):
            reading_pass = source_catalog.build_source_reading_pass(source_url, "1")

        self.assertEqual(reading_pass["line_count"], 1)
        self.assertNotIn("Jump to dictionary", reading_pass["lines"][0]["text"])
        self.assertEqual(reading_pass["lines"][0]["text"], "天命之謂性；率性之謂道；修道之謂教。")

    def test_build_source_reading_pass_uses_only_core_text_from_interleaved_commentary(self) -> None:
        source_url = "https://ctext.org/interleaved-commentary"

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            return_value=CTEXT_HTML_WITH_INTERLEAVED_COMMENTARY,
        ):
            catalog = source_catalog.build_source_catalog(source_url)
            reading_pass = source_catalog.build_source_reading_pass(source_url, "1")

        self.assertEqual(catalog["chapter_count"], 2)
        self.assertEqual(catalog["chapters"][0]["title"], "右第一章")
        self.assertNotIn("text", catalog["chapters"][0])
        self.assertNotIn("supplemental_text", catalog["chapters"][0])
        self.assertEqual(reading_pass["line_count"], 2)
        self.assertEqual(reading_pass["lines"][0]["line_index_in_container"], 1)
        self.assertEqual(reading_pass["lines"][1]["line_index_in_container"], 2)
        self.assertEqual(reading_pass["lines"][0]["container_line_count"], 2)
        self.assertEqual(reading_pass["lines"][0]["text"], "天命之謂性，率性之謂道。")
        self.assertEqual(reading_pass["lines"][1]["text"], "脩道之謂教。")
        self.assertNotIn("命，猶令也。", "\n".join(line["text"] for line in reading_pass["lines"]))
        self.assertNotIn("右第一章", "\n".join(line["text"] for line in reading_pass["lines"]))

    def test_build_source_catalog_uses_packaged_bundled_sources_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            side_effect=AssertionError("Bundled source catalogs should not fetch remote HTML."),
        ):
            for work, spec in BUNDLED_SOURCES.items():
                with self.subTest(work=work):
                    catalog = source_catalog.build_source_catalog(spec["source_url"])
                    self.assertEqual(catalog["chapter_count"], spec["chapter_count"])
                    self.assertTrue(Path(catalog["catalog_path"]).exists())
                    self.assertNotIn(str(Path(tmp)), catalog["catalog_path"])
                    self.assertIn(f"books/{work}/catalog.json", catalog["catalog_path"])
                    self.assertNotIn("text", catalog["chapters"][0])
                    self.assertIn("reading_unit_count", catalog["chapters"][0])

    def test_build_source_catalog_reads_legacy_hashed_local_cache_for_bundled_sources(self) -> None:
        source_url = BUNDLED_SOURCES["lunyu"]["source_url"]
        chapter_id = "chapter-001"

        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp) / "state"
            bundle_root = Path(tmp) / "bundle"
            legacy_dir = state_root / "source-store" / source_catalog._source_store_key(source_url)
            catalog_path = legacy_dir / "catalog.json"
            chapter_path = legacy_dir / "chapters" / f"{chapter_id}.json"

            raw_catalog = {
                "provider": "ctext-html",
                "source_url": source_url,
                "title": "Legacy Lunyu",
                "chapter_count": 1,
                "chapters": [
                    {
                        "id": chapter_id,
                        "order": 1,
                        "title": "學而第一",
                        "summary": "子曰學而時習之",
                        "character_count": 13,
                        "text": "子曰：「學而時習之，不亦說乎？」",
                    }
                ],
            }
            raw_chapter = {
                "provider": "ctext-html",
                "source_url": source_url,
                "source_title": "Legacy Lunyu",
                "chapter": raw_catalog["chapters"][0],
            }
            source_catalog._write_json_file(
                catalog_path,
                source_catalog._normalized_catalog_payload(source_url, raw_catalog, catalog_path),
            )
            source_catalog._write_json_file(
                chapter_path,
                source_catalog._normalized_chapter_payload(source_url, raw_chapter, chapter_path),
            )

            with patch(
                "the_big_learn.source_catalog.state_dir",
                return_value=state_root,
            ), patch(
                "the_big_learn.source_catalog.data_root",
                return_value=bundle_root,
            ), patch(
                "the_big_learn.source_catalog._fetch_source_html",
                side_effect=AssertionError("Legacy hashed cache should be read without fetching."),
            ):
                catalog = source_catalog.build_source_catalog(source_url)
                payload = source_catalog.download_source_chapter(source_url, "1")

        self.assertEqual(catalog["title"], "Legacy Lunyu")
        self.assertIn(source_catalog._source_store_key(source_url), catalog["catalog_path"])
        self.assertEqual(payload["chapter"]["title"], "學而第一")
        self.assertIn(source_catalog._source_store_key(source_url), payload["chapter_path"])

    def test_packaged_da_xue_catalog_exposes_classic_only_chapters_and_separate_commentary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            side_effect=AssertionError("Bundled source catalogs should not fetch remote HTML."),
        ):
            catalog = source_catalog.build_source_catalog(BUNDLED_SOURCES["da-xue"]["source_url"])
            payload = source_catalog.download_source_chapter(BUNDLED_SOURCES["da-xue"]["source_url"], "1")

        self.assertEqual(catalog["chapter_count"], 7)
        self.assertEqual(catalog["chapters"][0]["title"], "大學之道")
        self.assertEqual(catalog["commentary_chapter_count"], 11)
        self.assertEqual(catalog["commentary_chapters"][0]["title"], "朱熹序與總說")
        self.assertTrue(
            catalog["commentary_chapters"][0]["commentary_path"].endswith("commentary/commentary-introduction.json")
        )
        self.assertEqual(payload["chapter"]["title"], "大學之道")
        self.assertEqual(payload["chapter"]["text"], "大學之道，在明明德，在親民，在止於至善。")
        self.assertEqual(payload["chapter"]["reading_unit_count"], 1)
        self.assertNotIn("大學之書", payload["chapter"]["text"])
        commentary_payload = json.loads(Path(catalog["commentary_chapters"][0]["commentary_path"]).read_text(encoding="utf-8"))
        self.assertEqual(commentary_payload["schema_version"], 2)
        self.assertEqual(commentary_payload["commentary"]["title"], "朱熹序與總說")
        self.assertGreater(commentary_payload["commentary"]["reading_unit_count"], 0)
        self.assertTrue(commentary_payload["commentary_path"].endswith("commentary/commentary-introduction.json"))

    def test_download_source_chapter_uses_packaged_lunyu_chapter_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            side_effect=AssertionError("Bundled source chapters should not fetch remote HTML."),
        ):
            payload = source_catalog.download_source_chapter(BUNDLED_SOURCES["lunyu"]["source_url"], "1")

        self.assertEqual(payload["chapter"]["title"], "學而第一")
        self.assertIn("子曰：「學而時習之，不亦說乎？", payload["chapter"]["text"])
        self.assertGreater(payload["chapter"]["reading_unit_count"], 1)
        self.assertEqual(len(payload["chapter"]["reading_units"]), payload["chapter"]["reading_unit_count"])
        self.assertTrue(Path(payload["chapter_path"]).exists())
        self.assertNotIn(str(Path(tmp)), payload["chapter_path"])

    def test_download_source_chapter_uses_packaged_sanguo_chapter_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.source_catalog.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.source_catalog._fetch_source_html",
            side_effect=AssertionError("Bundled source chapters should not fetch remote HTML."),
        ):
            payload = source_catalog.download_source_chapter(BUNDLED_SOURCES["sanguo-yanyi"]["source_url"], "1")

        self.assertIn("宴桃園豪傑三結義", payload["chapter"]["title"])
        self.assertIn("滾滾長江東逝水", payload["chapter"]["text"])
        self.assertTrue(Path(payload["chapter_path"]).exists())
        self.assertNotIn(str(Path(tmp)), payload["chapter_path"])

    def test_detect_source_provider_rejects_unknown_host(self) -> None:
        with self.assertRaises(source_catalog.SourceCatalogError):
            source_catalog.detect_source_provider("https://example.com/book")


if __name__ == "__main__":
    unittest.main()
