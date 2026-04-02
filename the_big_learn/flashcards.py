from __future__ import annotations

import json
from pathlib import Path
import time
import unicodedata

from .display import canonical_layer_name, format_hanzi_layers, format_layer_value
from .updates import state_dir


FLASHCARD_DIRNAME = "flashcards"
FLASHCARD_BANK_DIRNAME = "bank"
FLASHCARD_VARIATIONS_DIRNAME = "variations"

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


def _slugify_pinyin(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    words = [word for word in stripped.lower().replace("'", "").split() if word]
    return "-".join(words)


def _normalize_variation_text(text: str) -> str:
    return " ".join(text.split())


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
    }


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
        key: _require_non_empty_string(layers, key)
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


def save_bank_entry(bank_entry: dict) -> dict:
    normalized_entry = _validate_bank_entry(bank_entry)
    entry_path = flashcard_bank_dir() / f"{normalized_entry['id']}.json"
    _write_json_file(entry_path, normalized_entry)
    return {
        "bank_entry": normalized_entry,
        "bank_entry_path": str(entry_path),
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
) -> dict:
    if bank_entry is None and bank_entry_id is None:
        raise ValueError("Provide either a flashcard bank_entry or a bank_entry_id.")
    if bank_entry is None and variations is None:
        raise ValueError("Provide a flashcard bank_entry or flashcard variations to save.")

    result: dict[str, object] = {}
    resolved_bank_entry_id = bank_entry_id.strip() if isinstance(bank_entry_id, str) else bank_entry_id
    if resolved_bank_entry_id is not None:
        result["bank_entry_id"] = resolved_bank_entry_id

    if bank_entry is not None:
        saved_entry = save_bank_entry(bank_entry)
        result.update(saved_entry)
        resolved_bank_entry_id = saved_entry["bank_entry"]["id"]

    if variations is not None:
        if resolved_bank_entry_id is None:
            raise ValueError("Saving flashcard variations requires a bank_entry or bank_entry_id.")
        saved_variations = save_variations(resolved_bank_entry_id, variations)
        result.update(saved_variations)

    return result
