from __future__ import annotations

import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from the_big_learn.flashcards import (
    character_index_entry_id,
    choose_weighted_bank_entry,
    flashcard_occurrence_count,
    flashcard_review_state_path,
    flashcard_weight,
    increment_significance_flag_count,
    run_flashcard_review_step,
    save_bank_entry,
    save_character_index_entries,
    save_flashcard_artifacts,
)


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
    }


def _demo_character_line(
    *,
    line_id: str,
    line_index_in_container: int,
    gloss_en: str,
) -> dict:
    return {
        "id": line_id,
        "line_index_in_container": line_index_in_container,
        "layers": {
            "traditional": "學",
            "simplified": "学",
            "zhuyin": "ㄒㄩㄝˊ",
            "pinyin": "xué",
            "gloss_en": gloss_en,
            "translation_en": gloss_en,
        },
        "character_glosses_en": [gloss_en],
    }


class FlashcardPersistenceTests(unittest.TestCase):
    def test_flashcard_weight_uses_ten_times_significance_flags_plus_citations(self) -> None:
        entry = _demo_bank_entry()
        entry["significance_flag_count"] = 2
        entry["citations"] = [{}, {}, {}]

        self.assertEqual(flashcard_occurrence_count(entry), 3)
        self.assertEqual(flashcard_weight(entry), 23)

    def test_choose_weighted_bank_entry_skips_zero_weight_entries(self) -> None:
        zero_weight_entry = _demo_bank_entry()
        weighted_entry = _demo_bank_entry()
        weighted_entry["id"] = "fc-char-u5b78-u5b66"
        weighted_entry["origin"] = {
            "kind": "line-index",
            "note": "Auto-indexed from guided-reading line shells.",
        }
        weighted_entry["status"] = "active"
        weighted_entry["significance_flag_count"] = 1
        weighted_entry["citations"] = [{}, {}]

        class FixedRandom:
            def random(self) -> float:
                return 0.0

        selected = choose_weighted_bank_entry(
            [zero_weight_entry, weighted_entry],
            rng=FixedRandom(),  # type: ignore[arg-type]
        )

        self.assertEqual(selected["bank_entry"]["id"], "fc-char-u5b78-u5b66")
        self.assertEqual(selected["occurrence_count"], 2)
        self.assertEqual(selected["significance_flag_count"], 1)
        self.assertEqual(selected["weight"], 12)

    def test_run_flashcard_review_step_alternates_between_prompt_and_reveal(self) -> None:
        entry = _demo_bank_entry()
        entry["citations"] = [
            {
                "work": "da-xue",
                "section": "chapter-001",
                "line_id": "da-xue-zhangju-001",
                "char_index": 1,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            save_bank_entry(entry)

            first = run_flashcard_review_step(rng=random.Random(1))
            self.assertEqual(first["phase"], "prompt")
            self.assertEqual(first["bank_entry_id"], "fc-da-xue-001-qin-min")
            self.assertEqual(len(first["visible_faces"]), 1)
            self.assertTrue(flashcard_review_state_path().exists())

            second = run_flashcard_review_step()
            self.assertEqual(second["phase"], "reveal")
            self.assertEqual(second["bank_entry_id"], "fc-da-xue-001-qin-min")
            self.assertEqual(len(second["visible_faces"]), 2)
            self.assertFalse(flashcard_review_state_path().exists())

    def test_save_bank_entry_writes_json_to_state_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            result = save_bank_entry(_demo_bank_entry())
            saved_path = Path(result["bank_entry_path"])
            payload = json.loads(saved_path.read_text(encoding="utf-8"))

        self.assertTrue(saved_path.name.endswith(".json"))
        self.assertEqual(saved_path.parent.name, "bank")
        self.assertEqual(payload["id"], "fc-da-xue-001-qin-min")
        self.assertEqual(payload["origin"]["question_id"], "q-001")
        self.assertEqual(
            payload["eligible_prompt_layers"],
            ["simplified", "traditional", "pinyin", "zhuyin", "gloss_en", "translation_en"],
        )

    def test_save_flashcard_artifacts_writes_variations_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            result = save_flashcard_artifacts(
                bank_entry=_demo_bank_entry(),
                variations=[
                    {
                        "prompt_layer": "hanzi",
                        "answer_layer": "reading",
                        "prompt_text": "亲民(親民)",
                        "answer_text": "qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)",
                    }
                ],
            )
            variations_path = Path(result["variations_path"])
            payload = json.loads(variations_path.read_text(encoding="utf-8"))

        self.assertEqual(result["variation_count"], 1)
        self.assertEqual(payload["bank_entry_id"], "fc-da-xue-001-qin-min")
        self.assertEqual(payload["variations"][0]["bank_entry_id"], "fc-da-xue-001-qin-min")
        self.assertEqual(payload["variations"][0]["prompt_layer"], "hanzi")

    def test_increment_significance_flag_count_updates_saved_bank_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            save_bank_entry(_demo_bank_entry())
            result = increment_significance_flag_count("fc-da-xue-001-qin-min", increment=2)
            payload = json.loads(
                (Path(tmp) / "flashcards" / "bank" / "fc-da-xue-001-qin-min.json").read_text(encoding="utf-8")
            )

        self.assertEqual(result["significance_flag_increment"], 2)
        self.assertEqual(result["significance_flag_count"], 2)
        self.assertEqual(payload["significance_flag_count"], 2)

    def test_save_bank_entry_preserves_existing_significance_flag_count_when_omitted(self) -> None:
        flagged_entry = _demo_bank_entry()
        flagged_entry["significance_flag_count"] = 3
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            save_bank_entry(flagged_entry)
            save_bank_entry(_demo_bank_entry())
            payload = json.loads(
                (Path(tmp) / "flashcards" / "bank" / "fc-da-xue-001-qin-min.json").read_text(encoding="utf-8")
            )

        self.assertEqual(payload["significance_flag_count"], 3)

    def test_save_character_index_entries_merges_citations_without_duplicates(self) -> None:
        entry_id = character_index_entry_id("學", "学")
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            first = save_character_index_entries(
                "lunyu",
                "chapter-001",
                [
                    _demo_character_line(
                        line_id="chapter-001-line-001",
                        line_index_in_container=1,
                        gloss_en="study",
                    )
                ],
            )
            duplicate = save_character_index_entries(
                "lunyu",
                "chapter-001",
                [
                    _demo_character_line(
                        line_id="chapter-001-line-001",
                        line_index_in_container=1,
                        gloss_en="study",
                    )
                ],
            )
            second = save_character_index_entries(
                "mengzi",
                "chapter-002",
                [
                    _demo_character_line(
                        line_id="chapter-002-line-001",
                        line_index_in_container=1,
                        gloss_en="learn",
                    )
                ],
            )
            payload = json.loads(
                (Path(tmp) / "flashcards" / "bank" / f"{entry_id}.json").read_text(encoding="utf-8")
            )

        self.assertEqual(first["entry_count"], 1)
        self.assertEqual(first["citation_count"], 1)
        self.assertEqual(duplicate["entry_count"], 1)
        self.assertEqual(duplicate["citation_count"], 0)
        self.assertEqual(second["entry_count"], 1)
        self.assertEqual(second["citation_count"], 1)
        self.assertEqual(payload["layers"]["simplified"], "学")
        self.assertEqual(payload["layers"]["traditional"], "學")
        self.assertEqual(payload["layers"]["pinyin"], "xué")
        self.assertEqual(payload["layers"]["gloss_en"], "study; learn")
        self.assertEqual(payload["layers"]["translation_en"], "study; learn")
        self.assertEqual(payload["source_work"], "lunyu")
        self.assertEqual(payload["source_works"], ["lunyu", "mengzi"])
        self.assertEqual(payload["source_line_ids"], ["chapter-001-line-001", "chapter-002-line-001"])
        self.assertEqual(len(payload["citations"]), 2)
        self.assertEqual(payload["citations"][0]["line_id"], "chapter-001-line-001")
        self.assertEqual(payload["citations"][0]["char_index"], 1)
        self.assertEqual(payload["citations"][1]["work"], "mengzi")

    def test_character_index_merges_preserve_significance_flag_count(self) -> None:
        entry_id = character_index_entry_id("學", "学")
        with tempfile.TemporaryDirectory() as tmp, patch(
            "the_big_learn.flashcards.state_dir",
            return_value=Path(tmp),
        ):
            save_character_index_entries(
                "lunyu",
                "chapter-001",
                [
                    _demo_character_line(
                        line_id="chapter-001-line-001",
                        line_index_in_container=1,
                        gloss_en="study",
                    )
                ],
            )
            save_flashcard_artifacts(bank_entry_id=entry_id, significance_flag_increment=1)
            save_character_index_entries(
                "mengzi",
                "chapter-002",
                [
                    _demo_character_line(
                        line_id="chapter-002-line-001",
                        line_index_in_container=1,
                        gloss_en="learn",
                    )
                ],
            )
            payload = json.loads(
                (Path(tmp) / "flashcards" / "bank" / f"{entry_id}.json").read_text(encoding="utf-8")
            )

        self.assertEqual(payload["significance_flag_count"], 1)


if __name__ == "__main__":
    unittest.main()
