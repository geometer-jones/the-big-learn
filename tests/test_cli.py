from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from the_big_learn.claude_host import install_claude_skills
from the_big_learn.cli import _render_session_markdown, main
from the_big_learn.flashcards import save_bank_entry


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

    def test_progress_command_renders_saved_statuses(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.guided_reading_catalog",
            return_value=[
                {
                    "id": "da-xue",
                    "title": "Da Xue",
                    "chapter_count": 1,
                    "translated_chapter_count": 1,
                    "responded_chapter_count": 0,
                    "chapters": [
                        {
                            "title": "Chapter 1",
                            "status_label": "[translation saved]",
                            "line_count": 3,
                            "character_count": 58,
                        }
                    ],
                }
            ],
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout):
            exit_code = main(["progress"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Reading Progress", stdout.getvalue())
        self.assertIn("Da Xue", stdout.getvalue())
        self.assertIn("Chapter 1: [translation saved]", stdout.getvalue())

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
                "chapter_path": str(Path(tmp) / "source-store" / "lunyu" / "chapters" / "chapter-001.json"),
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

    def test_progress_save_command_can_persist_line_translation_log(self) -> None:
        payload = {
            "work": "da-xue",
            "section": "chapter-001",
            "learner_translation_log": [
                {
                    "line_id": "chapter-001-line-001",
                    "translation_en": "The way of Great Learning lies in making bright virtue shine.",
                }
            ],
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
        self.assertTrue(result["saved_translation"])
        self.assertEqual(
            saved_payload["books"]["da-xue"]["chapters"]["chapter-001"]["learner_translation_log"],
            [
                {
                    "line_id": "chapter-001-line-001",
                    "translation_en": "The way of Great Learning lies in making bright virtue shine.",
                    "saved_at": 1712345678,
                }
            ],
        )
        self.assertNotIn("personal_translation_en", saved_payload["books"]["da-xue"]["chapters"]["chapter-001"])

    def test_progress_save_command_can_persist_line_response_log(self) -> None:
        payload = {
            "work": "da-xue",
            "section": "chapter-001",
            "learner_response_log": [
                {
                    "line_id": "chapter-001-line-001",
                    "response_en": "The claim starts from moral clarity before public order.",
                }
            ],
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
        self.assertTrue(result["saved_response"])
        self.assertEqual(
            saved_payload["books"]["da-xue"]["chapters"]["chapter-001"]["learner_response_log"],
            [
                {
                    "line_id": "chapter-001-line-001",
                    "response_en": "The claim starts from moral clarity before public order.",
                    "saved_at": 1712345678,
                }
            ],
        )

    def test_progress_save_command_can_persist_book_artifacts(self) -> None:
        payload = {
            "work": "da-xue",
            "personal_book_summary_en": "The book starts from self-cultivation and scales outward.",
            "personal_book_response_en": "I find the moral sequencing persuasive but not self-proving.",
            "saved_at": 1712345678,
        }
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout), patch(
            "sys.stdin",
            StringIO(json.dumps(payload)),
        ):
            exit_code = main(["progress-save", "--format", "json"])
            saved_payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertTrue(result["saved_summary"])
        self.assertTrue(result["saved_book_response"])
        self.assertEqual(
            saved_payload["books"]["da-xue"]["personal_summary_en"],
            "The book starts from self-cultivation and scales outward.",
        )
        self.assertEqual(
            saved_payload["books"]["da-xue"]["personal_response_en"],
            "I find the moral sequencing persuasive but not self-proving.",
        )

    def test_progress_save_command_can_persist_global_learner_style_only(self) -> None:
        payload = {
            "learner_style": {
                "global": {
                    "prompt_explicitness": "Explicit",
                }
            },
            "saved_at": 1712345678,
        }
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout), patch(
            "sys.stdin",
            StringIO(json.dumps(payload)),
        ):
            exit_code = main(["progress-save", "--format", "json"])
            saved_payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertTrue(result["saved_learner_style"])
        self.assertEqual(result["learner_style"]["global"]["prompt_explicitness"], "explicit")
        self.assertEqual(saved_payload["learner_style"]["global"]["prompt_explicitness"], "explicit")
        self.assertEqual(saved_payload["learner_style"]["global"]["updated_at"], 1712345678)

    def test_progress_save_command_can_persist_work_scoped_learner_style(self) -> None:
        payload = {
            "work": "da-xue",
            "section": "chapter-001",
            "learner_style": {
                "work": {
                    "discussion_depth": "Brief",
                }
            },
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

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertTrue(result["saved_learner_style"])
        self.assertEqual(result["chapter"]["resolved_learner_style"]["discussion_depth"], "brief")
        self.assertEqual(result["learner_style"]["works"]["da-xue"]["discussion_depth"], "brief")

    def test_progress_save_command_rejects_invalid_learner_style_value(self) -> None:
        payload = {
            "learner_style": {
                "global": {
                    "discussion_depth": "chatty",
                }
            }
        }
        stdout = StringIO()
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), redirect_stderr(stderr), patch("sys.stdout", stdout), patch(
            "sys.stdin",
            StringIO(json.dumps(payload)),
        ):
            exit_code = main(["progress-save", "--format", "json"])

        self.assertEqual(exit_code, 1)
        self.assertIn("learner_style.global.discussion_depth must be one of", stderr.getvalue())
        self.assertEqual("", stdout.getvalue())

    def test_flashcard_save_command_writes_bank_entry_and_variations(self) -> None:
        payload = {
            "bank_entry": {
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
                "status": "draft",
            },
            "variations": [
                {
                    "prompt_layer": "hanzi",
                    "answer_layer": "reading",
                    "prompt_text": "亲民(親民)",
                    "answer_text": "qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)",
                }
            ],
        }
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout), patch(
            "sys.stdin",
            StringIO(json.dumps(payload)),
        ):
            exit_code = main(["flashcard-save", "--format", "json"])
            bank_path = Path(tmp) / "flashcards" / "bank" / "fc-da-xue-001-qin-min.json"
            variations_path = Path(tmp) / "flashcards" / "variations" / "fc-da-xue-001-qin-min.json"
            bank_exists = bank_path.exists()
            variations_exist = variations_path.exists()

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["bank_entry_id"], "fc-da-xue-001-qin-min")
        self.assertEqual(result["variation_count"], 1)
        self.assertTrue(bank_exists)
        self.assertTrue(variations_exist)

    def test_flashcard_save_command_can_increment_significance_flag_count(self) -> None:
        create_payload = {
            "bank_entry": {
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
                "status": "draft",
            }
        }
        increment_payload = {
            "bank_entry_id": "fc-da-xue-001-qin-min",
            "significance_flag_increment": 2,
        }
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            create_stdout = StringIO()
            with redirect_stderr(StringIO()), patch("sys.stdout", create_stdout), patch(
                "sys.stdin",
                StringIO(json.dumps(create_payload)),
            ):
                first_exit_code = main(["flashcard-save", "--format", "json"])

            self.assertEqual(first_exit_code, 0)

            stdout = StringIO()
            with redirect_stderr(StringIO()), patch("sys.stdout", stdout), patch(
                "sys.stdin",
                StringIO(json.dumps(increment_payload)),
            ):
                second_exit_code = main(["flashcard-save", "--format", "json"])
                bank_payload = json.loads(
                    (Path(tmp) / "flashcards" / "bank" / "fc-da-xue-001-qin-min.json").read_text(encoding="utf-8")
                )

            self.assertEqual(second_exit_code, 0)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["bank_entry_id"], "fc-da-xue-001-qin-min")
            self.assertEqual(result["significance_flag_count"], 2)
            self.assertEqual(bank_payload["significance_flag_count"], 2)

    def test_flashcard_review_command_alternates_between_prompt_and_reveal(self) -> None:
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout):
            save_bank_entry(
                {
                    "id": "fc-char-u5b78-u5b66",
                    "source_work": "lunyu",
                    "source_line_ids": ["chapter-001-line-001", "chapter-002-line-003"],
                    "source_segment_ids": [],
                    "origin": {
                        "kind": "line-index",
                        "note": "Auto-indexed from guided-reading line shells.",
                    },
                    "layers": {
                        "traditional": "學",
                        "simplified": "学",
                        "zhuyin": "ㄒㄩㄝˊ",
                        "pinyin": "xué",
                        "gloss_en": "study; learn",
                        "translation_en": "study; learn",
                    },
                    "eligible_prompt_layers": [
                        "simplified",
                        "traditional",
                        "pinyin",
                        "zhuyin",
                        "gloss_en",
                        "translation_en",
                    ],
                    "tags": ["character-index", "lunyu"],
                    "status": "active",
                    "citations": [
                        {
                            "work": "lunyu",
                            "section": "chapter-001",
                            "line_id": "chapter-001-line-001",
                            "char_index": 1,
                        },
                        {
                            "work": "lunyu",
                            "section": "chapter-002",
                            "line_id": "chapter-002-line-003",
                            "char_index": 1,
                        },
                    ],
                    "significance_flag_count": 2,
                }
            )

            first_exit_code = main(["flashcard-review", "--format", "json", "--seed", "1"])
            first = json.loads(stdout.getvalue())

            stdout.seek(0)
            stdout.truncate(0)

            second_exit_code = main(["flashcard-review", "--format", "json"])
            second = json.loads(stdout.getvalue())

        self.assertEqual(first_exit_code, 0)
        self.assertEqual(first["phase"], "prompt")
        self.assertEqual(first["bank_entry_id"], "fc-char-u5b78-u5b66")
        self.assertEqual(first["occurrence_count"], 2)
        self.assertEqual(first["significance_flag_count"], 2)
        self.assertEqual(first["weight"], 22)
        self.assertEqual(len(first["visible_faces"]), 1)

        self.assertEqual(second_exit_code, 0)
        self.assertEqual(second["phase"], "reveal")
        self.assertEqual(second["bank_entry_id"], "fc-char-u5b78-u5b66")
        self.assertEqual(len(second["visible_faces"]), 2)
        self.assertEqual(second["visible_faces"][0]["name"], "hanzi")
        self.assertEqual(second["visible_faces"][1]["name"], "reading")
        self.assertEqual(
            {face["name"] for face in second["visible_faces"]},
            {"hanzi", "reading"},
        )
        self.assertIn("study; learn", second["visible_faces"][1]["text"])

    def test_flashcard_review_command_rejects_empty_or_zero_weight_bank(self) -> None:
        stderr = StringIO()
        stdout = StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ), redirect_stderr(stderr), patch("sys.stdout", stdout):
            save_bank_entry(
                {
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
                    "status": "draft",
                    "significance_flag_count": 0,
                }
            )

            exit_code = main(["flashcard-review", "--format", "json"])

        self.assertEqual(exit_code, 1)
        self.assertIn("No flashcards with positive review weight were found.", stderr.getvalue())
        self.assertEqual("", stdout.getvalue())

    def test_source_catalog_command_renders_detected_chapters(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.build_source_catalog",
            return_value={
                "provider": "wikisource-html",
                "source_url": "https://zh.wikisource.org/wiki/demo",
                "title": "Demo Source",
                "chapter_count": 2,
                "catalog_path": "/tmp/catalog.json",
                "chapters": [
                    {
                        "order": 1,
                        "title": "右第一章",
                        "summary": "天命之謂性",
                        "character_count": 23,
                    },
                    {
                        "order": 2,
                        "title": "右第二章",
                        "summary": "君子中庸",
                        "character_count": 18,
                    },
                ],
            },
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout):
            exit_code = main(["source", "catalog", "--url", "https://zh.wikisource.org/wiki/demo"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Demo Source", stdout.getvalue())
        self.assertIn("Chapters detected: 2", stdout.getvalue())
        self.assertIn("1. 右第一章 - 天命之謂性", stdout.getvalue())

    def test_source_read_command_renders_raw_reading_units(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.build_source_reading_pass",
            return_value={
                "mode": "raw-source",
                "provider": "ctext-html",
                "source_url": "https://ctext.org/demo",
                "source_title": "Demo Source",
                "chapter_path": "/tmp/chapter-001.json",
                "line_count": 2,
                "chapter": {
                    "order": 1,
                    "title": "右第一章",
                    "character_count": 18,
                },
                "lines": [
                    {
                        "id": "chapter-001-line-001",
                        "text": "右第一章。天命之謂性。",
                        "character_count": 8,
                    },
                    {
                        "id": "chapter-001-line-002",
                        "text": "天命之謂性；率性之謂道；修道之謂教。",
                        "character_count": 17,
                    },
                ],
            },
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout):
            exit_code = main(["source", "read", "--url", "https://ctext.org/demo", "--chapter", "1"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Reading mode: raw-source", stdout.getvalue())
        self.assertIn("Reading units: 2", stdout.getvalue())
        self.assertIn("chapter-001-line-001", stdout.getvalue())
        self.assertIn("Line 1/2", stdout.getvalue())
        self.assertIn("天命之謂性；率性之謂道；修道之謂教。", stdout.getvalue())

    def test_source_read_command_surfaces_saved_generated_annotations(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.build_source_reading_pass",
            return_value={
                "mode": "raw-source",
                "provider": "ctext-html",
                "source_url": "https://ctext.org/demo",
                "source_title": "Demo Source",
                "chapter_path": "/tmp/chapter-001.json",
                "line_count": 1,
                "saved_annotation_count": 1,
                "chapter": {
                    "order": 1,
                    "title": "右第一章",
                    "character_count": 18,
                },
                "lines": [
                    {
                        "id": "chapter-001-line-001",
                        "text": "右第一章。天命之謂性。",
                        "character_count": 8,
                        "has_saved_generated_annotation": True,
                        "annotation_source": "saved-generated",
                    }
                ],
            },
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout):
            exit_code = main(["source", "read", "--url", "https://ctext.org/demo", "--chapter", "1"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Reading units with saved generated annotations: 1", stdout.getvalue())
        self.assertIn("Saved generated annotation: yes", stdout.getvalue())

    def test_source_read_command_surfaces_character_index_reconstruction(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.build_source_reading_pass",
            return_value={
                "mode": "raw-source",
                "provider": "ctext-html",
                "source_url": "https://ctext.org/demo-memory",
                "source_title": "Demo Source",
                "chapter_path": "/tmp/chapter-001.json",
                "line_count": 1,
                "saved_annotation_count": 0,
                "saved_character_index_count": 1,
                "chapter": {
                    "order": 1,
                    "title": "學而第一",
                    "character_count": 6,
                },
                "lines": [
                    {
                        "id": "chapter-001-line-001",
                        "text": "學而時習之。",
                        "character_count": 6,
                        "has_saved_character_index_annotation": True,
                        "annotation_source": "saved-character-index",
                    }
                ],
            },
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout):
            exit_code = main(["source", "read", "--url", "https://ctext.org/demo-memory", "--chapter", "1"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Reading units reconstructed from character index: 1", stdout.getvalue())
        self.assertIn("Reconstructed from character index: yes", stdout.getvalue())

    def test_render_command_can_use_stacked_character_layout(self) -> None:
        stdout = StringIO()
        with patch(
            "the_big_learn.cli.render_reading_pass",
            return_value={
                "work": "da-xue",
                "lines": [
                    {
                        "id": "demo-line-stacked",
                        "character_glosses_en": ["great", "learning"],
                        "layers": {
                            "traditional": "大學",
                            "simplified": "大学",
                            "zhuyin": "ㄉㄚˋ ㄒㄩㄝˊ",
                            "pinyin": "dà xué",
                            "gloss_en": "great learning",
                            "translation_en": "Great learning.",
                        },
                        "segments": [
                            {
                                "id": "demo-line-stacked-a",
                                "traditional": "大學",
                                "simplified": "大学",
                                "zhuyin": "ㄉㄚˋ ㄒㄩㄝˊ",
                                "pinyin": "dà xué",
                                "gloss_en": "great learning",
                            }
                        ],
                    }
                ],
            },
        ), redirect_stderr(StringIO()), patch("sys.stdout", stdout):
            exit_code = main(["render", "--character-layout", "stacked"])

        self.assertEqual(exit_code, 0)
        self.assertNotIn("<table>", stdout.getvalue())
        self.assertIn("Chinese: 大", stdout.getvalue())
        self.assertIn("Chinese: 学(學)", stdout.getvalue())
        self.assertIn("Reading: dà(ㄉㄚˋ)", stdout.getvalue())
        self.assertIn("Chinese Phrase: 大学(大學)", stdout.getvalue())

    def test_render_session_markdown_uses_combined_hanzi_display(self) -> None:
        output = _render_session_markdown(
            {
                "session_id": "demo-session",
                "lines": [],
                "learner_translations": [],
                "answers": [
                    {
                        "question_id": "q-001",
                        "question": "Why is 親民 read this way?",
                        "phrase": "亲民(親民)",
                        "direct_answer": "demo",
                        "explanation": "demo explanation",
                        "variant_note": None,
                    }
                ],
                "flashcard_entries": [
                    {
                        "id": "fc-demo",
                        "layers": {
                            "traditional": "親民",
                            "simplified": "亲民",
                            "zhuyin": "ㄑㄧㄣ ㄇㄧㄣˊ",
                            "pinyin": "qīn mín",
                            "gloss_en": "renew the people",
                        },
                    }
                ],
                "flashcard_variations": [
                    {
                        "prompt_layer": "hanzi",
                        "answer_layer": "reading",
                        "prompt_text": "亲民(親民)",
                        "answer_text": "qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)",
                    }
                ],
            }
        )

        self.assertIn("- Hanzi: 亲民(親民)", output)
        self.assertIn("- Reading: qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)", output)
        self.assertIn("- hanzi -> reading: 亲民(親民) => qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)", output)
        self.assertIn("## Immediate Answers", output)
        self.assertIn("- Question: Why is 親民 read this way?", output)
        self.assertNotIn("## Learner Questions", output)
        self.assertNotIn("- Traditional:", output)


if __name__ == "__main__":
    unittest.main()
