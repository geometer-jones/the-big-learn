from __future__ import annotations

import unittest
from unittest.mock import patch

from the_big_learn.flashcards import build_bank_entry, build_variations
from the_big_learn.runtime import render_reading_pass, run_guided_reading_session


def _demo_line() -> dict:
    return {
        "id": "da-xue-zhangju-001",
        "work": "da-xue",
        "section": "opening-outline",
        "order": 1,
        "layers": {
            "traditional": "學問之道，在親民。",
            "simplified": "学问之道，在亲民。",
            "zhuyin": "ㄒㄩㄝˊ ㄨㄣˋ ㄓ ㄉㄠˋ，ㄗㄞˋ ㄑㄧㄣ ㄇㄧㄣˊ。",
            "pinyin": "xué wèn zhī dào, zài qīn mín.",
            "gloss_en": "the way of learning, in renewing the people",
            "translation_en": "The way of learning lies in renewing the people.",
        },
        "segments": [
            {
                "id": "da-xue-zhangju-001-d",
                "traditional": "親民",
                "simplified": "亲民",
                "zhuyin": "ㄑㄧㄣ ㄇㄧㄣˊ",
                "pinyin": "qīn mín",
                "gloss_en": "renew the people",
                "notes": [
                    "親 is often taken as 新 in this line."
                ],
            }
        ],
    }


def _demo_question() -> dict:
    return {
        "id": "q-001",
        "line_id": "da-xue-zhangju-001",
        "segment_id": "da-xue-zhangju-001-d",
        "question": "Why is 親民 read as renewing the people here?",
        "status": "queued",
    }


def _demo_fixture() -> dict:
    return {
        "session_id": "da-xue-demo-001",
        "workflow": "four-books-guided-reading",
        "source": {
            "work": "da-xue",
            "line_ids": [
                "da-xue-zhangju-001",
            ],
        },
        "learner_translations": [
            {
                "id": "lt-001",
                "line_id": "da-xue-zhangju-001",
                "prompt": "Translate the line into English in your own voice.",
                "learner_translation_en": "Learning is about renewing the people.",
                "status": "recorded",
            }
        ],
        "learner_questions": [
            _demo_question(),
        ],
    }


def _demo_policy() -> dict:
    return {
        "supported_layers": {
            "hanzi",
            "reading",
            "gloss_en",
            "translation_en",
        },
        "default_priority_pairs": [
            {
                "prompt_layer": "hanzi",
                "answer_layer": "reading",
            },
            {
                "prompt_layer": "gloss_en",
                "answer_layer": "hanzi",
            },
        ],
    }


class RuntimeTests(unittest.TestCase):
    def test_render_reading_pass_returns_repository_lines(self) -> None:
        line = _demo_line()

        with patch("the_big_learn.runtime.select_lines_by_range", return_value=[line]) as select_lines_by_range, patch(
            "the_big_learn.runtime.load_lines",
            return_value=[line],
        ):
            result = render_reading_pass("da-xue", start=1, end=1)

        select_lines_by_range.assert_called_once_with("da-xue", start=1, end=1)
        self.assertEqual(result["lines"][0]["id"], "da-xue-zhangju-001")
        self.assertEqual(result["lines"][0]["line_index_in_container"], 1)
        self.assertEqual(result["lines"][0]["container_line_count"], 1)

    def test_run_guided_reading_session_emits_variant_note(self) -> None:
        line = _demo_line()
        fixture = _demo_fixture()

        with patch("the_big_learn.runtime.load_fixture", return_value=fixture), patch(
            "the_big_learn.runtime.select_lines_by_ids",
            return_value=[line],
        ), patch("the_big_learn.runtime.load_lines", return_value=[line]), patch(
            "the_big_learn.runtime.load_flashcard_policy",
            return_value=_demo_policy(),
        ):
            result = run_guided_reading_session()

        self.assertEqual(result["answers"][0]["question_id"], "q-001")
        self.assertEqual(result["answers"][0]["question"], "Why is 親民 read as renewing the people here?")
        self.assertEqual(result["learner_translations"][0]["line_id"], "da-xue-zhangju-001")
        self.assertEqual(result["learner_translations"][0]["status"], "recorded")
        self.assertEqual(result["answers"][0]["phrase"], "亲民(親民)")
        self.assertIn("親 is often taken as 新", result["answers"][0]["variant_note"])
        self.assertIn("Line da-xue-zhangju-001 reads: 学问之道，在亲民。(學問之道，在親民。)", result["answers"][0]["explanation"])
        self.assertEqual(result["lines"][0]["line_index_in_container"], 1)

    def test_flashcard_entry_matches_expected_source_fields(self) -> None:
        line = _demo_line()
        question = _demo_question()
        segment = line["segments"][0]
        entry = build_bank_entry(question, line, segment)

        self.assertEqual(entry["id"], "fc-da-xue-001-qin-min")
        self.assertEqual(entry["source_line_ids"], ["da-xue-zhangju-001"])
        self.assertEqual(entry["source_segment_ids"], ["da-xue-zhangju-001-d"])
        self.assertEqual(entry["layers"]["traditional"], "親民")
        self.assertEqual(entry["origin"]["note"], "Learner asked about 亲民(親民).")
        self.assertEqual(
            entry["eligible_prompt_layers"],
            ["simplified", "traditional", "pinyin", "zhuyin", "gloss_en", "translation_en"],
        )

    def test_default_variations_follow_policy(self) -> None:
        line = _demo_line()
        question = _demo_question()
        segment = line["segments"][0]
        entry = build_bank_entry(question, line, segment)
        policy = _demo_policy()
        variations = build_variations(entry, policy)

        self.assertEqual(len(variations), len(policy["default_priority_pairs"]))
        self.assertEqual(variations[0]["prompt_layer"], "hanzi")
        self.assertEqual(variations[0]["prompt_text"], "亲民(親民)")
        self.assertEqual(variations[0]["answer_layer"], "reading")
        self.assertEqual(variations[0]["answer_text"], "qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)")
        self.assertEqual(variations[1]["answer_layer"], "hanzi")
        self.assertEqual(variations[1]["answer_text"], "亲民(親民)")
        for variation in variations:
            self.assertNotEqual(variation["prompt_layer"], variation["answer_layer"])

    def test_variations_skip_redundant_traditional_vs_simplified_cards(self) -> None:
        line = _demo_line()
        question = _demo_question()
        segment = line["segments"][0]
        entry = build_bank_entry(question, line, segment)
        policy = {
            "supported_layers": {"traditional", "simplified", "pinyin"},
            "default_priority_pairs": [
                {
                    "prompt_layer": "traditional",
                    "answer_layer": "simplified",
                },
                {
                    "prompt_layer": "traditional",
                    "answer_layer": "pinyin",
                },
            ],
        }

        variations = build_variations(entry, policy)

        self.assertEqual(len(variations), 1)
        self.assertEqual(variations[0]["prompt_text"], "亲民(親民)")
        self.assertEqual(variations[0]["answer_text"], "qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)")

    def test_variations_skip_redundant_pinyin_vs_zhuyin_cards(self) -> None:
        line = _demo_line()
        question = _demo_question()
        segment = line["segments"][0]
        entry = build_bank_entry(question, line, segment)
        policy = {
            "supported_layers": {"zhuyin", "pinyin", "hanzi"},
            "default_priority_pairs": [
                {
                    "prompt_layer": "zhuyin",
                    "answer_layer": "pinyin",
                },
                {
                    "prompt_layer": "hanzi",
                    "answer_layer": "pinyin",
                },
            ],
        }

        variations = build_variations(entry, policy)

        self.assertEqual(len(variations), 1)
        self.assertEqual(variations[0]["answer_text"], "qīn mín(ㄑㄧㄣ ㄇㄧㄣˊ)")

    def test_variations_skip_redundant_gloss_vs_translation_cards_for_single_entry(self) -> None:
        line = _demo_line()
        question = _demo_question()
        segment = line["segments"][0]
        entry = build_bank_entry(question, line, segment)
        policy = {
            "supported_layers": {"hanzi", "gloss_en", "translation_en"},
            "default_priority_pairs": [
                {
                    "prompt_layer": "hanzi",
                    "answer_layer": "gloss_en",
                },
                {
                    "prompt_layer": "hanzi",
                    "answer_layer": "translation_en",
                },
                {
                    "prompt_layer": "gloss_en",
                    "answer_layer": "hanzi",
                },
                {
                    "prompt_layer": "translation_en",
                    "answer_layer": "hanzi",
                },
            ],
        }

        variations = build_variations(entry, policy)

        self.assertEqual(len(variations), 2)
        self.assertEqual(
            {(variation["prompt_layer"], variation["answer_layer"]) for variation in variations},
            {("hanzi", "gloss_en"), ("gloss_en", "hanzi")},
        )

    def test_variations_keep_distinct_gloss_and_translation_cards_when_text_differs(self) -> None:
        line = _demo_line()
        question = _demo_question()
        entry = build_bank_entry(question, line, segment=None)
        policy = {
            "supported_layers": {"hanzi", "gloss_en", "translation_en"},
            "default_priority_pairs": [
                {
                    "prompt_layer": "hanzi",
                    "answer_layer": "gloss_en",
                },
                {
                    "prompt_layer": "hanzi",
                    "answer_layer": "translation_en",
                },
            ],
        }

        variations = build_variations(entry, policy)

        self.assertEqual(len(variations), 2)
        self.assertEqual(
            [(variation["prompt_layer"], variation["answer_layer"]) for variation in variations],
            [("hanzi", "gloss_en"), ("hanzi", "translation_en")],
        )


if __name__ == "__main__":
    unittest.main()
