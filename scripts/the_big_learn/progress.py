from __future__ import annotations

import json
import shutil
import time
import unicodedata
from pathlib import Path
from typing import Any

from .bundled_sources import BUNDLED_SOURCES
from .flashcards import save_character_index_entries
from .source_catalog import (
    build_source_reading_pass,
    load_saved_source_catalog,
    load_saved_source_chapter,
    save_source_chapter_generated_annotations,
)
from .updates import state_dir


PROGRESS_FILE_NAME = "reading-progress.json"
BROWSABLE_PROGRESS_DIRNAME = "reading"
VISIBLE_BROWSABLE_PROGRESS_DIRNAME = "The Big Learn Reading"
BROWSABLE_PROGRESS_README_FILE_NAME = "README.md"
BROWSABLE_PROGRESS_CATALOG_FILE_NAME = "catalog.json"
BROWSABLE_LEARNER_STYLE_FILE_NAME = "learner-style.json"
BOOK_PROGRESS_FILE_NAME = "book.json"
CHAPTER_PROGRESS_FILE_NAME = "progress.json"
TRANSLATION_LOG_FILE_NAME = "learner-translation-log.json"
RESPONSE_LOG_FILE_NAME = "learner-response-log.json"
LEARNER_STYLE_FIELD_CHOICES = {
    "prompt_explicitness": {"compact", "explicit"},
    "discussion_depth": {"brief", "standard"},
}
LEARNER_STYLE_ALLOWED_TOP_LEVEL_KEYS = {"global", "work", "works"}

BOOK_TITLES = {work: spec["title"] for work, spec in BUNDLED_SOURCES.items()}

CHAPTER_TITLES = {}

SUPPORTED_WORKS = list(BUNDLED_SOURCES.keys())
TRANSLATION_SAVED_TAG = "[translation saved]"
RESPONSE_SAVED_TAG = "[response saved]"
UNSAVED_TAG = "[unsaved]"

BROWSABLE_PROGRESS_README = """# Guided Reading Artifacts

This directory mirrors the canonical `reading-progress.json` state file into smaller files that are easier to browse in a file manager or editor.

Layout:
- `catalog.json`: saved-status overview across supported works
- `learner-style.json`: saved global and work-scoped learner preferences
- `<work>/book.json`: saved book-level summary and response artifacts
- `<work>/chapters/<chapter>/progress.json`: chapter metadata and saved-status summary
- `<work>/chapters/<chapter>/learner-translation-log.json`: saved line-by-line translations
- `<work>/chapters/<chapter>/learner-response-log.json`: saved line-by-line responses

`reading-progress.json` remains the machine-oriented source of truth for the CLI. This directory is a browsable mirror for humans.
"""


def progress_path() -> Path:
    return state_dir() / PROGRESS_FILE_NAME


def browsable_progress_dir() -> Path:
    return state_dir() / BROWSABLE_PROGRESS_DIRNAME


def visible_progress_dir() -> Path:
    return Path.home() / VISIBLE_BROWSABLE_PROGRESS_DIRNAME


def browsable_progress_readme_path() -> Path:
    return browsable_progress_dir() / BROWSABLE_PROGRESS_README_FILE_NAME


def browsable_progress_catalog_path() -> Path:
    return browsable_progress_dir() / BROWSABLE_PROGRESS_CATALOG_FILE_NAME


def learner_style_path() -> Path:
    return browsable_progress_dir() / BROWSABLE_LEARNER_STYLE_FILE_NAME


def work_progress_dir(work: str) -> Path:
    return browsable_progress_dir() / work


def work_chapters_dir(work: str) -> Path:
    return work_progress_dir(work) / "chapters"


def book_progress_path(work: str) -> Path:
    return work_progress_dir(work) / BOOK_PROGRESS_FILE_NAME


def chapter_progress_dir(work: str, section: str) -> Path:
    return work_chapters_dir(work) / section


def chapter_progress_file_path(work: str, section: str) -> Path:
    return chapter_progress_dir(work, section) / CHAPTER_PROGRESS_FILE_NAME


def chapter_translation_log_path(work: str, section: str) -> Path:
    return chapter_progress_dir(work, section) / TRANSLATION_LOG_FILE_NAME


def chapter_response_log_path(work: str, section: str) -> Path:
    return chapter_progress_dir(work, section) / RESPONSE_LOG_FILE_NAME


def _visible_progress_path(path: Path) -> Path:
    try:
        relative_path = path.relative_to(browsable_progress_dir())
    except ValueError:
        return visible_progress_dir()
    return visible_progress_dir() / relative_path


def progress_artifact_paths(work: str | None = None, section: str | None = None) -> dict[str, str]:
    paths = {
        "root": str(browsable_progress_dir()),
        "readme": str(browsable_progress_readme_path()),
        "catalog": str(browsable_progress_catalog_path()),
        "learner_style": str(learner_style_path()),
        "visible_root": str(visible_progress_dir()),
        "visible_readme": str(_visible_progress_path(browsable_progress_readme_path())),
        "visible_catalog": str(_visible_progress_path(browsable_progress_catalog_path())),
        "visible_learner_style": str(_visible_progress_path(learner_style_path())),
    }

    if isinstance(work, str) and work.strip():
        normalized_work = work.strip()
        paths.update(
            {
                "work_dir": str(work_progress_dir(normalized_work)),
                "book": str(book_progress_path(normalized_work)),
                "visible_work_dir": str(_visible_progress_path(work_progress_dir(normalized_work))),
                "visible_book": str(_visible_progress_path(book_progress_path(normalized_work))),
            }
        )

        if isinstance(section, str) and section.strip():
            normalized_section = section.strip()
            paths.update(
                {
                    "chapter_dir": str(chapter_progress_dir(normalized_work, normalized_section)),
                    "chapter": str(chapter_progress_file_path(normalized_work, normalized_section)),
                    "learner_translation_log": str(chapter_translation_log_path(normalized_work, normalized_section)),
                    "learner_response_log": str(chapter_response_log_path(normalized_work, normalized_section)),
                    "visible_chapter_dir": str(_visible_progress_path(chapter_progress_dir(normalized_work, normalized_section))),
                    "visible_chapter": str(_visible_progress_path(chapter_progress_file_path(normalized_work, normalized_section))),
                    "visible_learner_translation_log": str(
                        _visible_progress_path(chapter_translation_log_path(normalized_work, normalized_section))
                    ),
                    "visible_learner_response_log": str(
                        _visible_progress_path(chapter_response_log_path(normalized_work, normalized_section))
                    ),
                }
            )

    return paths


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _delete_file_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def load_progress() -> dict[str, Any]:
    payload = _read_json_file(progress_path())
    books = payload.get("books")
    result = {
        "books": books if isinstance(books, dict) else {},
    }
    learner_style = _sanitize_saved_learner_style(payload.get("learner_style"))
    if learner_style:
        result["learner_style"] = learner_style
    return result


def _book_title(work: str) -> str:
    return BOOK_TITLES.get(work, work.replace("-", " ").title())


def _chapter_title(work: str, section: str) -> str:
    return CHAPTER_TITLES.get((work, section), section.replace("-", " ").title())


def _normalize_work_id(work: Any) -> str:
    if not isinstance(work, str) or not work.strip():
        raise ValueError("Work id must be a non-empty string.")

    normalized_work = work.strip()
    if normalized_work not in BOOK_TITLES:
        raise ValueError(f"Unknown work {normalized_work!r}.")
    return normalized_work


def _count_chinese_characters(text: str) -> int:
    count = 0
    for char in text:
        if char.isspace() or unicodedata.category(char).startswith("P"):
            continue
        count += 1
    return count


def _bundled_source_chapter_catalog_for_work(work: str) -> list[dict[str, Any]]:
    spec = BUNDLED_SOURCES.get(work)
    if spec is None:
        return []

    catalog = load_saved_source_catalog(spec["source_url"])
    if catalog is None:
        return []

    chapters: list[dict[str, Any]] = []
    for chapter in catalog.get("chapters", []):
        if not isinstance(chapter, dict):
            continue
        chapters.append(
            {
                "id": str(chapter["id"]),
                "title": str(chapter.get("title") or _chapter_title(work, str(chapter["id"]))),
                "line_count": int(chapter.get("reading_unit_count", 0)),
                "character_count": int(chapter.get("character_count", 0)),
                "start_order": int(chapter.get("order", 0)),
                "end_order": int(chapter.get("order", 0)),
                "container_kind": "source-chapter",
                "source_url": spec["source_url"],
            }
        )

    return chapters


def chapter_catalog_for_work(work: str) -> list[dict[str, Any]]:
    return _bundled_source_chapter_catalog_for_work(work)


def _has_saved_text(payload: Any, key: str) -> bool:
    if not isinstance(payload, dict):
        return False
    value = payload.get(key)
    return isinstance(value, str) and bool(value.strip())


def _normalize_learner_translation_log_entries(
    payload: Any,
    *,
    default_saved_at: int,
) -> list[dict[str, Any]]:
    return _normalize_line_text_log_entries(
        payload,
        text_key="translation_en",
        default_saved_at=default_saved_at,
    )


def _normalize_learner_response_log_entries(
    payload: Any,
    *,
    default_saved_at: int,
) -> list[dict[str, Any]]:
    return _normalize_line_text_log_entries(
        payload,
        text_key="response_en",
        default_saved_at=default_saved_at,
    )


def _normalize_line_text_log_entries(
    payload: Any,
    *,
    text_key: str,
    default_saved_at: int,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []

    entries: list[dict[str, Any]] = []
    for raw_entry in payload:
        if not isinstance(raw_entry, dict):
            continue

        line_id = str(raw_entry.get("line_id") or "").strip()
        text = raw_entry.get(text_key)
        if not line_id or not isinstance(text, str):
            continue

        normalized_text = text.strip()
        if not normalized_text:
            continue

        raw_saved_at = raw_entry.get("saved_at")
        saved_at = int(raw_saved_at) if isinstance(raw_saved_at, int) else default_saved_at
        entries.append(
            {
                "line_id": line_id,
                text_key: normalized_text,
                "saved_at": saved_at,
            }
        )

    return entries


def _merge_learner_translation_log(
    chapter_entry: dict[str, Any],
    learner_translation_log: Any,
    *,
    default_saved_at: int,
) -> list[dict[str, Any]]:
    return _merge_line_text_log(
        chapter_entry,
        learner_translation_log,
        chapter_key="learner_translation_log",
        text_key="translation_en",
        default_saved_at=default_saved_at,
    )


def _merge_learner_response_log(
    chapter_entry: dict[str, Any],
    learner_response_log: Any,
    *,
    default_saved_at: int,
) -> list[dict[str, Any]]:
    return _merge_line_text_log(
        chapter_entry,
        learner_response_log,
        chapter_key="learner_response_log",
        text_key="response_en",
        default_saved_at=default_saved_at,
    )


def _merge_line_text_log(
    chapter_entry: dict[str, Any],
    incoming_log: Any,
    *,
    chapter_key: str,
    text_key: str,
    default_saved_at: int,
) -> list[dict[str, Any]]:
    normalizer = _normalize_learner_translation_log_entries
    if text_key == "response_en":
        normalizer = _normalize_learner_response_log_entries

    existing_entries = normalizer(chapter_entry.get(chapter_key), default_saved_at=default_saved_at)
    incoming_entries = normalizer(incoming_log, default_saved_at=default_saved_at)
    if not incoming_entries:
        return existing_entries

    merged_by_line_id: dict[str, dict[str, Any]] = {}
    seen_line_ids: list[str] = []
    for entry in [*existing_entries, *incoming_entries]:
        line_id = entry["line_id"]
        if line_id not in merged_by_line_id:
            seen_line_ids.append(line_id)
        merged_by_line_id[line_id] = entry

    chapter_line_ids = [
        str(line_id)
        for line_id in chapter_entry.get("line_ids", [])
        if isinstance(line_id, str) and str(line_id).strip()
    ]
    ordered_line_ids = [line_id for line_id in chapter_line_ids if line_id in merged_by_line_id]
    ordered_line_ids.extend(line_id for line_id in seen_line_ids if line_id not in ordered_line_ids)
    return [merged_by_line_id[line_id] for line_id in ordered_line_ids]


def _sanitize_saved_learner_style_scope(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    sanitized: dict[str, Any] = {}
    for field, allowed_values in LEARNER_STYLE_FIELD_CHOICES.items():
        value = payload.get(field)
        if not isinstance(value, str):
            continue
        normalized_value = value.strip().lower()
        if normalized_value in allowed_values:
            sanitized[field] = normalized_value

    updated_at = payload.get("updated_at")
    if isinstance(updated_at, int):
        sanitized["updated_at"] = updated_at
    return sanitized


def _sanitize_saved_learner_style(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    sanitized: dict[str, Any] = {}

    global_scope = _sanitize_saved_learner_style_scope(payload.get("global"))
    if global_scope:
        sanitized["global"] = global_scope

    works_payload = payload.get("works")
    if isinstance(works_payload, dict):
        works: dict[str, dict[str, Any]] = {}
        for work, scope in works_payload.items():
            if not isinstance(work, str) or work.strip() not in BOOK_TITLES:
                continue
            sanitized_scope = _sanitize_saved_learner_style_scope(scope)
            if sanitized_scope:
                works[work.strip()] = sanitized_scope
        if works:
            sanitized["works"] = works

    return sanitized


def _normalize_learner_style_scope(
    payload: Any,
    *,
    label: str,
    default_saved_at: int,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object.")

    unknown_fields = sorted(set(payload) - set(LEARNER_STYLE_FIELD_CHOICES))
    if unknown_fields:
        raise ValueError(f"{label} has unsupported fields: {', '.join(unknown_fields)}.")

    normalized: dict[str, Any] = {}
    for field, allowed_values in LEARNER_STYLE_FIELD_CHOICES.items():
        if field not in payload:
            continue

        value = payload[field]
        if not isinstance(value, str):
            raise ValueError(f"{label}.{field} must be a string.")

        normalized_value = value.strip().lower()
        if normalized_value not in allowed_values:
            allowed = ", ".join(sorted(allowed_values))
            raise ValueError(f"{label}.{field} must be one of: {allowed}.")
        normalized[field] = normalized_value

    if not normalized:
        raise ValueError(f"{label} must include at least one supported field.")

    normalized["updated_at"] = default_saved_at
    return normalized


def _normalize_learner_style_payload(
    payload: Any,
    *,
    work: str | None,
    default_saved_at: int,
) -> dict[str, Any] | None:
    if payload is None:
        return None

    if not isinstance(payload, dict):
        raise ValueError("learner_style must be a JSON object.")

    unknown_keys = sorted(set(payload) - LEARNER_STYLE_ALLOWED_TOP_LEVEL_KEYS)
    if unknown_keys:
        raise ValueError(f"learner_style has unsupported keys: {', '.join(unknown_keys)}.")

    normalized: dict[str, Any] = {}

    if "global" in payload:
        normalized["global"] = _normalize_learner_style_scope(
            payload["global"],
            label="learner_style.global",
            default_saved_at=default_saved_at,
        )

    if "work" in payload:
        if not isinstance(work, str) or not work.strip():
            raise ValueError("learner_style.work requires a current work.")
        normalized.setdefault("works", {})[work] = _normalize_learner_style_scope(
            payload["work"],
            label="learner_style.work",
            default_saved_at=default_saved_at,
        )

    if "works" in payload:
        works_payload = payload["works"]
        if not isinstance(works_payload, dict):
            raise ValueError("learner_style.works must be a JSON object keyed by work id.")

        normalized_works = normalized.setdefault("works", {})
        for raw_work, scope in works_payload.items():
            normalized_work = _normalize_work_id(raw_work)
            normalized_works[normalized_work] = _normalize_learner_style_scope(
                scope,
                label=f"learner_style.works.{normalized_work}",
                default_saved_at=default_saved_at,
            )

    if not normalized:
        raise ValueError("learner_style must include at least one of global, work, or works.")

    return normalized


def _merge_learner_style(
    progress: dict[str, Any],
    learner_style: Any,
    *,
    work: str | None,
    default_saved_at: int,
) -> dict[str, Any]:
    normalized = _normalize_learner_style_payload(
        learner_style,
        work=work,
        default_saved_at=default_saved_at,
    )
    existing = _sanitize_saved_learner_style(progress.get("learner_style"))
    if normalized is None:
        return existing

    merged = {
        "global": dict(existing.get("global", {})),
        "works": {key: dict(value) for key, value in existing.get("works", {}).items()},
    }

    if "global" in normalized:
        merged["global"].update(normalized["global"])

    for work_id, scope in normalized.get("works", {}).items():
        existing_scope = merged["works"].get(work_id, {})
        existing_scope.update(scope)
        merged["works"][work_id] = existing_scope

    if not merged["global"]:
        merged.pop("global")
    if not merged["works"]:
        merged.pop("works")

    progress["learner_style"] = merged
    return merged


def load_learner_style() -> dict[str, Any]:
    return _sanitize_saved_learner_style(load_progress().get("learner_style"))


def _resolved_learner_style_from_payload(
    learner_style: dict[str, Any] | None,
    work: str | None = None,
) -> dict[str, Any]:
    if not isinstance(learner_style, dict):
        return {}

    resolved = dict(learner_style.get("global", {}))
    if isinstance(work, str) and work.strip():
        work_scope = learner_style.get("works", {}).get(work.strip(), {})
        if isinstance(work_scope, dict):
            resolved.update(work_scope)
    return resolved


def resolved_learner_style(work: str | None = None) -> dict[str, Any]:
    return _resolved_learner_style_from_payload(load_learner_style(), work)


def chapter_status(chapter_progress: dict[str, Any] | None) -> dict[str, Any]:
    progress = chapter_progress if isinstance(chapter_progress, dict) else {}
    has_translation = _has_saved_line_log(progress, "learner_translation_log", "translation_en") or _has_saved_text(
        progress,
        "personal_translation_en",
    )
    has_response = _has_saved_line_log(progress, "learner_response_log", "response_en") or _has_saved_text(
        progress,
        "personal_response_en",
    )

    status_tags: list[str] = []
    if has_translation:
        status_tags.append(TRANSLATION_SAVED_TAG)
    if has_response:
        status_tags.append(RESPONSE_SAVED_TAG)
    if not status_tags:
        status_tags.append(UNSAVED_TAG)

    return {
        "has_personal_translation": has_translation,
        "has_personal_response": has_response,
        "status_tags": status_tags,
        "status_label": " ".join(status_tags),
    }


def book_status(book_progress: dict[str, Any] | None) -> dict[str, Any]:
    progress = book_progress if isinstance(book_progress, dict) else {}
    has_summary = _has_saved_text(progress, "personal_summary_en")
    has_response = _has_saved_text(progress, "personal_response_en")

    status_tags: list[str] = []
    if has_summary:
        status_tags.append("[summary saved]")
    if has_response:
        status_tags.append(RESPONSE_SAVED_TAG)
    if not status_tags:
        status_tags.append(UNSAVED_TAG)

    return {
        "has_personal_summary": has_summary,
        "has_book_personal_response": has_response,
        "book_status_tags": status_tags,
        "book_status_label": " ".join(status_tags),
    }


def _has_saved_line_log(progress: dict[str, Any], chapter_key: str, text_key: str) -> bool:
    payload = progress.get(chapter_key)
    if text_key == "translation_en":
        return bool(_normalize_learner_translation_log_entries(payload, default_saved_at=0))
    return bool(_normalize_learner_response_log_entries(payload, default_saved_at=0))


def _resolve_chapter_entry(work: str, selector: str) -> dict[str, Any]:
    normalized_work = _normalize_work_id(work)
    if not isinstance(selector, str):
        raise ValueError("Chapter selector must be a non-empty string.")

    normalized_selector = selector.strip()
    if not normalized_selector:
        raise ValueError("Chapter selector must be a non-empty string.")

    for chapter in chapter_catalog_for_work(normalized_work):
        if chapter["id"] == normalized_selector or chapter["title"] == normalized_selector:
            return chapter

    raise ValueError(f"Unknown chapter {selector!r} for work {normalized_work!r}")


def _line_ids_for_chapter_entry(chapter: dict[str, Any]) -> list[str]:
    line_ids = chapter.get("line_ids")
    if isinstance(line_ids, list):
        return [str(line_id) for line_id in line_ids]

    source_url = chapter.get("source_url")
    if not isinstance(source_url, str) or not source_url.strip():
        return []

    payload = load_saved_source_chapter(source_url, str(chapter["id"]))
    if payload is None:
        return []

    reading_units = payload.get("chapter", {}).get("reading_units")
    if not isinstance(reading_units, list):
        return []

    return [
        str(unit["id"])
        for unit in reading_units
        if isinstance(unit, dict) and isinstance(unit.get("id"), str) and str(unit.get("text", "")).strip()
    ]


def guided_reading_catalog() -> list[dict[str, Any]]:
    progress = load_progress()
    progress_books = progress.get("books", {})
    books: list[dict[str, Any]] = []

    for work in SUPPORTED_WORKS:
        chapters = chapter_catalog_for_work(work)
        saved_book = progress_books.get(work, {}) if isinstance(progress_books, dict) else {}
        saved_chapters = saved_book.get("chapters", {}) if isinstance(saved_book, dict) else {}

        chapter_entries: list[dict[str, Any]] = []
        translated_count = 0
        responded_count = 0

        for chapter in chapters:
            saved_chapter = saved_chapters.get(chapter["id"], {}) if isinstance(saved_chapters, dict) else {}
            status = chapter_status(saved_chapter)
            if status["has_personal_translation"]:
                translated_count += 1
            if status["has_personal_response"]:
                responded_count += 1

            chapter_entries.append(
                {
                    **chapter,
                    **status,
                }
            )

        status = book_status(saved_book)
        books.append(
            {
                "id": work,
                "title": _book_title(work),
                "chapter_count": len(chapter_entries),
                "translated_chapter_count": translated_count,
                "responded_chapter_count": responded_count,
                "chapters": chapter_entries,
                **status,
            }
        )

    return books


def _write_browsable_book_payload(work: str, book_entry: dict[str, Any]) -> None:
    chapters = book_entry.get("chapters")
    chapter_ids = []
    if isinstance(chapters, dict):
        chapter_ids = sorted(str(chapter_id) for chapter_id in chapters)

    payload = {
        "work": work,
        "book_title": str(book_entry.get("book_title") or _book_title(work)),
        "chapters_dir": str(work_chapters_dir(work)),
        "chapter_ids": chapter_ids,
        **book_status(book_entry),
    }

    for key in (
        "personal_summary_en",
        "personal_summary_saved_at",
        "personal_response_en",
        "personal_response_saved_at",
    ):
        if key in book_entry:
            payload[key] = book_entry[key]

    _write_json_file(book_progress_path(work), payload)


def _write_browsable_chapter_payload(work: str, chapter_id: str, chapter_entry: dict[str, Any]) -> None:
    payload = {
        "work": work,
        "book_title": _book_title(work),
        "chapter_id": chapter_id,
        "chapter_title": str(chapter_entry.get("chapter_title") or _chapter_title(work, chapter_id)),
        "line_ids": chapter_entry.get("line_ids", []),
        "line_count": chapter_entry.get("line_count", 0),
        "character_count": chapter_entry.get("character_count", 0),
        **chapter_status(chapter_entry),
    }

    for key in (
        "personal_translation_en",
        "personal_translation_saved_at",
        "personal_response_en",
        "personal_response_saved_at",
        "resolved_learner_style",
    ):
        if key in chapter_entry:
            payload[key] = chapter_entry[key]

    translation_log = _normalize_learner_translation_log_entries(
        chapter_entry.get("learner_translation_log"),
        default_saved_at=0,
    )
    translation_log_file = chapter_translation_log_path(work, chapter_id)
    if translation_log:
        _write_json_file(
            translation_log_file,
            {
                "work": work,
                "chapter_id": chapter_id,
                "entries": translation_log,
            },
        )
        payload["learner_translation_log_path"] = str(translation_log_file)
        payload["learner_translation_log_entry_count"] = len(translation_log)
    else:
        _delete_file_if_exists(translation_log_file)

    response_log = _normalize_learner_response_log_entries(
        chapter_entry.get("learner_response_log"),
        default_saved_at=0,
    )
    response_log_file = chapter_response_log_path(work, chapter_id)
    if response_log:
        _write_json_file(
            response_log_file,
            {
                "work": work,
                "chapter_id": chapter_id,
                "entries": response_log,
            },
        )
        payload["learner_response_log_path"] = str(response_log_file)
        payload["learner_response_log_entry_count"] = len(response_log)
    else:
        _delete_file_if_exists(response_log_file)

    _write_json_file(chapter_progress_file_path(work, chapter_id), payload)


def _write_browsable_progress_snapshot(progress: dict[str, Any]) -> None:
    _write_text_file(browsable_progress_readme_path(), BROWSABLE_PROGRESS_README)
    _write_json_file(
        browsable_progress_catalog_path(),
        {
            "books": guided_reading_catalog(),
        },
    )

    learner_style = _sanitize_saved_learner_style(progress.get("learner_style"))
    if learner_style:
        _write_json_file(learner_style_path(), learner_style)
    else:
        _delete_file_if_exists(learner_style_path())

    books = progress.get("books")
    if not isinstance(books, dict):
        return

    for work, raw_book_entry in books.items():
        if not isinstance(work, str) or work.strip() not in BOOK_TITLES:
            continue
        if not isinstance(raw_book_entry, dict):
            continue

        normalized_work = work.strip()
        _write_browsable_book_payload(normalized_work, raw_book_entry)

        chapters = raw_book_entry.get("chapters")
        if not isinstance(chapters, dict):
            continue

        for chapter_id, raw_chapter_entry in chapters.items():
            if not isinstance(chapter_id, str) or not chapter_id.strip():
                continue
            if not isinstance(raw_chapter_entry, dict):
                continue
            _write_browsable_chapter_payload(normalized_work, chapter_id.strip(), raw_chapter_entry)

    if visible_progress_dir().exists():
        shutil.rmtree(visible_progress_dir())
    shutil.copytree(browsable_progress_dir(), visible_progress_dir())


def save_chapter_progress(
    work: str,
    section: str,
    *,
    personal_translation_en: str | None = None,
    personal_response_en: str | None = None,
    learner_translation_log: list[dict[str, Any]] | None = None,
    learner_response_log: list[dict[str, Any]] | None = None,
    learner_style: dict[str, Any] | None = None,
    saved_at: int | None = None,
) -> dict[str, Any]:
    normalized_work = _normalize_work_id(work)
    chapter = _resolve_chapter_entry(normalized_work, section)
    progress = load_progress()
    books = progress.setdefault("books", {})
    book_entry = books.setdefault(
        normalized_work,
        {
            "book_title": _book_title(normalized_work),
            "chapters": {},
        },
    )
    chapters = book_entry.setdefault("chapters", {})
    chapter_id = str(chapter["id"])
    chapter_entry = chapters.setdefault(
        chapter_id,
        {
            "chapter_title": chapter["title"],
            "line_ids": _line_ids_for_chapter_entry(chapter),
            "line_count": chapter["line_count"],
            "character_count": chapter["character_count"],
        },
    )

    timestamp = int(time.time()) if saved_at is None else int(saved_at)
    merged_learner_style = _merge_learner_style(
        progress,
        learner_style,
        work=normalized_work,
        default_saved_at=timestamp,
    )

    if learner_translation_log is not None:
        merged_log = _merge_learner_translation_log(
            chapter_entry,
            learner_translation_log,
            default_saved_at=timestamp,
        )
        if merged_log:
            chapter_entry["learner_translation_log"] = merged_log
            chapter_entry.pop("personal_translation_en", None)
            chapter_entry.pop("personal_translation_saved_at", None)

    if learner_response_log is not None:
        merged_log = _merge_learner_response_log(
            chapter_entry,
            learner_response_log,
            default_saved_at=timestamp,
        )
        if merged_log:
            chapter_entry["learner_response_log"] = merged_log
            chapter_entry.pop("personal_response_en", None)
            chapter_entry.pop("personal_response_saved_at", None)

    if learner_translation_log is None and isinstance(personal_translation_en, str) and personal_translation_en.strip():
        chapter_entry["personal_translation_en"] = personal_translation_en.strip()
        chapter_entry["personal_translation_saved_at"] = timestamp

    if learner_response_log is None and isinstance(personal_response_en, str) and personal_response_en.strip():
        chapter_entry["personal_response_en"] = personal_response_en.strip()
        chapter_entry["personal_response_saved_at"] = timestamp

    if merged_learner_style:
        chapter_entry["resolved_learner_style"] = _resolved_learner_style_from_payload(
            merged_learner_style,
            normalized_work,
        )

    _write_json_file(progress_path(), progress)
    _write_browsable_progress_snapshot(progress)
    return chapter_entry


def save_book_progress(
    work: str,
    *,
    personal_summary_en: str | None = None,
    personal_response_en: str | None = None,
    saved_at: int | None = None,
) -> dict[str, Any]:
    normalized_work = _normalize_work_id(work)
    progress = load_progress()
    books = progress.setdefault("books", {})
    book_entry = books.setdefault(
        normalized_work,
        {
            "book_title": _book_title(normalized_work),
            "chapters": {},
        },
    )

    timestamp = int(time.time()) if saved_at is None else int(saved_at)
    if isinstance(personal_summary_en, str) and personal_summary_en.strip():
        book_entry["personal_summary_en"] = personal_summary_en.strip()
        book_entry["personal_summary_saved_at"] = timestamp

    if isinstance(personal_response_en, str) and personal_response_en.strip():
        book_entry["personal_response_en"] = personal_response_en.strip()
        book_entry["personal_response_saved_at"] = timestamp

    _write_json_file(progress_path(), progress)
    _write_browsable_progress_snapshot(progress)
    return book_entry


def save_learner_style(
    learner_style: dict[str, Any],
    *,
    work: str | None = None,
    saved_at: int | None = None,
) -> dict[str, Any]:
    normalized_work = None
    if isinstance(work, str) and work.strip():
        normalized_work = _normalize_work_id(work)

    progress = load_progress()
    timestamp = int(time.time()) if saved_at is None else int(saved_at)
    merged_learner_style = _merge_learner_style(
        progress,
        learner_style,
        work=normalized_work,
        default_saved_at=timestamp,
    )
    _write_json_file(progress_path(), progress)
    _write_browsable_progress_snapshot(progress)
    return merged_learner_style


def save_chapter_generated_annotations(
    work: str,
    section: str,
    generated_annotations: list[dict[str, Any]],
    *,
    saved_at: int | None = None,
) -> dict[str, Any]:
    normalized_work = _normalize_work_id(work)
    chapter = _resolve_chapter_entry(normalized_work, section)
    source_url = chapter.get("source_url")
    if not isinstance(source_url, str) or not source_url.strip():
        raise ValueError(
            f"Chapter {section!r} for work {normalized_work!r} is not source-backed and cannot store generated annotations."
        )

    saved = save_source_chapter_generated_annotations(
        source_url,
        str(chapter["id"]),
        generated_annotations,
        saved_at=saved_at,
    )
    reading_pass = build_source_reading_pass(source_url, str(chapter["id"]))
    lines_by_id = {
        str(line["id"]): line
        for line in reading_pass.get("lines", [])
        if isinstance(line, dict) and isinstance(line.get("id"), str)
    }
    indexed_lines = [lines_by_id[line_id] for line_id in saved.get("line_ids", []) if line_id in lines_by_id]
    if indexed_lines:
        character_index_result = save_character_index_entries(
            normalized_work,
            str(chapter["id"]),
            indexed_lines,
            source_url=source_url,
        )
        saved["saved_character_index_cards"] = character_index_result["entry_count"]
        saved["saved_character_index_citations"] = character_index_result["citation_count"]
        saved["character_index_bank_entry_ids"] = character_index_result["bank_entry_ids"]

    return saved
