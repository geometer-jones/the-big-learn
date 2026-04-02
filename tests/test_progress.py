from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from the_big_learn import progress


def _demo_catalog() -> dict:
    return {
        "chapters": [
            {
                "id": "chapter-001",
                "order": 1,
                "title": "Chapter 1",
                "character_count": 58,
                "reading_unit_count": 3,
            }
        ]
    }


def _demo_chapter() -> dict:
    return {
        "chapter": {
            "reading_units": [
                {"id": "chapter-001-line-001", "text": "大学之道，在明明德，在亲民，在止于至善。"},
                {"id": "chapter-001-line-002", "text": "知止而后有定；定而后能静；静而后能安；安而后能虑；虑而后能得。"},
                {"id": "chapter-001-line-003", "text": "物有本末；事有终始。知所先后，则近道矣。"},
            ]
        }
    }


class ProgressTests(unittest.TestCase):
    def test_guided_reading_catalog_defaults_to_no_saved_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.SUPPORTED_WORKS",
            ["da-xue"],
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=_demo_catalog(),
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=_demo_chapter(),
        ):
            books = progress.guided_reading_catalog()

        self.assertEqual(books[0]["id"], "da-xue")
        self.assertEqual(books[0]["translated_chapter_count"], 0)
        self.assertEqual(books[0]["responded_chapter_count"], 0)
        self.assertEqual(books[0]["chapters"][0]["id"], "chapter-001")
        self.assertEqual(books[0]["chapters"][0]["line_count"], 3)
        self.assertEqual(books[0]["chapters"][0]["character_count"], 58)
        self.assertEqual(books[0]["chapters"][0]["status_tags"], ["[unsaved]"])
        self.assertEqual(books[0]["chapters"][0]["status_label"], "[unsaved]")

    def test_save_chapter_progress_records_translation_and_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=_demo_catalog(),
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=_demo_chapter(),
        ):
            saved = progress.save_chapter_progress(
                "da-xue",
                "chapter-001",
                personal_translation_en="My chapter translation.",
                personal_response_en="My chapter response.",
                saved_at=1712345678,
            )
            books = progress.guided_reading_catalog()
            payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        self.assertEqual(saved["personal_translation_en"], "My chapter translation.")
        self.assertEqual(saved["personal_response_en"], "My chapter response.")
        self.assertEqual(saved["personal_translation_saved_at"], 1712345678)
        self.assertEqual(saved["personal_response_saved_at"], 1712345678)
        self.assertEqual(
            payload["books"]["da-xue"]["chapters"]["chapter-001"]["personal_translation_en"],
            "My chapter translation.",
        )
        self.assertEqual(books[0]["translated_chapter_count"], 1)
        self.assertEqual(books[0]["responded_chapter_count"], 1)
        self.assertEqual(
            books[0]["chapters"][0]["status_tags"],
            ["[translation saved]", "[response saved]"],
        )
        self.assertEqual(books[0]["chapters"][0]["status_label"], "[translation saved] [response saved]")

    def test_save_chapter_progress_can_record_partial_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=_demo_catalog(),
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=_demo_chapter(),
        ):
            progress.save_chapter_progress(
                "da-xue",
                "chapter-001",
                personal_translation_en="Only translation so far.",
                saved_at=1712345678,
            )
            books = progress.guided_reading_catalog()

        self.assertTrue(books[0]["chapters"][0]["has_personal_translation"])
        self.assertFalse(books[0]["chapters"][0]["has_personal_response"])
        self.assertEqual(books[0]["chapters"][0]["status_tags"], ["[translation saved]"])
        self.assertEqual(books[0]["chapters"][0]["status_label"], "[translation saved]")

    def test_save_chapter_progress_can_persist_line_by_line_translation_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=_demo_catalog(),
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=_demo_chapter(),
        ):
            progress.save_chapter_progress(
                "da-xue",
                "chapter-001",
                learner_translation_log=[
                    {
                        "line_id": "chapter-001-line-001",
                        "translation_en": "The way of Great Learning lies in making bright virtue shine.",
                    }
                ],
                saved_at=1712345678,
            )
            saved = progress.save_chapter_progress(
                "da-xue",
                "chapter-001",
                learner_translation_log=[
                    {
                        "line_id": "chapter-001-line-002",
                        "translation_en": "Once you know where to stop, you can settle.",
                    }
                ],
                saved_at=1712345680,
            )
            books = progress.guided_reading_catalog()
            payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        log = payload["books"]["da-xue"]["chapters"]["chapter-001"]["learner_translation_log"]
        self.assertEqual(
            log,
            [
                {
                    "line_id": "chapter-001-line-001",
                    "translation_en": "The way of Great Learning lies in making bright virtue shine.",
                    "saved_at": 1712345678,
                },
                {
                    "line_id": "chapter-001-line-002",
                    "translation_en": "Once you know where to stop, you can settle.",
                    "saved_at": 1712345680,
                },
            ],
        )
        self.assertNotIn("personal_translation_en", saved)
        self.assertNotIn("personal_translation_saved_at", saved)
        self.assertNotIn("personal_translation_en", payload["books"]["da-xue"]["chapters"]["chapter-001"])
        self.assertEqual(books[0]["chapters"][0]["status_label"], "[translation saved]")

    def test_save_chapter_progress_can_persist_line_by_line_response_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=_demo_catalog(),
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=_demo_chapter(),
        ):
            saved = progress.save_chapter_progress(
                "da-xue",
                "chapter-001",
                learner_response_log=[
                    {
                        "line_id": "chapter-001-line-001",
                        "response_en": "This feels like a program for self-cultivation before governance.",
                    }
                ],
                saved_at=1712345678,
            )
            books = progress.guided_reading_catalog()
            payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        self.assertEqual(
            payload["books"]["da-xue"]["chapters"]["chapter-001"]["learner_response_log"],
            [
                {
                    "line_id": "chapter-001-line-001",
                    "response_en": "This feels like a program for self-cultivation before governance.",
                    "saved_at": 1712345678,
                }
            ],
        )
        self.assertNotIn("personal_response_en", saved)
        self.assertEqual(books[0]["chapters"][0]["status_label"], "[response saved]")

    def test_save_book_progress_records_summary_and_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.SUPPORTED_WORKS",
            ["da-xue"],
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=_demo_catalog(),
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=_demo_chapter(),
        ):
            saved = progress.save_book_progress(
                "da-xue",
                personal_summary_en="The book argues that order radiates outward from cultivated clarity.",
                personal_response_en="I buy the sequence, but I still want to test its political assumptions.",
                saved_at=1712345678,
            )
            books = progress.guided_reading_catalog()
            payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        self.assertEqual(
            saved["personal_summary_en"],
            "The book argues that order radiates outward from cultivated clarity.",
        )
        self.assertEqual(
            saved["personal_response_en"],
            "I buy the sequence, but I still want to test its political assumptions.",
        )
        self.assertEqual(payload["books"]["da-xue"]["personal_summary_saved_at"], 1712345678)
        self.assertTrue(books[0]["has_personal_summary"])
        self.assertTrue(books[0]["has_book_personal_response"])

    def test_save_learner_style_merges_global_and_work_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ):
            progress.save_learner_style(
                {
                    "global": {
                        "prompt_explicitness": "Explicit",
                    }
                },
                saved_at=1712345678,
            )
            saved = progress.save_learner_style(
                {
                    "work": {
                        "discussion_depth": "Brief",
                    }
                },
                work="da-xue",
                saved_at=1712345680,
            )
            loaded = progress.load_progress()
            resolved_default = progress.resolved_learner_style()
            resolved_work = progress.resolved_learner_style("da-xue")

        self.assertEqual(saved["global"]["prompt_explicitness"], "explicit")
        self.assertEqual(saved["works"]["da-xue"]["discussion_depth"], "brief")
        self.assertEqual(saved["works"]["da-xue"]["updated_at"], 1712345680)
        self.assertEqual(loaded["learner_style"]["global"]["prompt_explicitness"], "explicit")
        self.assertEqual(resolved_default["prompt_explicitness"], "explicit")
        self.assertEqual(resolved_work["discussion_depth"], "brief")
        self.assertEqual(resolved_work["prompt_explicitness"], "explicit")

    def test_save_chapter_progress_returns_resolved_learner_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=_demo_catalog(),
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=_demo_chapter(),
        ):
            saved = progress.save_chapter_progress(
                "da-xue",
                "chapter-001",
                learner_style={
                    "global": {
                        "prompt_explicitness": "Explicit",
                    },
                    "work": {
                        "discussion_depth": "Brief",
                    },
                },
                saved_at=1712345678,
            )

        self.assertEqual(saved["resolved_learner_style"]["prompt_explicitness"], "explicit")
        self.assertEqual(saved["resolved_learner_style"]["discussion_depth"], "brief")

    def test_save_chapter_progress_supports_bundled_source_books(self) -> None:
        bundled_catalog = {
            "chapters": [
                {
                    "id": "chapter-001",
                    "order": 1,
                    "title": "學而第一",
                    "character_count": 493,
                    "reading_unit_count": 26,
                }
            ]
        }
        bundled_chapter = {
            "chapter": {
                "reading_units": [
                    {"id": "chapter-001-line-001", "text": "子曰：「學而時習之，不亦說乎？"},
                    {"id": "chapter-001-line-002", "text": "有朋自遠方來，不亦樂乎？"},
                ]
            }
        }

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.SUPPORTED_WORKS",
            ["lunyu"],
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=bundled_catalog,
        ), patch(
            "the_big_learn.progress.load_saved_source_chapter",
            return_value=bundled_chapter,
        ):
            saved = progress.save_chapter_progress(
                "lunyu",
                "chapter-001",
                personal_translation_en="My Lunyu chapter translation.",
                personal_response_en="My Lunyu chapter response.",
                saved_at=1712345678,
            )
            books = progress.guided_reading_catalog()
            payload = json.loads((Path(tmp) / "reading-progress.json").read_text(encoding="utf-8"))

        self.assertEqual(saved["personal_translation_en"], "My Lunyu chapter translation.")
        self.assertEqual(saved["personal_response_en"], "My Lunyu chapter response.")
        self.assertEqual(saved["line_ids"], ["chapter-001-line-001", "chapter-001-line-002"])
        self.assertEqual(payload["books"]["lunyu"]["chapters"]["chapter-001"]["chapter_title"], "學而第一")
        self.assertEqual(books[0]["id"], "lunyu")
        self.assertEqual(books[0]["translated_chapter_count"], 1)
        self.assertEqual(books[0]["responded_chapter_count"], 1)
        self.assertEqual(books[0]["chapters"][0]["status_label"], "[translation saved] [response saved]")

    def test_save_chapter_generated_annotations_resolves_source_backed_chapter(self) -> None:
        bundled_catalog = {
            "chapters": [
                {
                    "id": "chapter-001",
                    "order": 1,
                    "title": "學而第一",
                    "character_count": 493,
                    "reading_unit_count": 26,
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.progress.state_dir",
            return_value=Path(tmp),
        ), patch(
            "the_big_learn.progress.SUPPORTED_WORKS",
            ["lunyu"],
        ), patch(
            "the_big_learn.progress.load_saved_source_catalog",
            return_value=bundled_catalog,
        ), patch(
            "the_big_learn.progress.save_source_chapter_generated_annotations",
            return_value={
                "chapter_id": "chapter-001",
                "chapter_path": str(Path(tmp) / "source-store" / "lunyu" / "chapters" / "chapter-001.json"),
                "saved_annotation_count": 1,
                "line_ids": ["chapter-001-line-001"],
            },
        ) as save_source_chapter_generated_annotations:
            saved = progress.save_chapter_generated_annotations(
                "lunyu",
                "chapter-001",
                [
                    {
                        "line_id": "chapter-001-line-001",
                        "layers": {"pinyin": "zǐ yuē"},
                    }
                ],
                saved_at=1712345678,
            )

        save_source_chapter_generated_annotations.assert_called_once_with(
            "https://ctext.org/si-shu-zhang-ju-ji-zhu/lun-yu-ji-zhu?if=en",
            "chapter-001",
            [
                {
                    "line_id": "chapter-001-line-001",
                    "layers": {"pinyin": "zǐ yuē"},
                }
            ],
            saved_at=1712345678,
        )
        self.assertEqual(saved["saved_annotation_count"], 1)
        self.assertEqual(saved["line_ids"], ["chapter-001-line-001"])


if __name__ == "__main__":
    unittest.main()
