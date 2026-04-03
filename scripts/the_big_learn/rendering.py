from __future__ import annotations

import unicodedata

from .display import format_hanzi_pair, format_reading_pair


def _is_punctuation(char: str) -> bool:
    return char.isspace() or unicodedata.category(char).startswith("P")


def _tokenize_phonetic_layer(text: str) -> list[str]:
    cleaned = "".join(" " if _is_punctuation(char) else char for char in text)
    return cleaned.split()


def _normalize_character_gloss(text: str) -> str:
    parts = [part.strip() for part in text.split(";")]
    normalized = "; ".join(part for part in parts if part)
    return normalized.strip()


def _build_gloss_cells(line: dict, simplified_chars: list[str]) -> list[str]:
    explicit_glosses = line.get("character_glosses_en")
    if explicit_glosses is not None:
        if not isinstance(explicit_glosses, list) or not all(isinstance(gloss, str) for gloss in explicit_glosses):
            raise ValueError(f"Invalid character glosses for {line['id']}")

        if len(explicit_glosses) == len(simplified_chars):
            return [_normalize_character_gloss(gloss) for gloss in explicit_glosses]

        gloss_cells = [""] * len(simplified_chars)
        non_punctuation_count = sum(0 if _is_punctuation(char) else 1 for char in simplified_chars)
        if len(explicit_glosses) != non_punctuation_count:
            raise ValueError(f"Mismatched character gloss counts for {line['id']}")

        gloss_index = 0
        for index, simplified_char in enumerate(simplified_chars):
            if _is_punctuation(simplified_char):
                continue
            gloss_cells[index] = _normalize_character_gloss(explicit_glosses[gloss_index])
            gloss_index += 1
        return gloss_cells

    gloss_cells = [""] * len(simplified_chars)
    cursor = 0

    for segment in line.get("segments", []):
        segment_text = segment["simplified"]
        if len(segment_text) != 1:
            continue

        start = line["layers"]["simplified"].find(segment_text, cursor)
        if start == -1:
            start = line["layers"]["simplified"].find(segment_text)
        if start == -1:
            continue

        gloss_cells[start] = segment["gloss_en"]
        cursor = start + len(segment_text)

    if any(gloss_cells):
        return gloss_cells

    if sum(0 if _is_punctuation(char) else 1 for char in simplified_chars) == 1:
        for index, char in enumerate(simplified_chars):
            if not _is_punctuation(char):
                gloss_cells[index] = line["layers"]["gloss_en"]
                break

    return gloss_cells


def _find_segment_ranges(line: dict) -> list[dict[str, int | str]]:
    ranges: list[dict[str, int | str]] = []
    cursor = 0
    simplified_text = line["layers"]["simplified"]

    for segment in line.get("segments", []):
        segment_text = segment["simplified"]
        if not segment_text:
            continue

        start = simplified_text.find(segment_text, cursor)
        if start == -1:
            start = simplified_text.find(segment_text)
        if start == -1:
            continue

        end = start + len(segment_text)
        ranges.append(
            {
                "start": start,
                "end": end,
                "traditional": segment["traditional"],
                "simplified": segment["simplified"],
                "gloss_en": segment["gloss_en"],
            }
        )
        cursor = end

    return ranges


def _build_phrase_cells(
    line: dict,
    simplified_chars: list[str],
    traditional_chars: list[str],
    gloss_cells: list[str],
    *,
    layer_key: str,
) -> list[dict[str, int | str] | None]:
    phrase_cells: list[dict[str, int | str] | None] = [
        {
            "text": "",
            "rowspan": 1,
        }
        for _ in simplified_chars
    ]

    for segment_range in _find_segment_ranges(line):
        start = int(segment_range["start"])
        end = int(segment_range["end"])
        rowspan = end - start
        text = str(segment_range[layer_key])
        if layer_key == "simplified":
            text = format_hanzi_pair(str(segment_range["traditional"]), str(segment_range["simplified"]))
            if rowspan > 1 and text:
                text = f"{text} 〃"
        phrase_cells[start] = {
            "text": text,
            "rowspan": rowspan,
        }
        for index in range(start + 1, end):
            phrase_cells[index] = None

    for index, simplified_char in enumerate(simplified_chars):
        if phrase_cells[index] is None:
            continue
        if _is_punctuation(simplified_char):
            phrase_cells[index] = {
                "text": "",
                "rowspan": 1,
            }
            continue
        if phrase_cells[index]["text"]:
            continue
        if layer_key == "simplified":
            phrase_cells[index] = {
                "text": format_hanzi_pair(traditional_chars[index], simplified_char),
                "rowspan": 1,
            }
            continue
        phrase_cells[index] = {
            "text": gloss_cells[index],
            "rowspan": 1,
        }

    return phrase_cells


def build_character_rows(line: dict) -> list[dict[str, object]]:
    simplified_chars = list(line["layers"]["simplified"])
    traditional_chars = list(line["layers"]["traditional"])
    if len(traditional_chars) != len(simplified_chars):
        raise ValueError(f"Mismatched Hanzi character counts for {line['id']}")

    zhuyin_tokens = _tokenize_phonetic_layer(line["layers"]["zhuyin"])
    pinyin_tokens = _tokenize_phonetic_layer(line["layers"]["pinyin"])
    expected_token_count = sum(0 if _is_punctuation(char) else 1 for char in simplified_chars)

    if len(zhuyin_tokens) != expected_token_count:
        raise ValueError(f"Mismatched phonetic token counts for {line['id']}")
    if len(pinyin_tokens) != expected_token_count:
        raise ValueError(f"Mismatched phonetic token counts for {line['id']}")

    gloss_cells = _build_gloss_cells(line, simplified_chars)
    phrase_cells = _build_phrase_cells(line, simplified_chars, traditional_chars, gloss_cells, layer_key="simplified")
    phrase_translation_cells = _build_phrase_cells(
        line,
        simplified_chars,
        traditional_chars,
        gloss_cells,
        layer_key="gloss_en",
    )
    rows: list[dict[str, object]] = []
    token_index = 0

    for index, simplified_char in enumerate(simplified_chars):
        is_punctuation = _is_punctuation(simplified_char)
        pinyin_token = simplified_char
        zhuyin_token = simplified_char
        pinyin = simplified_char
        if not is_punctuation:
            zhuyin_token = zhuyin_tokens[token_index]
            pinyin_token = pinyin_tokens[token_index]
            pinyin = format_reading_pair(zhuyin_token, pinyin_token)
            token_index += 1

        row = {
            "char_index": index + 1,
            "traditional_char": traditional_chars[index],
            "simplified_char": simplified_char,
            "pinyin_token": pinyin_token,
            "zhuyin_token": zhuyin_token,
            "pinyin": pinyin,
            "gloss_en": gloss_cells[index],
            "phrase": phrase_cells[index],
            "phrase_translation": phrase_translation_cells[index],
            "is_punctuation": is_punctuation,
        }
        rows.append(row)

    return rows
