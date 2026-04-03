from __future__ import annotations

import json
from pathlib import Path
import random
import time
import unicodedata
from typing import Any

from .display import canonical_layer_name, format_hanzi_layers, format_layer_value, format_reading_layers
from .rendering import build_character_rows
from .updates import state_dir


FLASHCARD_DIRNAME = "flashcards"
FLASHCARD_BANK_DIRNAME = "bank"
FLASHCARD_VARIATIONS_DIRNAME = "variations"
FLASHCARD_REVIEW_STATE_FILENAME = "review-state.json"

PROMPT_LAYERS = {
    "traditional",
    "simplified",
    "zhuyin",
    "pinyin",
    "gloss_en",
    "translation_en",
}

ENTRY_STATUSES = {
    "draft",
    "active",
    "suspended",
}

ORIGIN_KINDS = {
    "learner-question",
    "line-index",
    "manual-curation",
    "review-session",
}

DEFAULT_ELIGIBLE_PROMPT_LAYERS = (
    "simplified",
    "traditional",
    "pinyin",
    "zhuyin",
    "gloss_en",
    "translation_en",
)
CHARACTER_INDEX_TAG = "character-index"
CHARACTER_INDEX_ORIGIN_KIND = "line-index"
CHARACTER_INDEX_ORIGIN_NOTE = "Auto-indexed from guided-reading line shells."


def _slugify_pinyin(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    words = [word for word in stripped.lower().replace("'", "").split() if word]
    return "-".join(words)


def _normalize_variation_text(text: str) -> str:
    return " ".join(text.split())


def _normalize_semicolon_text(text: str) -> str:
    return "; ".join(part for part in (item.strip() for item in text.split(";")) if part)


def _merge_semicolon_text(existing: str, incoming: str) -> str:
    merged: list[str] = []
    seen: set[str] = set()
    for text in (existing, incoming):
        for part in (item.strip() for item in text.split(";")):
            if not part or part in seen:
                continue
            seen.add(part)
            merged.append(part)
    return "; ".join(merged)


def _merge_string_lists(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for items in (existing, incoming):
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
    return merged


def _codepoint_slug(text: str) -> str:
    return "-".join(f"u{ord(char):x}" for char in text)


def _effective_variation_layer_name(layers: dict[str, str], layer: str) -> str:
    layer_name = canonical_layer_name(layer)
    if layer_name in {"gloss_en", "translation_en"}:
        gloss_text = _normalize_variation_text(format_layer_value(layers, "gloss_en"))
        translation_text = _normalize_variation_text(format_layer_value(layers, "translation_en"))
        if gloss_text == translation_text:
            return "english_en"
    return layer_name


def build_bank_entry(question: dict, line: dict, segment: dict | None) -> dict:
    source = segment or {
        "traditional": line["layers"]["traditional"],
        "simplified": line["layers"]["simplified"],
        "zhuyin": line["layers"]["zhuyin"],
        "pinyin": line["layers"]["pinyin"],
        "gloss_en": line["layers"]["gloss_en"],
        "translation_en": line["layers"]["translation_en"],
    }
    slug = _slugify_pinyin(source["pinyin"])
    entry_id = f"fc-{line['work']}-{line['order']:03d}-{slug}"

    return {
        "id": entry_id,
        "source_work": line["work"],
        "source_line_ids": [line["id"]],
        "source_segment_ids": [segment["id"]] if segment else [],
        "origin": {
            "kind": "learner-question",
            "question_id": question["id"],
            "note": f"Learner asked about {format_hanzi_layers(source)}.",
        },
        "layers": {
            "traditional": source["traditional"],
            "simplified": source["simplified"],
            "zhuyin": source["zhuyin"],
            "pinyin": source["pinyin"],
            "gloss_en": source["gloss_en"],
            "translation_en": source.get("translation_en", source["gloss_en"]),
        },
        "eligible_prompt_layers": list(DEFAULT_ELIGIBLE_PROMPT_LAYERS),
        "tags": [
            line["work"],
            "learner-question",
        ],
        "status": "draft",
        "significance_flag_count": 0,
    }


def character_index_entry_id(traditional: str, simplified: str) -> str:
    simplified_slug = _codepoint_slug(simplified)
    traditional_slug = _codepoint_slug(traditional)
    if simplified_slug == traditional_slug:
        return f"fc-char-{simplified_slug}"
    return f"fc-char-{simplified_slug}-{traditional_slug}"


def build_variations(bank_entry: dict, policy: dict) -> list[dict]:
    variations = []
    seen: set[tuple[str, str, str, str]] = set()
    for pair in policy["default_priority_pairs"]:
        prompt_layer = pair["prompt_layer"]
        answer_layer = pair["answer_layer"]
        prompt_layer_name = _effective_variation_layer_name(bank_entry["layers"], prompt_layer)
        answer_layer_name = _effective_variation_layer_name(bank_entry["layers"], answer_layer)
        if prompt_layer_name == answer_layer_name:
            continue
        prompt_text = format_layer_value(bank_entry["layers"], prompt_layer)
        answer_text = format_layer_value(bank_entry["layers"], answer_layer)
        dedupe_key = (
            prompt_layer_name,
            answer_layer_name,
            _normalize_variation_text(prompt_text),
            _normalize_variation_text(answer_text),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        variations.append(
            {
                "bank_entry_id": bank_entry["id"],
                "prompt_layer": prompt_layer,
                "answer_layer": answer_layer,
                "prompt_text": prompt_text,
                "answer_text": answer_text,
            }
        )
    return variations


def flashcard_store_dir() -> Path:
    return state_dir() / FLASHCARD_DIRNAME


def flashcard_bank_dir() -> Path:
    return flashcard_store_dir() / FLASHCARD_BANK_DIRNAME


def flashcard_variations_dir() -> Path:
    return flashcard_store_dir() / FLASHCARD_VARIATIONS_DIRNAME


def flashcard_review_state_path() -> Path:
    return flashcard_store_dir() / FLASHCARD_REVIEW_STATE_FILENAME


def _write_json_file(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _require_non_empty_string(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Flashcard field {key!r} must be a non-empty string.")
    return value.strip()


def _validate_optional_string_list(payload: dict, key: str) -> list[str]:
    value = payload.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"Flashcard field {key!r} must be a list of non-empty strings.")
    return [item.strip() for item in value]


def _validate_optional_non_negative_int(payload: dict, key: str) -> int | None:
    if key not in payload:
        return None
    value = payload.get(key)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Flashcard field {key!r} must be a non-negative integer.")
    return value


def _validate_citation(citation: Any, *, index: int) -> dict[str, Any]:
    if not isinstance(citation, dict):
        raise ValueError(f"Flashcard citation {index} must be a JSON object.")

    normalized: dict[str, Any] = {}
    for key in ("work", "section", "line_id"):
        value = citation.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Flashcard citation {index} field {key!r} must be a non-empty string.")
        normalized[key] = value.strip()

    char_index = citation.get("char_index")
    if not isinstance(char_index, int) or char_index < 1:
        raise ValueError(f"Flashcard citation {index} field 'char_index' must be a positive integer.")
    normalized["char_index"] = char_index

    source_url = citation.get("source_url")
    if source_url is not None:
        if not isinstance(source_url, str) or not source_url.strip():
            raise ValueError(f"Flashcard citation {index} field 'source_url' must be a non-empty string.")
        normalized["source_url"] = source_url.strip()

    line_index_in_container = citation.get("line_index_in_container")
    if line_index_in_container is not None:
        if not isinstance(line_index_in_container, int) or line_index_in_container < 1:
            raise ValueError(
                f"Flashcard citation {index} field 'line_index_in_container' must be a positive integer."
            )
        normalized["line_index_in_container"] = line_index_in_container

    for key in (
        "char_traditional",
        "char_simplified",
        "char_zhuyin",
        "char_pinyin",
        "char_gloss_en",
        "line_traditional",
        "line_simplified",
        "line_zhuyin",
        "line_pinyin",
        "line_translation_en",
    ):
        value = citation.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Flashcard citation {index} field {key!r} must be a non-empty string.")
        normalized[key] = _normalize_semicolon_text(value.strip()) if key in {"char_gloss_en", "line_translation_en"} else value.strip()

    return normalized


def _validate_citation_list(payload: dict, key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Flashcard field {key!r} must be a list of citations.")

    normalized: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for index, citation in enumerate(value, start=1):
        normalized_citation = _validate_citation(citation, index=index)
        dedupe_key = (
            normalized_citation.get("source_url"),
            normalized_citation["work"],
            normalized_citation["section"],
            normalized_citation["line_id"],
            normalized_citation["char_index"],
            normalized_citation.get("line_index_in_container"),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(normalized_citation)
    return normalized


def _validate_bank_entry(bank_entry: dict) -> dict:
    if not isinstance(bank_entry, dict):
        raise ValueError("Flashcard bank entry payload must be a JSON object.")

    entry_id = _require_non_empty_string(bank_entry, "id")
    source_work = _require_non_empty_string(bank_entry, "source_work")
    status = _require_non_empty_string(bank_entry, "status")
    if status not in ENTRY_STATUSES:
        raise ValueError(f"Unsupported flashcard status: {status!r}")

    origin = bank_entry.get("origin")
    if not isinstance(origin, dict):
        raise ValueError("Flashcard origin must be a JSON object.")
    origin_kind = _require_non_empty_string(origin, "kind")
    if origin_kind not in ORIGIN_KINDS:
        raise ValueError(f"Unsupported flashcard origin kind: {origin_kind!r}")
    normalized_origin = {
        "kind": origin_kind,
    }
    question_id = origin.get("question_id")
    if question_id is not None:
        normalized_origin["question_id"] = _require_non_empty_string(origin, "question_id")
    note = origin.get("note")
    if note is not None:
        normalized_origin["note"] = _require_non_empty_string(origin, "note")

    layers = bank_entry.get("layers")
    if not isinstance(layers, dict):
        raise ValueError("Flashcard layers must be a JSON object.")
    normalized_layers = {
        key: _normalize_semicolon_text(_require_non_empty_string(layers, key))
        for key in ("traditional", "simplified", "zhuyin", "pinyin", "gloss_en", "translation_en")
    }

    eligible_prompt_layers = bank_entry.get("eligible_prompt_layers")
    if not isinstance(eligible_prompt_layers, list) or not eligible_prompt_layers:
        raise ValueError("Flashcard eligible_prompt_layers must be a non-empty list.")
    normalized_prompt_layers: list[str] = []
    seen_layers: set[str] = set()
    for layer in eligible_prompt_layers:
        if not isinstance(layer, str) or layer not in PROMPT_LAYERS:
            raise ValueError(f"Unsupported prompt layer: {layer!r}")
        if layer in seen_layers:
            continue
        seen_layers.add(layer)
        normalized_prompt_layers.append(layer)

    normalized_entry = {
        "id": entry_id,
        "source_work": source_work,
        "source_line_ids": _validate_optional_string_list(bank_entry, "source_line_ids"),
        "source_segment_ids": _validate_optional_string_list(bank_entry, "source_segment_ids"),
        "origin": normalized_origin,
        "layers": normalized_layers,
        "eligible_prompt_layers": normalized_prompt_layers,
        "status": status,
    }

    tags = bank_entry.get("tags")
    if tags is not None:
        normalized_entry["tags"] = _validate_optional_string_list(bank_entry, "tags")

    notes = bank_entry.get("notes")
    if notes is not None:
        normalized_entry["notes"] = _validate_optional_string_list(bank_entry, "notes")

    source_works = bank_entry.get("source_works")
    if source_works is not None:
        normalized_entry["source_works"] = _validate_optional_string_list(bank_entry, "source_works")

    citations = bank_entry.get("citations")
    if citations is not None:
        normalized_entry["citations"] = _validate_citation_list(bank_entry, "citations")

    significance_flag_count = _validate_optional_non_negative_int(bank_entry, "significance_flag_count")
    if significance_flag_count is not None:
        normalized_entry["significance_flag_count"] = significance_flag_count

    return normalized_entry


def _normalize_variation(bank_entry_id: str, variation: dict) -> dict:
    if not isinstance(variation, dict):
        raise ValueError("Each flashcard variation must be a JSON object.")

    variation_bank_entry_id = variation.get("bank_entry_id", bank_entry_id)
    if variation_bank_entry_id != bank_entry_id:
        raise ValueError("Flashcard variation bank_entry_id does not match the saved bank entry.")

    prompt_layer = _require_non_empty_string(variation, "prompt_layer")
    answer_layer = _require_non_empty_string(variation, "answer_layer")
    prompt_text = _require_non_empty_string(variation, "prompt_text")
    answer_text = _require_non_empty_string(variation, "answer_text")

    normalized = {
        "bank_entry_id": bank_entry_id,
        "prompt_layer": prompt_layer,
        "answer_layer": answer_layer,
        "prompt_text": prompt_text,
        "answer_text": answer_text,
    }

    hint = variation.get("hint")
    if hint is not None:
        normalized["hint"] = _require_non_empty_string(variation, "hint")

    return normalized


def load_bank_entry(bank_entry_id: str) -> dict[str, Any] | None:
    _require_non_empty_string({"bank_entry_id": bank_entry_id}, "bank_entry_id")
    entry_path = flashcard_bank_dir() / f"{bank_entry_id}.json"
    try:
        payload = json.loads(entry_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if not isinstance(payload, dict):
        raise ValueError(f"Saved flashcard bank entry {bank_entry_id!r} is not a JSON object.")
    return _validate_bank_entry(payload)


def list_bank_entries(*, statuses: set[str] | None = None) -> list[dict[str, Any]]:
    bank_dir = flashcard_bank_dir()
    if not bank_dir.exists():
        return []

    normalized_statuses = set(statuses) if statuses is not None else None
    entries: list[dict[str, Any]] = []
    for path in sorted(bank_dir.glob("*.json")):
        try:
            entry = load_bank_entry(path.stem)
        except ValueError:
            continue
        if entry is None:
            continue
        if normalized_statuses is not None and entry["status"] not in normalized_statuses:
            continue
        entries.append(entry)
    return entries


def flashcard_occurrence_count(bank_entry: dict[str, Any]) -> int:
    citations = bank_entry.get("citations")
    if not isinstance(citations, list):
        return 0
    return sum(1 for citation in citations if isinstance(citation, dict))


def flashcard_weight(bank_entry: dict[str, Any]) -> int:
    return (10 * int(bank_entry.get("significance_flag_count", 0))) + flashcard_occurrence_count(bank_entry)


def flashcard_review_faces(bank_entry: dict[str, Any]) -> dict[str, dict[str, str]]:
    layers = bank_entry["layers"]
    return {
        "hanzi": {
            "name": "hanzi",
            "text": format_hanzi_layers(layers),
        },
        "reading": {
            "name": "reading",
            "text": f"{format_reading_layers(layers)} - {layers['gloss_en']}",
        },
    }


def choose_weighted_bank_entry(
    bank_entries: list[dict[str, Any]],
    *,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    weighted_entries = [
        (
            bank_entry,
            flashcard_occurrence_count(bank_entry),
            int(bank_entry.get("significance_flag_count", 0)),
            flashcard_weight(bank_entry),
        )
        for bank_entry in bank_entries
    ]
    weighted_entries = [
        (bank_entry, occurrence_count, significance_flag_count, weight)
        for bank_entry, occurrence_count, significance_flag_count, weight in weighted_entries
        if weight > 0
    ]
    if not weighted_entries:
        raise ValueError("No flashcards with positive review weight were found.")

    total_weight = sum(weight for _, _, _, weight in weighted_entries)
    threshold = (rng or random.Random()).random() * total_weight
    cumulative = 0
    selected_entry = weighted_entries[-1]
    for candidate in weighted_entries:
        bank_entry, occurrence_count, significance_flag_count, weight = candidate
        cumulative += weight
        selected_entry = candidate
        if threshold < cumulative:
            break

    bank_entry, occurrence_count, significance_flag_count, weight = selected_entry
    return {
        "bank_entry": bank_entry,
        "occurrence_count": occurrence_count,
        "significance_flag_count": significance_flag_count,
        "weight": weight,
    }


def load_flashcard_review_state() -> dict[str, Any]:
    path = flashcard_review_state_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("Saved flashcard review state is not a JSON object.")
    return payload


def clear_flashcard_review_state() -> None:
    path = flashcard_review_state_path()
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _save_flashcard_review_state(payload: dict[str, Any]) -> None:
    _write_json_file(flashcard_review_state_path(), payload)


def run_flashcard_review_step(
    *,
    rng: random.Random | None = None,
    reset: bool = False,
) -> dict[str, Any]:
    resolved_rng = rng or random.Random()
    if reset:
        clear_flashcard_review_state()

    state = load_flashcard_review_state()
    pending = state.get("pending_card")
    if isinstance(pending, dict):
        bank_entry_id = pending.get("bank_entry_id")
        shown_face_name = pending.get("shown_face")
        if isinstance(bank_entry_id, str) and isinstance(shown_face_name, str):
            bank_entry = load_bank_entry(bank_entry_id)
            if bank_entry is not None:
                faces = flashcard_review_faces(bank_entry)
                if shown_face_name in faces:
                    shown_face = faces[shown_face_name]
                    other_face_name = "reading" if shown_face_name == "hanzi" else "hanzi"
                    clear_flashcard_review_state()
                    return {
                        "phase": "reveal",
                        "bank_entry": bank_entry,
                        "bank_entry_id": bank_entry["id"],
                        "status": bank_entry["status"],
                        "origin_kind": bank_entry["origin"]["kind"],
                        "weight": flashcard_weight(bank_entry),
                        "significance_flag_count": int(bank_entry.get("significance_flag_count", 0)),
                        "occurrence_count": flashcard_occurrence_count(bank_entry),
                        "shown_face": shown_face,
                        "hidden_face": faces[other_face_name],
                        "visible_faces": [faces["hanzi"], faces["reading"]],
                    }
        clear_flashcard_review_state()

    selected = choose_weighted_bank_entry(
        list_bank_entries(statuses={"draft", "active"}),
        rng=resolved_rng,
    )
    bank_entry = selected["bank_entry"]
    faces = flashcard_review_faces(bank_entry)
    shown_face_name = resolved_rng.choice(["hanzi", "reading"])
    shown_face = faces[shown_face_name]
    hidden_face_name = "reading" if shown_face_name == "hanzi" else "hanzi"

    _save_flashcard_review_state(
        {
            "pending_card": {
                "bank_entry_id": bank_entry["id"],
                "shown_face": shown_face_name,
            }
        }
    )

    return {
        "phase": "prompt",
        "bank_entry": bank_entry,
        "bank_entry_id": bank_entry["id"],
        "status": bank_entry["status"],
        "origin_kind": bank_entry["origin"]["kind"],
        "weight": selected["weight"],
        "significance_flag_count": selected["significance_flag_count"],
        "occurrence_count": selected["occurrence_count"],
        "shown_face": shown_face,
        "hidden_face_name": hidden_face_name,
        "visible_faces": [shown_face],
    }


def _merge_citations(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for citation in [*existing, *incoming]:
        dedupe_key = (
            citation.get("source_url"),
            citation["work"],
            citation["section"],
            citation["line_id"],
            citation["char_index"],
            citation.get("line_index_in_container"),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        merged.append(citation)
    return merged


def _merge_character_index_bank_entries(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    if existing["id"] != incoming["id"]:
        raise ValueError("Character index flashcards can only merge entries with the same id.")
    if existing.get("origin", {}).get("kind") != CHARACTER_INDEX_ORIGIN_KIND:
        raise ValueError(f"Existing flashcard {existing['id']!r} is not a character-index entry.")
    if incoming.get("origin", {}).get("kind") != CHARACTER_INDEX_ORIGIN_KIND:
        raise ValueError(f"Incoming flashcard {incoming['id']!r} is not a character-index entry.")

    merged_source_works = _merge_string_lists(
        existing.get("source_works", [existing["source_work"]]),
        incoming.get("source_works", [incoming["source_work"]]),
    )
    merged_citations = _merge_citations(existing.get("citations", []), incoming.get("citations", []))

    merged = {
        "id": existing["id"],
        "source_work": existing.get("source_work") or incoming["source_work"],
        "source_line_ids": _merge_string_lists(existing.get("source_line_ids", []), incoming.get("source_line_ids", [])),
        "source_segment_ids": _merge_string_lists(
            existing.get("source_segment_ids", []),
            incoming.get("source_segment_ids", []),
        ),
        "source_works": merged_source_works,
        "origin": {
            "kind": CHARACTER_INDEX_ORIGIN_KIND,
            "note": existing.get("origin", {}).get("note")
            or incoming.get("origin", {}).get("note")
            or CHARACTER_INDEX_ORIGIN_NOTE,
        },
        "layers": {
            "traditional": _merge_semicolon_text(existing["layers"]["traditional"], incoming["layers"]["traditional"]),
            "simplified": _merge_semicolon_text(existing["layers"]["simplified"], incoming["layers"]["simplified"]),
            "zhuyin": _merge_semicolon_text(existing["layers"]["zhuyin"], incoming["layers"]["zhuyin"]),
            "pinyin": _merge_semicolon_text(existing["layers"]["pinyin"], incoming["layers"]["pinyin"]),
            "gloss_en": _merge_semicolon_text(existing["layers"]["gloss_en"], incoming["layers"]["gloss_en"]),
            "translation_en": _merge_semicolon_text(
                existing["layers"]["translation_en"],
                incoming["layers"]["translation_en"],
            ),
        },
        "eligible_prompt_layers": _merge_string_lists(
            existing["eligible_prompt_layers"],
            incoming["eligible_prompt_layers"],
        ),
        "tags": _merge_string_lists(existing.get("tags", []), incoming.get("tags", [])),
        "status": existing["status"] if existing["status"] == "suspended" else incoming["status"],
        "citations": merged_citations,
        "significance_flag_count": max(
            int(existing.get("significance_flag_count", 0)),
            int(incoming.get("significance_flag_count", 0)),
        ),
    }

    merged_notes = _merge_string_lists(existing.get("notes", []), incoming.get("notes", []))
    if merged_notes:
        merged["notes"] = merged_notes

    return merged


def merge_character_index_entry(bank_entry: dict) -> dict[str, Any]:
    normalized_entry = _validate_bank_entry(bank_entry)
    if normalized_entry.get("origin", {}).get("kind") != CHARACTER_INDEX_ORIGIN_KIND:
        raise ValueError("Character index merge requires a flashcard with origin kind 'line-index'.")

    entry_path = flashcard_bank_dir() / f"{normalized_entry['id']}.json"
    existing = load_bank_entry(normalized_entry["id"])
    if existing is None:
        _write_json_file(entry_path, normalized_entry)
        return {
            "bank_entry": normalized_entry,
            "bank_entry_path": str(entry_path),
            "citation_delta": len(normalized_entry.get("citations", [])),
        }

    merged_entry = _merge_character_index_bank_entries(existing, normalized_entry)
    _write_json_file(entry_path, merged_entry)
    return {
        "bank_entry": merged_entry,
        "bank_entry_path": str(entry_path),
        "citation_delta": len(merged_entry.get("citations", [])) - len(existing.get("citations", [])),
    }


def _build_character_index_entry(
    work: str,
    section: str,
    line: dict[str, Any],
    row: dict[str, Any],
    *,
    char_index: int,
    source_url: str | None = None,
) -> dict[str, Any] | None:
    if row.get("is_punctuation"):
        return None

    simplified_char = str(row.get("simplified_char", "")).strip()
    traditional_char = str(row.get("traditional_char", "")).strip()
    pinyin_token = str(row.get("pinyin_token", "")).strip()
    zhuyin_token = str(row.get("zhuyin_token", "")).strip()
    gloss_en = _normalize_semicolon_text(str(row.get("gloss_en", "")).strip())
    if not all((simplified_char, traditional_char, pinyin_token, zhuyin_token, gloss_en)):
        return None

    citation: dict[str, Any] = {
        "work": work,
        "section": section,
        "line_id": str(line["id"]),
        "char_index": char_index,
        "char_traditional": traditional_char,
        "char_simplified": simplified_char,
        "char_zhuyin": zhuyin_token,
        "char_pinyin": pinyin_token,
        "char_gloss_en": gloss_en,
    }
    if isinstance(source_url, str) and source_url.strip():
        citation["source_url"] = source_url.strip()
    line_index_in_container = line.get("line_index_in_container")
    if isinstance(line_index_in_container, int) and line_index_in_container > 0:
        citation["line_index_in_container"] = line_index_in_container
    layers = line.get("layers")
    if isinstance(layers, dict):
        for key in ("traditional", "simplified", "zhuyin", "pinyin", "translation_en"):
            value = layers.get(key)
            if not isinstance(value, str) or not value.strip():
                continue
            citation_key = f"line_{key}"
            citation[citation_key] = _normalize_semicolon_text(value.strip()) if key == "translation_en" else value.strip()

    return {
        "id": character_index_entry_id(traditional_char, simplified_char),
        "source_work": work,
        "source_works": [work],
        "source_line_ids": [str(line["id"])],
        "source_segment_ids": [],
        "origin": {
            "kind": CHARACTER_INDEX_ORIGIN_KIND,
            "note": CHARACTER_INDEX_ORIGIN_NOTE,
        },
        "layers": {
            "traditional": traditional_char,
            "simplified": simplified_char,
            "zhuyin": zhuyin_token,
            "pinyin": pinyin_token,
            "gloss_en": gloss_en,
            "translation_en": gloss_en,
        },
        "eligible_prompt_layers": list(DEFAULT_ELIGIBLE_PROMPT_LAYERS),
        "tags": [CHARACTER_INDEX_TAG, work],
        "status": "active",
        "citations": [citation],
        "significance_flag_count": 0,
    }


def build_character_index_entries(
    work: str,
    section: str,
    lines: list[dict[str, Any]],
    *,
    source_url: str | None = None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in lines:
        if not isinstance(line, dict) or not isinstance(line.get("layers"), dict):
            continue
        try:
            rows = build_character_rows(line)
        except ValueError:
            continue
        for char_index, row in enumerate(rows, start=1):
            entry = _build_character_index_entry(work, section, line, row, char_index=char_index, source_url=source_url)
            if entry is not None:
                entries.append(entry)
    return entries


def save_character_index_entries(
    work: str,
    section: str,
    lines: list[dict[str, Any]],
    *,
    source_url: str | None = None,
) -> dict[str, Any]:
    saved_entry_ids: list[str] = []
    citation_count = 0
    for entry in build_character_index_entries(work, section, lines, source_url=source_url):
        saved = merge_character_index_entry(entry)
        entry_id = saved["bank_entry"]["id"]
        if entry_id not in saved_entry_ids:
            saved_entry_ids.append(entry_id)
        citation_count += int(saved["citation_delta"])

    return {
        "entry_count": len(saved_entry_ids),
        "citation_count": citation_count,
        "bank_entry_ids": saved_entry_ids,
    }


def _is_punctuation_char(char: str) -> bool:
    return char.isspace() or unicodedata.category(char).startswith("P")


def _matching_character_index_citations(
    entry: dict[str, Any],
    *,
    source_url: str | None,
    section: str,
    line_id: str,
) -> list[dict[str, Any]]:
    if entry.get("origin", {}).get("kind") != CHARACTER_INDEX_ORIGIN_KIND:
        return []

    matches: list[dict[str, Any]] = []
    for citation in entry.get("citations", []):
        if not isinstance(citation, dict):
            continue
        if citation.get("section") != section or citation.get("line_id") != line_id:
            continue
        citation_source_url = citation.get("source_url")
        if source_url is not None and citation_source_url not in {None, source_url}:
            continue
        matches.append(citation)
    return matches


def load_character_index_citations_for_line(
    *,
    source_url: str | None,
    section: str,
    line_id: str,
) -> list[dict[str, Any]]:
    bank_dir = flashcard_bank_dir()
    if not bank_dir.exists():
        return []

    matches: list[dict[str, Any]] = []
    for path in sorted(bank_dir.glob("*.json")):
        try:
            entry = load_bank_entry(path.stem)
        except ValueError:
            continue
        if entry is None:
            continue
        for citation in _matching_character_index_citations(
            entry,
            source_url=source_url,
            section=section,
            line_id=line_id,
        ):
            matches.append(
                {
                    "entry": entry,
                    "citation": citation,
                }
            )

    matches.sort(key=lambda item: int(item["citation"]["char_index"]))
    return matches


def reconstruct_line_from_character_index(
    *,
    source_url: str | None,
    section: str,
    line: dict[str, Any],
) -> dict[str, Any] | None:
    line_id = str(line.get("id", "")).strip()
    if not line_id:
        return None

    matches = load_character_index_citations_for_line(
        source_url=source_url,
        section=section,
        line_id=line_id,
    )
    if not matches:
        return None

    first_citation = matches[0]["citation"]
    simplified_text = str(first_citation.get("line_simplified", "")).strip()
    traditional_text = str(first_citation.get("line_traditional", "")).strip()
    zhuyin_text = str(first_citation.get("line_zhuyin", "")).strip()
    pinyin_text = str(first_citation.get("line_pinyin", "")).strip()
    translation_text = str(first_citation.get("line_translation_en", "")).strip()
    if not all((simplified_text, traditional_text, zhuyin_text, pinyin_text, translation_text)):
        return None

    expected_char_count = sum(0 if _is_punctuation_char(char) else 1 for char in simplified_text)
    by_char_index: dict[int, dict[str, Any]] = {}
    for match in matches:
        citation = match["citation"]
        char_index = int(citation["char_index"])
        if char_index in by_char_index:
            return None
        by_char_index[char_index] = match

    if len(by_char_index) != expected_char_count:
        return None

    character_glosses_en: list[str] = []
    for char_index in range(1, expected_char_count + 1):
        match = by_char_index.get(char_index)
        if match is None:
            return None
        citation = match["citation"]
        gloss_text = str(citation.get("char_gloss_en") or match["entry"]["layers"].get("gloss_en", "")).strip()
        if not gloss_text:
            return None
        character_glosses_en.append(gloss_text)

    return {
        **line,
        "annotation_source": "saved-character-index",
        "has_saved_character_index_annotation": True,
        "layers": {
            "traditional": traditional_text,
            "simplified": simplified_text,
            "zhuyin": zhuyin_text,
            "pinyin": pinyin_text,
            "gloss_en": "; ".join(character_glosses_en),
            "translation_en": translation_text,
        },
        "character_glosses_en": character_glosses_en,
    }


def save_bank_entry(bank_entry: dict) -> dict:
    bank_entry_to_save = dict(bank_entry)
    if "significance_flag_count" not in bank_entry_to_save:
        existing_entry_id = bank_entry_to_save.get("id")
        if isinstance(existing_entry_id, str) and existing_entry_id.strip():
            existing_entry = load_bank_entry(existing_entry_id)
            if existing_entry is not None and "significance_flag_count" in existing_entry:
                bank_entry_to_save["significance_flag_count"] = existing_entry["significance_flag_count"]

    normalized_entry = _validate_bank_entry(bank_entry_to_save)
    entry_path = flashcard_bank_dir() / f"{normalized_entry['id']}.json"
    _write_json_file(entry_path, normalized_entry)
    return {
        "bank_entry": normalized_entry,
        "bank_entry_path": str(entry_path),
    }


def increment_significance_flag_count(bank_entry_id: str, increment: int = 1) -> dict[str, Any]:
    normalized_bank_entry_id = _require_non_empty_string({"bank_entry_id": bank_entry_id}, "bank_entry_id")
    if not isinstance(increment, int) or increment < 1:
        raise ValueError("Flashcard significance flag increment must be a positive integer.")

    existing = load_bank_entry(normalized_bank_entry_id)
    if existing is None:
        raise ValueError(f"Flashcard bank entry {normalized_bank_entry_id!r} was not found.")

    updated = dict(existing)
    updated["significance_flag_count"] = int(existing.get("significance_flag_count", 0)) + increment
    saved = save_bank_entry(updated)
    return {
        "bank_entry": saved["bank_entry"],
        "bank_entry_path": saved["bank_entry_path"],
        "significance_flag_increment": increment,
        "significance_flag_count": saved["bank_entry"]["significance_flag_count"],
    }


def save_variations(bank_entry_id: str, variations: list[dict]) -> dict:
    _require_non_empty_string({"bank_entry_id": bank_entry_id}, "bank_entry_id")
    if not isinstance(variations, list):
        raise ValueError("Flashcard variations payload must be a list.")

    normalized_variations = [_normalize_variation(bank_entry_id, variation) for variation in variations]
    variations_path = flashcard_variations_dir() / f"{bank_entry_id}.json"
    _write_json_file(
        variations_path,
        {
            "bank_entry_id": bank_entry_id,
            "saved_at": int(time.time()),
            "variations": normalized_variations,
        },
    )
    return {
        "bank_entry_id": bank_entry_id,
        "variation_count": len(normalized_variations),
        "variations_path": str(variations_path),
    }


def save_flashcard_artifacts(
    *,
    bank_entry: dict | None = None,
    bank_entry_id: str | None = None,
    variations: list[dict] | None = None,
    significance_flag_increment: int | None = None,
) -> dict:
    if bank_entry is None and bank_entry_id is None:
        raise ValueError("Provide either a flashcard bank_entry or a bank_entry_id.")
    if bank_entry is None and variations is None and significance_flag_increment is None:
        raise ValueError(
            "Provide a flashcard bank_entry, flashcard variations, or a significance flag increment to save."
        )

    result: dict[str, object] = {}
    resolved_bank_entry_id = bank_entry_id.strip() if isinstance(bank_entry_id, str) else bank_entry_id
    if resolved_bank_entry_id is not None:
        result["bank_entry_id"] = resolved_bank_entry_id

    if bank_entry is not None:
        saved_entry = save_bank_entry(bank_entry)
        result.update(saved_entry)
        resolved_bank_entry_id = saved_entry["bank_entry"]["id"]

    if significance_flag_increment is not None:
        if resolved_bank_entry_id is None:
            raise ValueError("Incrementing flashcard significance requires a bank_entry or bank_entry_id.")
        saved_significance = increment_significance_flag_count(
            resolved_bank_entry_id,
            significance_flag_increment,
        )
        result.update(saved_significance)

    if variations is not None:
        if resolved_bank_entry_id is None:
            raise ValueError("Saving flashcard variations requires a bank_entry or bank_entry_id.")
        saved_variations = save_variations(resolved_bank_entry_id, variations)
        result.update(saved_variations)

    return result
