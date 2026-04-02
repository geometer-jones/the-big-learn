from __future__ import annotations

import unittest

from the_big_learn.rendering import TRANSLATION_PROMPT, build_character_rows, render_lines_markdown


class RenderingTests(unittest.TestCase):
    def test_render_lines_markdown_renders_full_line_then_character_grid(self) -> None:
        lines = [
            {
                "id": "demo-line-001",
                "layers": {
                    "traditional": "學問之道，在止於善。",
                    "simplified": "学问之道，在止于善。",
                    "zhuyin": "ㄒㄩㄝˊ ㄨㄣˋ ㄓ ㄉㄠˋ，ㄗㄞˋ ㄓˇ ㄩˊ ㄕㄢˋ。",
                    "pinyin": "xué wèn zhī dào, zài zhǐ yú shàn.",
                    "gloss_en": "the way of learning rests in goodness",
                    "translation_en": "The way of learning rests in goodness.",
                },
                "segments": [
                    {
                        "id": "demo-line-001-a",
                        "traditional": "善",
                        "simplified": "善",
                        "zhuyin": "ㄕㄢˋ",
                        "pinyin": "shàn",
                        "gloss_en": "goodness",
                    }
                ],
            }
        ]

        output = render_lines_markdown(lines)

        self.assertIn("学问之道，在止于善。", output)
        self.assertNotIn("学问之道，在止于善。(學問之道，在止於善。)", output)
        self.assertIn("The way of learning rests in goodness.", output)
        self.assertIn("<table>", output)
        self.assertIn("<th>Chinese</th>", output)
        self.assertIn("<th>Reading</th>", output)
        self.assertIn("<th>English Definition</th>", output)
        self.assertIn("<th>Chinese Phrase</th>", output)
        self.assertIn("<th>English Phrase Translation</th>", output)
        self.assertIn("<td>学(學)</td>", output)
        self.assertIn("<td>xué(ㄒㄩㄝˊ)</td>", output)
        self.assertIn("<td>道</td>", output)
        self.assertIn("<td>善</td>", output)
        self.assertIn("<td>goodness</td>", output)
        self.assertNotIn("English Transliteration", output)
        self.assertEqual(output.count("学问之道，在止于善。"), 2)
        self.assertEqual(output.count("The way of learning rests in goodness."), 2)
        self.assertLess(output.index("<td>goodness</td>"), output.rindex("The way of learning rests in goodness."))
        self.assertLess(
            output.rindex("The way of learning rests in goodness."),
            output.rindex("学问之道，在止于善。"),
        )
        self.assertIn("Line 1/1 | demo-line-001", output)
        self.assertEqual(output.count(TRANSLATION_PROMPT), 2)
        self.assertIn("Raise any questions or comments as they come up.", output)
        self.assertIn("flag it.", output)
        self.assertNotIn("- Traditional:", output)
        self.assertNotIn("| Simplified | Traditional | Zhuyin | Pinyin | Gloss EN |", output)

    def test_render_lines_markdown_leaves_multi_character_segment_glosses_out_of_char_column(self) -> None:
        lines = [
            {
                "id": "demo-line-002",
                "layers": {
                    "traditional": "知止而定。",
                    "simplified": "知止而定。",
                    "zhuyin": "ㄓ ㄓˇ ㄦˊ ㄉㄧㄥˋ。",
                    "pinyin": "zhī zhǐ ér dìng.",
                    "gloss_en": "know where to stop, then settle",
                    "translation_en": "Know where to stop, then settle.",
                },
                "segments": [
                    {
                        "id": "demo-line-002-a",
                        "traditional": "知止",
                        "simplified": "知止",
                        "zhuyin": "ㄓ ㄓˇ",
                        "pinyin": "zhī zhǐ",
                        "gloss_en": "know where to stop",
                    }
                ],
            }
        ]

        output = render_lines_markdown(lines)

        self.assertIn("<td>知</td>", output)
        self.assertIn("<td>止</td>", output)
        self.assertIn("<td rowspan=\"2\">知止 〃</td>", output)
        self.assertIn("<td rowspan=\"2\">know where to stop</td>", output)
        self.assertLess(
            output.rindex("知止而定。"),
            output.index("Line 1/1 | demo-line-002"),
        )
        self.assertTrue(output.rstrip().endswith(f"Line 1/1 | demo-line-002\n{TRANSLATION_PROMPT}"))

    def test_render_lines_markdown_prefers_explicit_container_position_metadata(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line-positioned",
                    "line_index_in_container": 2,
                    "container_line_count": 3,
                    "layers": {
                        "traditional": "知止",
                        "simplified": "知止",
                        "zhuyin": "ㄓ ㄓˇ",
                        "pinyin": "zhī zhǐ",
                        "gloss_en": "know where to stop",
                        "translation_en": "Know where to stop.",
                    },
                }
            ]
        )

        self.assertIn("Line 2/3 | demo-line-positioned", output)
        self.assertNotIn("Line 1/1 | demo-line-positioned", output)

    def test_render_lines_markdown_uses_single_character_segment_gloss_when_available(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line",
                    "layers": {
                        "traditional": "人心",
                        "simplified": "人心",
                        "zhuyin": "ㄖㄣˊ ㄒㄧㄣ",
                        "pinyin": "rén xīn",
                        "gloss_en": "human heart",
                        "translation_en": "the human heart",
                    },
                    "segments": [
                        {
                            "id": "demo-line-a",
                            "traditional": "人",
                            "simplified": "人",
                            "zhuyin": "ㄖㄣˊ",
                            "pinyin": "rén",
                            "gloss_en": "person",
                        }
                    ],
                }
            ]
        )

        self.assertIn("<td>人</td>", output)
        self.assertIn("<td>rén(ㄖㄣˊ)</td>", output)
        self.assertIn("<td>person</td>", output)
        self.assertIn("<td>心</td>", output)
        self.assertLess(output.rindex("人心"), output.index("Line 1/1 | demo-line"))
        self.assertTrue(output.rstrip().endswith(f"Line 1/1 | demo-line\n{TRANSLATION_PROMPT}"))

    def test_render_lines_markdown_keeps_tone_marked_pinyin_and_phrase_cells(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line-umlaut",
                    "layers": {
                        "traditional": "慮",
                        "simplified": "虑",
                        "zhuyin": "ㄌㄩˋ",
                        "pinyin": "lǜ",
                        "gloss_en": "deliberate",
                        "translation_en": "deliberate",
                    },
                    "segments": [
                        {
                            "id": "demo-line-umlaut-a",
                            "traditional": "慮",
                            "simplified": "虑",
                            "zhuyin": "ㄌㄩˋ",
                            "pinyin": "lǜ",
                            "gloss_en": "deliberate",
                        }
                    ],
                }
            ]
        )

        self.assertIn("<td>虑(慮)</td>", output)
        self.assertIn("<td>lǜ(ㄌㄩˋ)</td>", output)
        self.assertIn("<td>deliberate</td>", output)
        self.assertLess(output.rindex("虑"), output.index("Line 1/1 | demo-line-umlaut"))
        self.assertTrue(output.rstrip().endswith(f"Line 1/1 | demo-line-umlaut\n{TRANSLATION_PROMPT}"))

    def test_render_lines_markdown_renders_phrase_translation_cells_with_segment_rowspan(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line-phrase",
                    "layers": {
                        "traditional": "大學之道",
                        "simplified": "大学之道",
                        "zhuyin": "ㄉㄚˋ ㄒㄩㄝˊ ㄓ ㄉㄠˋ",
                        "pinyin": "dà xué zhī dào",
                        "gloss_en": "great learning, the way of",
                        "translation_en": "The way of great learning.",
                    },
                    "segments": [
                        {
                            "id": "demo-line-phrase-a",
                            "traditional": "大學",
                            "simplified": "大学",
                            "zhuyin": "ㄉㄚˋ ㄒㄩㄝˊ",
                            "pinyin": "dà xué",
                            "gloss_en": "great learning",
                        },
                        {
                            "id": "demo-line-phrase-b",
                            "traditional": "之道",
                            "simplified": "之道",
                            "zhuyin": "ㄓ ㄉㄠˋ",
                            "pinyin": "zhī dào",
                            "gloss_en": "the way of",
                        },
                    ],
                }
            ]
        )

        self.assertIn("<td rowspan=\"2\">大学(大學) 〃</td>", output)
        self.assertIn("<td rowspan=\"2\">之道 〃</td>", output)
        self.assertIn("<td rowspan=\"2\">great learning</td>", output)
        self.assertIn("<td rowspan=\"2\">the way of</td>", output)

    def test_build_character_rows_leaves_spanned_phrase_cells_absent_until_next_segment(self) -> None:
        rows = build_character_rows(
            {
                "id": "demo-line-phrase-cells",
                "layers": {
                    "traditional": "大學之道",
                    "simplified": "大学之道",
                    "zhuyin": "ㄉㄚˋ ㄒㄩㄝˊ ㄓ ㄉㄠˋ",
                    "pinyin": "dà xué zhī dào",
                    "gloss_en": "great learning, the way of",
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
        self.assertEqual(rows[0]["phrase_translation_en"], {"text": "great learning", "rowspan": 2})
        self.assertIsNone(rows[1]["phrase"])
        self.assertIsNone(rows[1]["phrase_translation_en"])
        self.assertEqual(rows[2]["phrase"], {"text": "之道 〃", "rowspan": 2})
        self.assertEqual(rows[2]["phrase_translation_en"], {"text": "the way of", "rowspan": 2})
        self.assertIsNone(rows[3]["phrase"])
        self.assertIsNone(rows[3]["phrase_translation_en"])

    def test_render_lines_markdown_uses_explicit_character_glosses_for_multi_character_segments(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line-glosses",
                    "character_glosses_en": ["of; 's; linker", "way; path; principle"],
                    "layers": {
                        "traditional": "之道",
                        "simplified": "之道",
                        "zhuyin": "ㄓ ㄉㄠˋ",
                        "pinyin": "zhī dào",
                        "gloss_en": "the way of",
                        "translation_en": "The way of.",
                    },
                    "segments": [
                        {
                            "id": "demo-line-glosses-a",
                            "traditional": "之道",
                            "simplified": "之道",
                            "zhuyin": "ㄓ ㄉㄠˋ",
                            "pinyin": "zhī dào",
                            "gloss_en": "the way of",
                        }
                    ],
                }
            ]
        )

        self.assertIn("<th>English Definition</th>", output)
        self.assertIn("<th>Chinese Phrase</th>", output)
        self.assertIn("<td>zhī(ㄓ)</td>", output)
        self.assertIn("<td>of; &#x27;s; linker</td>", output)

    def test_render_lines_markdown_can_render_stacked_character_fallback(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line-stacked",
                    "character_glosses_en": [
                        "know",
                        "stop",
                        "and",
                        "settle",
                    ],
                    "layers": {
                        "traditional": "知止而定。",
                        "simplified": "知止而定。",
                        "zhuyin": "ㄓ ㄓˇ ㄦˊ ㄉㄧㄥˋ。",
                        "pinyin": "zhī zhǐ ér dìng.",
                        "gloss_en": "know where to stop, then settle",
                        "translation_en": "Know where to stop, then settle.",
                    },
                    "segments": [
                        {
                            "id": "demo-line-stacked-a",
                            "traditional": "知止",
                            "simplified": "知止",
                            "zhuyin": "ㄓ ㄓˇ",
                            "pinyin": "zhī zhǐ",
                            "gloss_en": "know where to stop",
                        }
                    ],
                }
            ],
            character_layout="stacked",
        )

        self.assertNotIn("<table>", output)
        self.assertIn("Chinese: 知", output)
        self.assertIn("Reading: zhī(ㄓ)", output)
        self.assertIn("English Definition: know", output)
        self.assertEqual(output.count("Chinese Phrase: 知止 〃"), 1)
        self.assertEqual(output.count("English Phrase Translation: know where to stop"), 1)
        self.assertIn("Chinese: 止\nReading: zhǐ(ㄓˇ)\nEnglish Definition: stop\n\nChinese: 而", output)
        self.assertIn("Line 1/1 | demo-line-stacked", output)
        self.assertTrue(output.rstrip().endswith(f"Line 1/1 | demo-line-stacked\n{TRANSLATION_PROMPT}"))

    def test_render_lines_markdown_fills_single_character_phrase_translation_cells_from_character_definitions(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line-fallback-phrase-translation",
                    "character_glosses_en": ["at; in; located at"],
                    "layers": {
                        "traditional": "在",
                        "simplified": "在",
                        "zhuyin": "ㄗㄞˋ",
                        "pinyin": "zài",
                        "gloss_en": "in",
                        "translation_en": "In.",
                    },
                }
            ]
        )

        self.assertIn("<td>在</td>", output)
        self.assertIn("<td>zài(ㄗㄞˋ)</td>", output)
        self.assertIn("<td>at; in; located at</td>", output)
        self.assertEqual(output.count("<td>at; in; located at</td>"), 2)

    def test_render_lines_markdown_normalizes_semicolon_spacing_in_character_glosses(self) -> None:
        output = render_lines_markdown(
            [
                {
                    "id": "demo-line-semicolons",
                    "character_glosses_en": ["and;then ; yet"],
                    "layers": {
                        "traditional": "而",
                        "simplified": "而",
                        "zhuyin": "ㄦˊ",
                        "pinyin": "ér",
                        "gloss_en": "and then",
                        "translation_en": "and then",
                    },
                }
            ]
        )

        self.assertIn("<td>and; then; yet</td>", output)
        self.assertNotIn("<td>and;then ; yet</td>", output)

    def test_render_lines_markdown_places_learner_translation_after_bottom_chinese(self) -> None:
        lines = [
            {
                "id": "demo-line-personal",
                "layers": {
                    "traditional": "知止",
                    "simplified": "知止",
                    "zhuyin": "ㄓ ㄓˇ",
                    "pinyin": "zhī zhǐ",
                    "gloss_en": "know where to stop",
                    "translation_en": "Know where to stop.",
                },
                "segments": [
                    {
                        "id": "demo-line-personal-a",
                        "traditional": "知止",
                        "simplified": "知止",
                        "zhuyin": "ㄓ ㄓˇ",
                        "pinyin": "zhī zhǐ",
                        "gloss_en": "know where to stop",
                    }
                ],
            }
        ]

        output = render_lines_markdown(
            lines,
            learner_translations=[
                {
                    "id": "lt-demo",
                    "line_id": "demo-line-personal",
                    "prompt": "Translate the line into English in your own voice.",
                    "learner_translation_en": "I should know where to stop.",
                }
            ],
        )

        self.assertEqual(output.count(TRANSLATION_PROMPT), 2)
        self.assertIn("I should know where to stop.", output)
        self.assertNotIn("Instruction:", output)
        self.assertIn("Line 1/1 | demo-line-personal", output)
        self.assertLess(output.rindex("知止"), output.index("Line 1/1 | demo-line-personal"))
        self.assertLess(
            output.index("Line 1/1 | demo-line-personal"),
            output.rindex(TRANSLATION_PROMPT),
        )
        self.assertLess(
            output.rindex(TRANSLATION_PROMPT),
            output.index("I should know where to stop."),
        )
        self.assertTrue(output.rstrip().endswith(f"{TRANSLATION_PROMPT}\nI should know where to stop."))


if __name__ == "__main__":
    unittest.main()
