from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from the_big_learn.flashcards import save_bank_entry, save_flashcard_artifacts


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


class FlashcardPersistenceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
