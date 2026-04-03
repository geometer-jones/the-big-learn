from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from the_big_learn.claude_host import install_claude_skills
from the_big_learn.cli import main
from the_big_learn.flashcards import save_bank_entry


def _demo_bank_entry() -> dict:
    return {
        "id": "fc-da-xue-001-qin-min",
        "source_work": "da-xue",
        "source_line_ids": ["da-xue-zhangju-001"],
        "source_segment_ids": ["da-xue-zhangju-001-d"],
        "origin": {
            "kind": "learner-question",
            "question_id": "q-001",
            "note": "Learner asked about 亲民(親民).",
        },
        "layers": {
            "traditional": "親民",
            "simplified": "亲民",
            "zhuyin": "ㄑㄧㄣ ㄇㄧㄣˊ",
            "pinyin": "qīn mín",
            "gloss_en": "renew the people",
            "translation_en": "renew the people",
        },
        "eligible_prompt_layers": [
            "simplified",
            "traditional",
            "pinyin",
            "zhuyin",
            "gloss_en",
            "translation_en",
        ],
        "tags": ["da-xue", "learner-question"],
        "status": "draft",
        "citations": [
            {
                "work": "da-xue",
                "section": "chapter-001",
                "line_id": "chapter-001-line-001",
                "char_index": 1,
            }
        ],
    }


class CliTests(unittest.TestCase):
    def test_claude_install_reports_existing_destination_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            install_claude_skills(target=target)

            stderr = StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["claude", "install", "--target", str(target)])

        self.assertEqual(exit_code, 1)
        self.assertIn("Destination already exists:", stderr.getvalue())
        self.assertIn("Use --force to replace existing Claude Code skills.", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_codex_path_can_emit_json(self) -> None:
        stdout = StringIO()
        with patch("sys.stdout", stdout):
            exit_code = main(["codex", "path", "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["target"].endswith("/.codex/skills"))

    def test_source_catalog_command_renders_json(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.build_source_catalog",
            return_value={
                "title": "Demo Source",
                "provider": "ctext-html",
                "source_url": "https://ctext.org/demo",
                "chapter_count": 1,
                "catalog_path": "/tmp/catalog.json",
                "chapters": [{"order": 1, "title": "Chapter 1", "summary": "demo", "character_count": 42}],
            },
        ), patch("sys.stdout", stdout):
            exit_code = main(["source", "catalog", "--url", "https://ctext.org/demo", "--format", "json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["title"], "Demo Source")
        self.assertEqual(payload["chapter_count"], 1)

    def test_source_read_command_renders_json(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.build_source_reading_pass",
            return_value={
                "source_title": "Demo Source",
                "source_url": "https://ctext.org/demo",
                "chapter_path": "/tmp/chapter-001.json",
                "mode": "raw-source",
                "line_count": 1,
                "chapter": {"id": "chapter-001", "order": 1, "title": "Chapter 1"},
                "lines": [{"id": "chapter-001-line-001", "text": "大学之道，在明明德。"}],
            },
        ), patch("sys.stdout", stdout):
            exit_code = main(["source", "read", "--url", "https://ctext.org/demo", "--chapter", "1", "--format", "json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["mode"], "raw-source")
        self.assertEqual(payload["lines"][0]["id"], "chapter-001-line-001")

    def test_progress_save_command_writes_guided_reading_artifacts(self) -> None:
        payload = {
            "work": "da-xue",
            "section": "chapter-001",
            "personal_translation_en": "My chapter translation.",
            "personal_response_en": "My chapter response.",
            "saved_at": 1712345678,
        }
        stdout = StringIO()
        demo_catalog = {
            "chapters": [
                {
                    "id": "chapter-001",
                    "order": 1,
                    "title": "Chapter 1",
                    "character_count": 16,
                    "reading_unit_count": 1,
                }
            ]
        }
        demo_chapter = {
            "chapter": {
                "reading_units": [
                    {"id": "chapter-001-line-001", "text": "大学之道，在明明德。"},
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=demo_catalog,
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=demo_chapter,
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout), patch(
            "sys.stdin",
            StringIO(json.dumps(payload)),
        ):
            exit_code = main(["progress-save", "--format", "json"])
            saved_payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["work"], "da-xue")
        self.assertTrue(result["saved_translation"])
        self.assertTrue(result["saved_response"])
        self.assertEqual(
            saved_payload["books"]["da-xue"]["chapters"]["chapter-001"]["personal_response_en"],
            "My chapter response.",
        )

    def test_progress_save_command_can_persist_generated_annotations(self) -> None:
        payload = {
            "work": "lunyu",
            "section": "chapter-001",
            "personal_translation_en": "My chapter translation.",
            "generated_annotations": [
                {
                    "line_id": "chapter-001-line-001",
                    "layers": {
                        "pinyin": "zǐ yuē",
                    },
                }
            ],
            "saved_at": 1712345678,
        }
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value={
                "chapters": [
                    {
                        "id": "chapter-001",
                        "order": 1,
                        "title": "學而第一",
                        "character_count": 493,
                        "reading_unit_count": 1,
                    }
                ]
            },
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value={
                "chapter": {
                    "reading_units": [
                        {"id": "chapter-001-line-001", "text": "子曰：「學而時習之，不亦說乎？」"},
                    ]
                }
            },
        ), patch(
            "the_big_learn.cli.save_chapter_generated_annotations",
            return_value={
                "chapter_id": "chapter-001",
                "chapter_path": str(Path(tmp) / "books" / "lunyu" / "chapters" / "chapter-001.json"),
                "saved_annotation_count": 1,
                "line_ids": ["chapter-001-line-001"],
            },
        ) as save_chapter_generated_annotations, redirect_stderr(StringIO()), patch(
            "sys.stdout",
            stdout,
        ), patch(
            "sys.stdin",
            StringIO(json.dumps(payload)),
        ):
            exit_code = main(["progress-save", "--format", "json"])

        self.assertEqual(exit_code, 0)
        save_chapter_generated_annotations.assert_called_once_with(
            "lunyu",
            "chapter-001",
            payload["generated_annotations"],
            saved_at=1712345678,
        )
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["saved_generated_annotations"], 1)
        self.assertTrue(result["generated_annotation_chapter_path"].endswith("chapter-001.json"))

    def test_flashcard_save_command_writes_bank_entry(self) -> None:
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout), patch(
            "sys.stdin",
            StringIO(json.dumps({"bank_entry": _demo_bank_entry()})),
        ):
            exit_code = main(["flashcard-save", "--format", "json"])

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["bank_entry_id"], "fc-da-xue-001-qin-min")
        self.assertEqual(
            Path(result["bank_entry_path"]),
            Path(tmp) / "flashcards" / "bank" / "fc-da-xue-001-qin-min.json",
        )

    def test_flashcard_review_command_renders_json(self) -> None:
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ), patch("sys.stdout", stdout):
            save_bank_entry(_demo_bank_entry())
            exit_code = main(["flashcard-review", "--format", "json", "--seed", "1"])

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["phase"], "prompt")
        self.assertEqual(result["bank_entry_id"], "fc-da-xue-001-qin-min")


if __name__ == "__main__":
    unittest.main()
