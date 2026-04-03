from __future__ import annotations

import unittest

from the_big_learn.rendering import build_character_rows


class CharacterRowTests(unittest.TestCase):
    def test_build_character_rows_leaves_spanned_phrase_cells_absent_until_next_segment(self) -> None:
        rows = build_character_rows(
            {
                "id": "demo-line-phrase-cells",
                "layers": {
                    "traditional": "大學之道",
                    "simplified": "大学之道",
                    "zhuyin": "ㄉㄚˋ ㄒㄩㄝˊ ㄓ ㄉㄠˋ",
                    "pinyin": "dà xué zhī dào",
                    "gloss_en": "great learning; the way of",
                    "translation_en": "The way of great learning.",
                },
                "segments": [
                    {
                        "id": "demo-line-phrase-cells-a",
                        "traditional": "大學",
                        "simplified": "大学",
                        "zhuyin": "ㄉㄚˋ ㄒㄩㄝˊ",
                        "pinyin": "dà xué",
                        "gloss_en": "great learning",
                    },
                    {
                        "id": "demo-line-phrase-cells-b",
                        "traditional": "之道",
                        "simplified": "之道",
                        "zhuyin": "ㄓ ㄉㄠˋ",
                        "pinyin": "zhī dào",
                        "gloss_en": "the way of",
                    },
                ],
            }
        )

        self.assertEqual(rows[0]["phrase"], {"text": "大学(大學) 〃", "rowspan": 2})
        self.assertIsNone(rows[1]["phrase"])
        self.assertEqual(rows[2]["phrase"], {"text": "之道 〃", "rowspan": 2})
        self.assertIsNone(rows[3]["phrase"])
        self.assertEqual(rows[0]["phrase_translation"], {"text": "great learning", "rowspan": 2})
        self.assertEqual(rows[2]["phrase_translation"], {"text": "the way of", "rowspan": 2})

    def test_build_character_rows_uses_explicit_character_glosses_for_multi_character_lines(self) -> None:
        rows = build_character_rows(
            {
                "id": "demo-line-glosses",
                "layers": {
                    "traditional": "學而",
                    "simplified": "学而",
                    "zhuyin": "ㄒㄩㄝˊ ㄦˊ",
                    "pinyin": "xué ér",
                    "gloss_en": "study and",
                    "translation_en": "Study and practice.",
                },
                "character_glosses_en": ["study", "and"],
            }
        )

        self.assertEqual(rows[0]["gloss_en"], "study")
        self.assertEqual(rows[1]["gloss_en"], "and")
        self.assertEqual(rows[0]["pinyin"], "xué(ㄒㄩㄝˊ)")
        self.assertEqual(rows[1]["pinyin"], "ér(ㄦˊ)")

    def test_build_character_rows_marks_punctuation_and_preserves_indices(self) -> None:
        rows = build_character_rows(
            {
                "id": "demo-line-punctuation",
                "layers": {
                    "traditional": "學，問。",
                    "simplified": "学，问。",
                    "zhuyin": "ㄒㄩㄝˊ，ㄨㄣˋ。",
                    "pinyin": "xué, wèn.",
                    "gloss_en": "study; ask",
                    "translation_en": "Study and ask.",
                },
                "character_glosses_en": ["study", "", "ask", ""],
            }
        )

        self.assertFalse(rows[0]["is_punctuation"])
        self.assertTrue(rows[1]["is_punctuation"])
        self.assertFalse(rows[2]["is_punctuation"])
        self.assertTrue(rows[3]["is_punctuation"])
        self.assertEqual([row["char_index"] for row in rows], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
