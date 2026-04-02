from __future__ import annotations

import html
import json
import unicodedata

from .display import format_hanzi_layers, format_hanzi_pair, format_reading_pair


CHARACTER_MODE_ORDER = [
    ("simplified", "Chinese"),
    ("pinyin", "Reading"),
    ("gloss_en", "English Definition"),
]
PHRASE_LABEL = "Chinese Phrase"
PHRASE_TRANSLATION_LABEL = "English Phrase Translation"
REPEATED_PHRASE_MARKER = " 〃"
FLOW_PROMPT_PREFIX = (
    "Raise any questions or comments as they come up. "
    "If a character feels worth unpacking, ask to explode it; "
    "if a flashcard feels especially significant or relevant, flag it. "
    "While I respond, keep reading and come back to the reply as it appears so the flow of reading stays intact."
)
TRANSLATION_PROMPT = f"{FLOW_PROMPT_PREFIX}\nYour translation?"
DEFAULT_CHARACTER_LAYOUT = "table"
STACKED_CHARACTER_LAYOUT = "stacked"
CHARACTER_LAYOUT_CHOICES = frozenset({DEFAULT_CHARACTER_LAYOUT, STACKED_CHARACTER_LAYOUT})


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


def _mark_repeated_phrase(text: str, *, rowspan: int, layer_key: str) -> str:
    if layer_key == "simplified" and rowspan > 1 and text:
        return f"{text}{REPEATED_PHRASE_MARKER}"
    return text


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
        phrase_cells[start] = {
            "text": _mark_repeated_phrase(text, rowspan=rowspan, layer_key=layer_key),
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
    rows: list[dict[str, str | dict[str, int | str] | None]] = []
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
        row = {
            "is_punctuation": is_punctuation,
            "traditional_char": traditional_chars[index],
            "simplified_char": simplified_char,
            "zhuyin_token": zhuyin_token,
            "pinyin_token": pinyin_token,
            "simplified": format_hanzi_pair(traditional_chars[index], simplified_char),
            "pinyin": pinyin,
            "gloss_en": gloss_cells[index],
            "phrase": phrase_cells[index],
            "phrase_translation_en": phrase_translation_cells[index],
        }
        if not is_punctuation:
            token_index += 1
        rows.append(row)

    return rows


def _render_character_table(line: dict) -> str:
    chunks = [
        "<table>",
        "  <thead>",
        "    <tr>",
    ]
    for _, label in CHARACTER_MODE_ORDER:
        chunks.append(f"      <th>{html.escape(label)}</th>")
    chunks.append(f"      <th>{html.escape(PHRASE_LABEL)}</th>")
    chunks.append(f"      <th>{html.escape(PHRASE_TRANSLATION_LABEL)}</th>")
    chunks.extend(
        [
            "    </tr>",
            "  </thead>",
            "  <tbody>",
        ]
    )

    for row in build_character_rows(line):
        chunks.append("    <tr>")
        for key, _ in CHARACTER_MODE_ORDER:
            chunks.append(f"      <td>{html.escape(str(row[key]))}</td>")

        phrase_cell = row["phrase"]
        if phrase_cell is not None:
            rowspan = int(phrase_cell["rowspan"])
            text = html.escape(str(phrase_cell["text"]))
            if rowspan > 1:
                chunks.append(f"      <td rowspan=\"{rowspan}\">{text}</td>")
            else:
                chunks.append(f"      <td>{text}</td>")

        phrase_translation_cell = row["phrase_translation_en"]
        if phrase_translation_cell is not None:
            rowspan = int(phrase_translation_cell["rowspan"])
            text = html.escape(str(phrase_translation_cell["text"]))
            if rowspan > 1:
                chunks.append(f"      <td rowspan=\"{rowspan}\">{text}</td>")
            else:
                chunks.append(f"      <td>{text}</td>")

        chunks.append("    </tr>")

    chunks.extend(
        [
            "  </tbody>",
            "</table>",
        ]
    )

    return "\n".join(chunks)


def _render_stacked_character_rows(line: dict) -> str:
    rows = build_character_rows(line)
    chunks: list[str] = []

    for row in rows:
        phrase_cell = row["phrase"]
        phrase_text = "" if phrase_cell is None else str(phrase_cell["text"])

        phrase_translation_cell = row["phrase_translation_en"]
        phrase_translation_text = "" if phrase_translation_cell is None else str(phrase_translation_cell["text"])

        chunks.append(f"Chinese: {row['simplified']}")
        chunks.append(f"Reading: {row['pinyin']}")

        gloss_text = str(row["gloss_en"]).strip()
        if gloss_text:
            chunks.append(f"English Definition: {gloss_text}")

        if phrase_text.strip():
            chunks.append(f"{PHRASE_LABEL}: {phrase_text}")

        if phrase_translation_text.strip():
            chunks.append(f"{PHRASE_TRANSLATION_LABEL}: {phrase_translation_text}")

        chunks.append("")

    return "\n".join(chunks).strip()


def _learner_translation_lookup(learner_translations: list[dict] | None) -> dict[str, dict[str, str]]:
    if learner_translations is None:
        return {}

    lookup: dict[str, dict[str, str]] = {}
    for translation in learner_translations:
        line_id = translation.get("line_id")
        prompt = translation.get("prompt")
        learner_translation = translation.get("learner_translation_en")
        if not isinstance(line_id, str):
            continue

        payload: dict[str, str] = {}
        if isinstance(prompt, str) and prompt.strip():
            payload["prompt"] = prompt
        if isinstance(learner_translation, str) and learner_translation.strip():
            payload["learner_translation_en"] = learner_translation

        if payload:
            lookup[line_id] = payload
    return lookup


def _format_full_line_hanzi(line: dict) -> str:
    return str(line["layers"]["simplified"])


def _line_counter_text(line: dict, fallback_index: int, fallback_total: int) -> str:
    line_index = line.get("line_index_in_container")
    line_count = line.get("container_line_count")

    if isinstance(line_index, int) and isinstance(line_count, int) and line_index > 0 and line_count > 0:
        return f"Line {line_index}/{line_count}"

    return f"Line {fallback_index}/{fallback_total}"


def _line_location_text(line: dict, fallback_index: int, fallback_total: int) -> str:
    parts = [_line_counter_text(line, fallback_index, fallback_total)]
    line_id = line.get("id")
    if isinstance(line_id, str) and line_id.strip():
        parts.append(line_id)
    return " | ".join(parts)


def _normalize_character_layout(character_layout: str) -> str:
    normalized = character_layout.strip().lower()
    if normalized not in CHARACTER_LAYOUT_CHOICES:
        allowed = ", ".join(sorted(CHARACTER_LAYOUT_CHOICES))
        raise ValueError(f"Unknown character layout {character_layout!r}. Expected one of: {allowed}.")
    return normalized


def render_lines_markdown(
    lines: list[dict],
    learner_translations: list[dict] | None = None,
    *,
    character_layout: str = DEFAULT_CHARACTER_LAYOUT,
) -> str:
    normalized_character_layout = _normalize_character_layout(character_layout)
    learner_translation_by_line = _learner_translation_lookup(learner_translations)
    chunks: list[str] = []
    total_lines = len(lines)
    for index, line in enumerate(lines, start=1):
        chunks.append(TRANSLATION_PROMPT)
        chunks.append(_format_full_line_hanzi(line))
        chunks.append(line["layers"]["translation_en"])
        chunks.append("")
        if normalized_character_layout == STACKED_CHARACTER_LAYOUT:
            chunks.append(_render_stacked_character_rows(line))
        else:
            chunks.append(_render_character_table(line))
        chunks.append("")
        chunks.append(line["layers"]["translation_en"])
        chunks.append(_format_full_line_hanzi(line))
        chunks.append(_line_location_text(line, index, total_lines))
        chunks.append(TRANSLATION_PROMPT)
        learner_translation = learner_translation_by_line.get(line["id"])
        if learner_translation is not None:
            recorded_translation = learner_translation.get("learner_translation_en")
            if recorded_translation is not None:
                chunks.append(recorded_translation)
        if line.get("notes"):
            chunks.append("")
            chunks.append("- Notes:")
            for note in line["notes"]:
                chunks.append(f"  - {note}")
        chunks.append("")
    return "\n".join(chunks).strip()


def render_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
