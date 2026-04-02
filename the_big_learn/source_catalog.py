from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .bundled_sources import BUNDLED_SOURCE_URL_TO_WORK_ID
from .data_paths import data_root
from .flashcards import reconstruct_line_from_character_index
from .repository import HTTP_USER_AGENT
from .updates import state_dir


SOURCE_STORE_DIRNAME = "source-store"
HTML_CACHE_FILE = "source.html"
CATALOG_CACHE_FILE = "catalog.json"
CHAPTERS_DIRNAME = "chapters"
COMMENTARY_DIRNAME = "commentary"
SOURCE_CHAPTER_SCHEMA_VERSION = 2
READING_UNIT_MAX_CHARS = 120
GENERATED_ANNOTATION_DEFAULT_STATUS = "generated"
GENERATED_ANNOTATION_LAYER_KEYS = (
    "traditional",
    "simplified",
    "zhuyin",
    "pinyin",
    "gloss_en",
    "translation_en",
)

CHAPTER_MARKER_RE = re.compile(
    r"(?P<title>右(?:經一章|傳之(?:首|[一二三四五六七八九十百]+)章|第[一二三四五六七八九十百]+章))"
)
TITLE_TAG_RE = re.compile(r"<title[^>]*>(?P<title>.*?)</title>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
CTEXT_ROW_RE = re.compile(r'<tr id="n\d+".*?</tr>', re.IGNORECASE | re.DOTALL)
CTEXT_CELL_RE = re.compile(r"<td\b(?P<attrs>[^>]*)>(?P<content>.*?)</td>", re.IGNORECASE | re.DOTALL)
CTEXT_ORIGINAL_RE = re.compile(
    r'<span\b[^>]*class="[^"]*\boriginal\b[^"]*"[^>]*>(?P<content>.*?)</span>',
    re.IGNORECASE | re.DOTALL,
)
CTEXT_POPUP_RE = re.compile(r'class="[^"]*\bpopup\b[^"]*"', re.IGNORECASE)
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[。！？?!；;])")
CLAUSE_BOUNDARY_RE = re.compile(r"(?<=[，、：,:])")


class SourceCatalogError(ValueError):
    """Raised when an external source cannot be cataloged safely."""


class _WikisourceBlockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._content_depth = 0
        self._block_depth = 0
        self._buffer: list[str] = []
        self._current_tag = ""
        self.blocks: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if tag == "div" and "mw-parser-output" in classes and self._content_depth == 0:
            self._content_depth = 1
            return

        if self._content_depth and tag == "div":
            self._content_depth += 1

        if self._content_depth and tag in {"p", "dd"}:
            self._block_depth += 1
            if self._block_depth == 1:
                self._buffer = []
                self._current_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if self._content_depth and tag in {"p", "dd"} and self._block_depth:
            self._block_depth -= 1
            if self._block_depth == 0:
                block = _normalize_whitespace("".join(self._buffer))
                if block:
                    self.blocks.append({"tag": self._current_tag or "p", "text": block})
                self._current_tag = ""

        if self._content_depth and tag == "div":
            self._content_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._content_depth and self._block_depth:
            self._buffer.append(data)


def _source_store_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source_store_dirname(source_url: str) -> str:
    return BUNDLED_SOURCE_URL_TO_WORK_ID.get(source_url, _source_store_key(source_url))


def source_cache_dir(source_url: str) -> Path:
    return state_dir() / SOURCE_STORE_DIRNAME / _source_store_dirname(source_url)


def packaged_source_cache_dir(source_url: str) -> Path:
    return data_root() / SOURCE_STORE_DIRNAME / _source_store_dirname(source_url)


def _legacy_source_cache_dir(source_url: str) -> Path | None:
    legacy_dir = state_dir() / SOURCE_STORE_DIRNAME / _source_store_key(source_url)
    return legacy_dir if legacy_dir != source_cache_dir(source_url) else None


def _legacy_packaged_source_cache_dir(source_url: str) -> Path | None:
    legacy_dir = data_root() / SOURCE_STORE_DIRNAME / _source_store_key(source_url)
    return legacy_dir if legacy_dir != packaged_source_cache_dir(source_url) else None


def source_html_path(source_url: str) -> Path:
    return source_cache_dir(source_url) / HTML_CACHE_FILE


def packaged_source_html_path(source_url: str) -> Path:
    return packaged_source_cache_dir(source_url) / HTML_CACHE_FILE


def source_catalog_path(source_url: str) -> Path:
    return source_cache_dir(source_url) / CATALOG_CACHE_FILE


def packaged_source_catalog_path(source_url: str) -> Path:
    return packaged_source_cache_dir(source_url) / CATALOG_CACHE_FILE


def source_chapter_path(source_url: str, chapter_id: str) -> Path:
    return source_cache_dir(source_url) / CHAPTERS_DIRNAME / f"{chapter_id}.json"


def packaged_source_chapter_path(source_url: str, chapter_id: str) -> Path:
    return packaged_source_cache_dir(source_url) / CHAPTERS_DIRNAME / f"{chapter_id}.json"


def _legacy_source_html_path(source_url: str) -> Path | None:
    legacy_dir = _legacy_source_cache_dir(source_url)
    if legacy_dir is None:
        return None
    return legacy_dir / HTML_CACHE_FILE


def _legacy_packaged_source_html_path(source_url: str) -> Path | None:
    legacy_dir = _legacy_packaged_source_cache_dir(source_url)
    if legacy_dir is None:
        return None
    return legacy_dir / HTML_CACHE_FILE


def _legacy_source_catalog_path(source_url: str) -> Path | None:
    legacy_dir = _legacy_source_cache_dir(source_url)
    if legacy_dir is None:
        return None
    return legacy_dir / CATALOG_CACHE_FILE


def _legacy_packaged_source_catalog_path(source_url: str) -> Path | None:
    legacy_dir = _legacy_packaged_source_cache_dir(source_url)
    if legacy_dir is None:
        return None
    return legacy_dir / CATALOG_CACHE_FILE


def _legacy_source_chapter_path(source_url: str, chapter_id: str) -> Path | None:
    legacy_dir = _legacy_source_cache_dir(source_url)
    if legacy_dir is None:
        return None
    return legacy_dir / CHAPTERS_DIRNAME / f"{chapter_id}.json"


def _legacy_packaged_source_chapter_path(source_url: str, chapter_id: str) -> Path | None:
    legacy_dir = _legacy_packaged_source_cache_dir(source_url)
    if legacy_dir is None:
        return None
    return legacy_dir / CHAPTERS_DIRNAME / f"{chapter_id}.json"


def detect_source_provider(source_url: str) -> str:
    hostname = urlsplit(source_url).netloc.lower()
    if hostname.endswith("wikisource.org"):
        return "wikisource-html"
    if hostname == "ctext.org" or hostname.endswith(".ctext.org"):
        return "ctext-html"
    raise SourceCatalogError(f"Unsupported source host for URL: {source_url}")


def _read_json_file(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate_cached_paths(*paths: Path | None) -> list[Path]:
    seen: set[Path] = set()
    candidates: list[Path] = []
    for path in paths:
        if path is None:
            continue
        if path in seen:
            continue
        seen.add(path)
        candidates.append(path)
    return candidates


def _read_first_json_file(*paths: Path) -> tuple[Path, dict[str, Any]] | tuple[None, None]:
    for path in _candidate_cached_paths(*paths):
        payload = _read_json_file(path)
        if payload is not None:
            return path, payload
    return None, None


def _read_cached_html(source_url: str) -> str | None:
    for path in _candidate_cached_paths(
        source_html_path(source_url),
        _legacy_source_html_path(source_url),
        packaged_source_html_path(source_url),
        _legacy_packaged_source_html_path(source_url),
    ):
        try:
            return path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            continue
    return None


def _write_cached_html(source_url: str, html_text: str) -> None:
    if not html_text.strip():
        return
    path = source_html_path(source_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def _download_source_html(source_url: str) -> str:
    request = Request(source_url, headers={"User-Agent": HTTP_USER_AGENT})
    with urlopen(request, timeout=15) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _fetch_source_html(source_url: str, *, refresh: bool = False) -> str:
    if not refresh:
        cached = _read_cached_html(source_url)
        if cached is not None:
            return cached

    html_text = _download_source_html(source_url)
    _write_cached_html(source_url, html_text)
    return html_text


def _strip_tags(html_fragment: str) -> str:
    with_breaks = re.sub(r"<br\s*/?>", "\n", html_fragment, flags=re.IGNORECASE)
    return unescape(TAG_RE.sub("", with_breaks))


def _normalize_whitespace(text: str) -> str:
    compacted = re.sub(r"[ \t\r\f\v]+", " ", text)
    compacted = re.sub(r"\n\s*", "\n", compacted)
    return compacted.strip()


def _count_characters(text: str) -> int:
    count = 0
    for char in text:
        if char.isspace() or unicodedata.category(char).startswith("P"):
            continue
        count += 1
    return count


def _source_title_from_html(html_text: str) -> str:
    match = TITLE_TAG_RE.search(html_text)
    if not match:
        return "Untitled source"
    title = _normalize_whitespace(_strip_tags(match.group("title")))
    title = title.removesuffix(" - Chinese Text Project")
    title = title.removesuffix(" - 維基文庫，自由的圖書館")
    return title or "Untitled source"


def _normalized_catalog_payload(source_url: str, payload: dict[str, Any], catalog_file: Path) -> dict[str, Any]:
    cache_dir = catalog_file.parent
    normalized_chapters: list[dict[str, Any]] = []
    for index, chapter in enumerate(payload.get("chapters", []), start=1):
        if not isinstance(chapter, dict):
            continue

        normalized_chapter = _normalized_source_chapter(chapter, index=index)

        normalized_chapters.append(
            {
                "id": normalized_chapter["id"],
                "order": normalized_chapter["order"],
                "title": normalized_chapter["title"],
                "summary": normalized_chapter["summary"],
                "character_count": normalized_chapter["character_count"],
                "reading_unit_count": int(chapter.get("reading_unit_count", normalized_chapter["reading_unit_count"])),
                "supplemental_unit_count": int(
                    chapter.get("supplemental_unit_count", normalized_chapter["supplemental_unit_count"])
                ),
                "chapter_path": str(cache_dir / CHAPTERS_DIRNAME / f"{normalized_chapter['id']}.json"),
            }
        )

    normalized_payload = {
        **payload,
        "source_url": source_url,
        "cache_dir": str(cache_dir),
        "catalog_path": str(catalog_file),
        "chapters": normalized_chapters,
    }

    commentary_entries = payload.get("commentary_chapters", [])
    if isinstance(commentary_entries, list):
        normalized_commentary_chapters: list[dict[str, Any]] = []
        for index, commentary in enumerate(commentary_entries, start=1):
            if not isinstance(commentary, dict):
                continue

            normalized_commentary = _normalized_source_chapter(commentary, index=index)
            normalized_commentary_chapters.append(
                {
                    "id": normalized_commentary["id"],
                    "order": normalized_commentary["order"],
                    "title": normalized_commentary["title"],
                    "summary": normalized_commentary["summary"],
                    "character_count": normalized_commentary["character_count"],
                    "reading_unit_count": int(
                        commentary.get("reading_unit_count", normalized_commentary["reading_unit_count"])
                    ),
                    "supplemental_unit_count": int(
                        commentary.get("supplemental_unit_count", normalized_commentary["supplemental_unit_count"])
                    ),
                    "commentary_path": str(cache_dir / COMMENTARY_DIRNAME / f"{normalized_commentary['id']}.json"),
                }
            )

        normalized_payload["commentary_chapters"] = normalized_commentary_chapters
        normalized_payload["commentary_chapter_count"] = int(
            payload.get("commentary_chapter_count", len(normalized_commentary_chapters))
        )

    return normalized_payload


def _normalized_chapter_payload(source_url: str, payload: dict[str, Any], chapter_file: Path) -> dict[str, Any]:
    raw_chapter = payload.get("chapter", {})
    chapter_index = int(raw_chapter.get("order", 1)) if isinstance(raw_chapter, dict) else 1
    return {
        **payload,
        "schema_version": SOURCE_CHAPTER_SCHEMA_VERSION,
        "source_url": source_url,
        "chapter": _normalized_source_chapter(raw_chapter if isinstance(raw_chapter, dict) else {}, index=chapter_index),
        "chapter_path": str(chapter_file),
    }


def _normalized_commentary_payload(source_url: str, payload: dict[str, Any], commentary_file: Path) -> dict[str, Any]:
    raw_commentary = payload.get("commentary", {})
    commentary_index = int(raw_commentary.get("order", 1)) if isinstance(raw_commentary, dict) else 1
    return {
        **payload,
        "schema_version": SOURCE_CHAPTER_SCHEMA_VERSION,
        "source_url": source_url,
        "commentary": _normalized_source_chapter(
            raw_commentary if isinstance(raw_commentary, dict) else {},
            index=commentary_index,
        ),
        "commentary_path": str(commentary_file),
    }


def _split_with_boundaries(text: str, pattern: re.Pattern[str]) -> list[str]:
    return [part.strip() for part in pattern.split(text) if part.strip()]


def _split_fixed_width(text: str, *, max_chars: int) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    return [stripped[index:index + max_chars].strip() for index in range(0, len(stripped), max_chars) if stripped[index:index + max_chars].strip()]


def _combine_fragments(fragments: list[str], *, max_chars: int) -> list[str]:
    units: list[str] = []
    buffer = ""

    for fragment in fragments:
        piece = fragment.strip()
        if not piece:
            continue
        if not buffer:
            buffer = piece
            continue
        if len(buffer) + len(piece) <= max_chars:
            buffer += piece
            continue
        units.append(buffer)
        buffer = piece

    if buffer:
        units.append(buffer)

    return units


def _split_long_fragment(fragment: str, *, max_chars: int) -> list[str]:
    piece = fragment.strip()
    if not piece:
        return []
    if len(piece) <= max_chars:
        return [piece]

    clause_fragments = _split_with_boundaries(piece, CLAUSE_BOUNDARY_RE)
    if clause_fragments and len(clause_fragments) > 1:
        units: list[str] = []
        buffer = ""
        for clause in clause_fragments:
            if len(clause) > max_chars:
                if buffer:
                    units.append(buffer)
                    buffer = ""
                units.extend(_split_fixed_width(clause, max_chars=max_chars))
                continue
            if not buffer:
                buffer = clause
                continue
            if len(buffer) + len(clause) <= max_chars:
                buffer += clause
                continue
            units.append(buffer)
            buffer = clause
        if buffer:
            units.append(buffer)
        return units

    return _split_fixed_width(piece, max_chars=max_chars)


def _unit_entries_from_text(
    chapter_id: str,
    text: str,
    *,
    id_label: str,
) -> list[dict[str, Any]]:
    raw_blocks = [_normalize_whitespace(block) for block in text.splitlines()]
    blocks = [block for block in raw_blocks if block]

    if not blocks and text.strip():
        blocks = [_normalize_whitespace(text)]

    units: list[dict[str, Any]] = []
    order = 1
    for source_block_order, block in enumerate(blocks, start=1):
        sentence_fragments = _split_with_boundaries(block, SENTENCE_BOUNDARY_RE) or [block]
        unit_fragments: list[str] = []
        for fragment in sentence_fragments:
            unit_fragments.extend(_split_long_fragment(fragment, max_chars=READING_UNIT_MAX_CHARS))

        for source_block_chunk, unit_text in enumerate(_combine_fragments(unit_fragments, max_chars=READING_UNIT_MAX_CHARS), start=1):
            units.append(
                {
                    "id": f"{chapter_id}-{id_label}-{order:03d}",
                    "order": order,
                    "text": unit_text,
                    "character_count": _count_characters(unit_text),
                    "source_block_order": source_block_order,
                    "source_block_chunk": source_block_chunk,
                }
            )
            order += 1

    return units


def _normalized_string_list(raw_values: Any) -> list[str]:
    if raw_values is None:
        return []
    if not isinstance(raw_values, list):
        raise ValueError("Expected a JSON list of strings.")
    normalized: list[str] = []
    for value in raw_values:
        text = str(value).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalized_generated_segments(raw_segments: Any, *, line_id: str) -> list[dict[str, Any]]:
    if raw_segments is None:
        return []
    if not isinstance(raw_segments, list):
        raise ValueError(f"Generated segments for {line_id} must be a list.")

    normalized_segments: list[dict[str, Any]] = []
    for index, segment in enumerate(raw_segments, start=1):
        if not isinstance(segment, dict):
            raise ValueError(f"Generated segment {index} for {line_id} must be a JSON object.")

        segment_id = str(segment.get("id", f"{line_id}-generated-segment-{index:03d}")).strip()
        if not segment_id:
            segment_id = f"{line_id}-generated-segment-{index:03d}"

        normalized_segment: dict[str, Any] = {"id": segment_id}
        for key in ("traditional", "simplified", "zhuyin", "pinyin", "gloss_en"):
            value = segment.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                normalized_segment[key] = text

        notes = _normalized_string_list(segment.get("notes"))
        if notes:
            normalized_segment["notes"] = notes

        if len(normalized_segment) == 1:
            raise ValueError(f"Generated segment {segment_id} for {line_id} is empty.")

        normalized_segments.append(normalized_segment)

    return normalized_segments


def _normalized_generated_annotation(
    raw_annotation: Any,
    *,
    line_id: str,
    saved_at: int | None = None,
) -> dict[str, Any]:
    if not isinstance(raw_annotation, dict):
        raise ValueError(f"Generated annotation for {line_id} must be a JSON object.")

    normalized: dict[str, Any] = {}

    raw_layers = raw_annotation.get("layers")
    if raw_layers is not None:
        if not isinstance(raw_layers, dict):
            raise ValueError(f"Generated annotation layers for {line_id} must be a JSON object.")

        normalized_layers = {}
        for key in GENERATED_ANNOTATION_LAYER_KEYS:
            value = raw_layers.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                normalized_layers[key] = text
        if normalized_layers:
            normalized["layers"] = normalized_layers

    segments = _normalized_generated_segments(raw_annotation.get("segments"), line_id=line_id)
    if segments:
        normalized["segments"] = segments

    character_glosses = _normalized_string_list(raw_annotation.get("character_glosses_en"))
    if character_glosses:
        normalized["character_glosses_en"] = character_glosses

    notes = _normalized_string_list(raw_annotation.get("notes"))
    if notes:
        normalized["notes"] = notes

    status = str(raw_annotation.get("status", GENERATED_ANNOTATION_DEFAULT_STATUS)).strip()
    if status:
        normalized["status"] = status

    for key in ("annotation_profile", "generated_by", "model"):
        value = raw_annotation.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            normalized[key] = text

    raw_saved_at = raw_annotation.get("saved_at", saved_at)
    if raw_saved_at is not None:
        normalized["saved_at"] = int(raw_saved_at)

    if not any(
        key in normalized
        for key in ("layers", "segments", "character_glosses_en", "notes")
    ):
        raise ValueError(
            f"Generated annotation for {line_id} must include at least one of layers, segments, "
            "character_glosses_en, or notes."
        )

    return normalized


def _normalized_units(
    raw_units: Any,
    *,
    chapter_id: str,
    id_label: str,
    fallback_text: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if isinstance(raw_units, list):
        for index, unit in enumerate(raw_units, start=1):
            if not isinstance(unit, dict):
                continue
            text = _normalize_whitespace(str(unit.get("text", "")))
            if not text:
                continue
            unit_id = str(unit.get("id", f"{chapter_id}-{id_label}-{index:03d}")).strip()
            if not unit_id:
                unit_id = f"{chapter_id}-{id_label}-{index:03d}"
            preserved_keys = {
                key: value
                for key, value in unit.items()
                if key
                not in {
                    "id",
                    "order",
                    "text",
                    "character_count",
                    "source_block_order",
                    "source_block_chunk",
                }
            }
            if "generated_annotation" in preserved_keys:
                preserved_keys["generated_annotation"] = _normalized_generated_annotation(
                    preserved_keys["generated_annotation"],
                    line_id=unit_id,
                )
            normalized.append(
                {
                    **preserved_keys,
                    "id": unit_id,
                    "order": int(unit.get("order", index)),
                    "text": text,
                    "character_count": int(unit.get("character_count", _count_characters(text))),
                    "source_block_order": int(unit.get("source_block_order", index)),
                    "source_block_chunk": int(unit.get("source_block_chunk", 1)),
                }
            )
    if normalized:
        return normalized
    return _unit_entries_from_text(chapter_id, fallback_text, id_label=id_label)


def _normalized_source_chapter(chapter: dict[str, Any], *, index: int) -> dict[str, Any]:
    chapter_id = str(chapter.get("id", "")).strip() or f"chapter-{index:03d}"
    text = str(chapter.get("text", "")).strip()
    supplemental_text = str(chapter.get("supplemental_text", "")).strip()
    reading_units = _normalized_units(
        chapter.get("reading_units"),
        chapter_id=chapter_id,
        id_label="line",
        fallback_text=text,
    )
    supplemental_units = _normalized_units(
        chapter.get("supplemental_units"),
        chapter_id=chapter_id,
        id_label="supp",
        fallback_text=supplemental_text,
    )
    preserved_keys = {
        key: value
        for key, value in chapter.items()
        if key
        not in {
            "id",
            "order",
            "title",
            "summary",
            "character_count",
            "text",
            "supplemental_text",
            "reading_units",
            "reading_unit_count",
            "supplemental_units",
            "supplemental_unit_count",
        }
    }
    return {
        **preserved_keys,
        "id": chapter_id,
        "order": int(chapter.get("order", index)),
        "title": str(chapter.get("title", "")).strip(),
        "summary": str(chapter.get("summary", "")).strip(),
        "character_count": int(chapter.get("character_count", _count_characters(text))),
        "text": text,
        "supplemental_text": supplemental_text,
        "reading_unit_count": len(reading_units),
        "reading_units": reading_units,
        "supplemental_unit_count": len(supplemental_units),
        "supplemental_units": supplemental_units,
    }


def _extract_ctext_blocks(html_text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for row_html in CTEXT_ROW_RE.findall(html_text):
        has_popup_line = CTEXT_POPUP_RE.search(row_html) is not None
        for cell_match in CTEXT_CELL_RE.finditer(row_html):
            attrs = cell_match.group("attrs")
            class_match = re.search(r'class="(?P<class>[^"]+)"', attrs, re.IGNORECASE)
            if class_match is None:
                continue

            classes = set(class_match.group("class").split())
            if "ctext" not in classes or "opt" in classes:
                continue

            content = cell_match.group("content")
            cleaned = _normalize_whitespace(_strip_tags(content))
            if cleaned:
                original_segments = [
                    segment
                    for match in CTEXT_ORIGINAL_RE.finditer(content)
                    if (segment := _normalize_whitespace(_strip_tags(match.group("content"))))
                ]
                commentary_only = _normalize_whitespace(_strip_tags(CTEXT_ORIGINAL_RE.sub("", content)))
                if has_popup_line:
                    reading_texts = original_segments or [cleaned]
                    supplemental_texts = [commentary_only] if commentary_only else []
                else:
                    reading_texts = []
                    supplemental_texts = [cleaned]

                blocks.append(
                    {
                        "text": cleaned,
                        "reading_texts": reading_texts,
                        "supplemental_texts": supplemental_texts,
                        "postfixed_heading": has_popup_line,
                    }
                )
            break
    return blocks


def _extract_wikisource_blocks(html_text: str) -> list[dict[str, Any]]:
    parser = _WikisourceBlockParser()
    parser.feed(html_text)
    blocks: list[dict[str, Any]] = []
    for block in parser.blocks:
        text = block["text"]
        tag = block["tag"]
        blocks.append(
            {
                "text": text,
                "reading_texts": [text] if tag == "p" else [],
                "supplemental_texts": [text] if tag == "dd" else [],
                "postfixed_heading": False,
            }
        )
    return blocks


def _chapter_heading(text: str) -> tuple[str, str] | None:
    match = CHAPTER_MARKER_RE.search(text)
    if not match:
        return None

    title = match.group("title").rstrip("。")
    remainder = text[match.end():].lstrip("。:： \n")
    if remainder:
        summary = remainder.split("。", 1)[0].strip()
    else:
        summary = ""
    return title, summary


def _finalize_chapter(current: dict[str, Any]) -> dict[str, Any]:
    text = "\n".join(block for block in current["reading_blocks"] if block).strip()
    supplemental_text = "\n".join(block for block in current["supplemental_blocks"] if block).strip()
    return {
        "id": current["id"],
        "order": current["order"],
        "title": current["title"],
        "summary": current["summary"],
        "character_count": _count_characters(text),
        "text": text,
        "supplemental_text": supplemental_text,
    }


def _catalog_from_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapters: list[dict[str, Any]] = []
    current_heading: dict[str, Any] | None = None
    pending_reading_blocks: list[str] = []
    pending_supplemental_blocks: list[str] = []
    pending_postfixed_heading = False

    for block in blocks:
        block_text = str(block["text"])
        heading = _chapter_heading(block_text)
        if heading is not None:
            if pending_reading_blocks:
                chapter_number = len(chapters) + 1
                if current_heading is not None:
                    chapters.append(
                        _finalize_chapter(
                            {
                                "id": f"chapter-{chapter_number:03d}",
                                "order": chapter_number,
                                "title": current_heading["title"],
                                "summary": current_heading["summary"],
                                "reading_blocks": list(pending_reading_blocks),
                                "supplemental_blocks": [
                                    *current_heading["supplemental_blocks"],
                                    *pending_supplemental_blocks,
                                ],
                            }
                        )
                    )
                    current_heading = {
                        "title": heading[0],
                        "summary": heading[1],
                        "supplemental_blocks": [block_text],
                    }
                elif pending_postfixed_heading:
                    chapters.append(
                        _finalize_chapter(
                            {
                                "id": f"chapter-{chapter_number:03d}",
                                "order": chapter_number,
                                "title": heading[0],
                                "summary": heading[1],
                                "reading_blocks": list(pending_reading_blocks),
                                "supplemental_blocks": [*pending_supplemental_blocks, block_text],
                            }
                        )
                    )
                else:
                    current_heading = {
                        "title": heading[0],
                        "summary": heading[1],
                        "supplemental_blocks": [
                            *pending_supplemental_blocks,
                            *pending_reading_blocks,
                            block_text,
                        ],
                    }
                pending_reading_blocks = []
                pending_supplemental_blocks = []
                pending_postfixed_heading = False
            else:
                current_heading = {
                    "title": heading[0],
                    "summary": heading[1],
                    "supplemental_blocks": [*pending_supplemental_blocks, block_text],
                }
                pending_supplemental_blocks = []
                pending_postfixed_heading = False
            continue

        pending_reading_blocks.extend(str(item) for item in block.get("reading_texts", []) if str(item).strip())
        pending_supplemental_blocks.extend(
            str(item) for item in block.get("supplemental_texts", []) if str(item).strip()
        )
        pending_postfixed_heading = pending_postfixed_heading or bool(block.get("postfixed_heading"))

    if current_heading is not None and pending_reading_blocks:
        chapter_number = len(chapters) + 1
        chapters.append(
            _finalize_chapter(
                {
                    "id": f"chapter-{chapter_number:03d}",
                    "order": chapter_number,
                    "title": current_heading["title"],
                    "summary": current_heading["summary"],
                    "reading_blocks": list(pending_reading_blocks),
                    "supplemental_blocks": [
                        *current_heading["supplemental_blocks"],
                        *pending_supplemental_blocks,
                    ],
                }
            )
        )

    return chapters


def _build_catalog_from_html(source_url: str, html_text: str) -> dict[str, Any]:
    provider = detect_source_provider(source_url)
    if provider == "wikisource-html":
        blocks = _extract_wikisource_blocks(html_text)
    elif provider == "ctext-html":
        blocks = _extract_ctext_blocks(html_text)
    else:  # pragma: no cover
        raise SourceCatalogError(f"Unsupported provider: {provider}")

    chapters = _catalog_from_blocks(blocks)

    return {
        "provider": provider,
        "source_url": source_url,
        "title": _source_title_from_html(html_text),
        "chapter_count": len(chapters),
        "chapters": chapters,
        "cache_dir": str(source_cache_dir(source_url)),
        "catalog_path": str(source_catalog_path(source_url)),
    }


def load_saved_source_catalog(source_url: str) -> dict[str, Any] | None:
    catalog_file, payload = _read_first_json_file(
        source_catalog_path(source_url),
        _legacy_source_catalog_path(source_url),
        packaged_source_catalog_path(source_url),
        _legacy_packaged_source_catalog_path(source_url),
    )
    if catalog_file is None or payload is None:
        return None
    normalized = _normalized_catalog_payload(source_url, payload, catalog_file)
    if catalog_file == source_catalog_path(source_url) and normalized != payload:
        _write_json_file(catalog_file, normalized)
    return normalized


def _build_full_source_catalog(source_url: str, *, refresh: bool = False) -> dict[str, Any]:
    html_text = _fetch_source_html(source_url, refresh=refresh)
    return _build_catalog_from_html(source_url, html_text)


def build_source_catalog(source_url: str, *, refresh: bool = False) -> dict[str, Any]:
    if not refresh:
        cached = load_saved_source_catalog(source_url)
        if cached is not None:
            return cached

    full_catalog = _build_full_source_catalog(source_url, refresh=refresh)
    catalog = _normalized_catalog_payload(source_url, full_catalog, source_catalog_path(source_url))
    _write_json_file(source_catalog_path(source_url), catalog)
    return catalog


def load_saved_source_chapter(source_url: str, chapter_id: str) -> dict[str, Any] | None:
    chapter_file, payload = _read_first_json_file(
        source_chapter_path(source_url, chapter_id),
        _legacy_source_chapter_path(source_url, chapter_id),
        packaged_source_chapter_path(source_url, chapter_id),
        _legacy_packaged_source_chapter_path(source_url, chapter_id),
    )
    if chapter_file is None or payload is None:
        return None
    normalized = _normalized_chapter_payload(source_url, payload, chapter_file)
    if chapter_file == source_chapter_path(source_url, chapter_id) and normalized != payload:
        _write_json_file(chapter_file, normalized)
    return normalized


def _resolve_chapter(chapters: list[dict[str, Any]], selector: str | int) -> dict[str, Any]:
    normalized = str(selector).strip()
    if not normalized:
        raise SourceCatalogError("Chapter selector is required.")

    if normalized.isdigit():
        chapter_number = int(normalized)
        for chapter in chapters:
            if int(chapter["order"]) == chapter_number:
                return chapter

    for chapter in chapters:
        if chapter["id"] == normalized:
            return chapter
        if chapter["title"] == normalized:
            return chapter

    raise SourceCatalogError(f"Unknown chapter selector: {selector!r}")


def download_source_chapter(source_url: str, selector: str | int, *, refresh: bool = False) -> dict[str, Any]:
    catalog = build_source_catalog(source_url, refresh=refresh)
    if not catalog["chapters"]:
        raise SourceCatalogError(
            f"No detectable chapters were found for {source_url}. Choose a source page with chapter markers."
        )

    chapter = _resolve_chapter(catalog["chapters"], selector)
    if not refresh:
        cached = load_saved_source_chapter(source_url, chapter["id"])
        if cached is not None:
            return cached

    full_catalog = _build_full_source_catalog(source_url, refresh=refresh)
    full_chapter = _resolve_chapter(full_catalog["chapters"], chapter["id"])
    chapter_file = source_chapter_path(source_url, chapter["id"])
    payload = _normalized_chapter_payload(
        source_url,
        {
            "provider": full_catalog["provider"],
            "source_url": source_url,
            "source_title": full_catalog["title"],
            "chapter": full_chapter,
            "chapter_path": str(chapter_file),
        },
        chapter_file,
    )

    _write_json_file(chapter_file, payload)
    return payload


def _reading_lines_from_chapter_text(chapter_id: str, text: str) -> list[dict[str, Any]]:
    return _unit_entries_from_text(chapter_id, text, id_label="line")


def _reading_lines_from_chapter(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    units = chapter.get("reading_units")
    if isinstance(units, list) and units:
        return [
            _line_from_reading_unit(
                {
                **{
                    key: value
                    for key, value in unit.items()
                    if key
                    not in {
                        "id",
                        "order",
                        "text",
                        "character_count",
                        "source_block_order",
                        "source_block_chunk",
                    }
                },
                "id": str(unit["id"]),
                "order": int(unit["order"]),
                "text": str(unit["text"]),
                "character_count": int(unit["character_count"]),
                **(
                    {"source_block_order": int(unit["source_block_order"])}
                    if "source_block_order" in unit
                    else {}
                ),
                **(
                    {"source_block_chunk": int(unit["source_block_chunk"])}
                    if "source_block_chunk" in unit
                    else {}
                ),
                }
            )
            for unit in units
            if isinstance(unit, dict) and str(unit.get("text", "")).strip()
        ]
    return _reading_lines_from_chapter_text(str(chapter.get("id", "chapter-001")), str(chapter.get("text", "")))


def _line_from_reading_unit(unit: dict[str, Any]) -> dict[str, Any]:
    line = dict(unit)
    annotation = line.get("generated_annotation")
    if not isinstance(annotation, dict):
        return line

    line["annotation_source"] = "saved-generated"
    line["has_saved_generated_annotation"] = True

    raw_layers = annotation.get("layers")
    if isinstance(raw_layers, dict):
        layers: dict[str, str] = {}
        traditional = str(raw_layers.get("traditional", line["text"])).strip()
        simplified = str(raw_layers.get("simplified", line["text"])).strip()
        if traditional:
            layers["traditional"] = traditional
        if simplified:
            layers["simplified"] = simplified

        for key in ("zhuyin", "pinyin", "gloss_en", "translation_en"):
            value = raw_layers.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                layers[key] = text

        if layers:
            line["layers"] = layers

    segments = annotation.get("segments")
    if isinstance(segments, list) and segments:
        line["segments"] = segments

    character_glosses_en = annotation.get("character_glosses_en")
    if isinstance(character_glosses_en, list) and character_glosses_en:
        line["character_glosses_en"] = character_glosses_en

    notes = annotation.get("notes")
    if isinstance(notes, list) and notes:
        line["notes"] = notes

    for key in ("status", "annotation_profile", "generated_by", "model", "saved_at"):
        value = annotation.get(key)
        if value is None:
            continue
        line[f"generated_annotation_{key}"] = value

    return line


def _annotate_chapter_line_positions(chapter: dict[str, Any], lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    line_count = len(lines)
    annotated_lines: list[dict[str, Any]] = []

    for index, line in enumerate(lines, start=1):
        annotated_lines.append(
            {
                **line,
                "container_id": str(chapter.get("id", "")),
                "container_title": str(chapter.get("title", "")),
                "container_kind": "chapter",
                "line_index_in_container": index,
                "container_line_count": line_count,
            }
        )

    return annotated_lines


def build_source_reading_pass(source_url: str, selector: str | int, *, refresh: bool = False) -> dict[str, Any]:
    payload = download_source_chapter(source_url, selector, refresh=refresh)
    chapter = payload["chapter"]
    lines = _annotate_chapter_line_positions(chapter, _reading_lines_from_chapter(chapter))
    reconstructed_lines: list[dict[str, Any]] = []
    for line in lines:
        if line.get("has_saved_generated_annotation"):
            reconstructed_lines.append(line)
            continue
        reconstructed = reconstruct_line_from_character_index(
            source_url=source_url,
            section=str(chapter.get("id", "")),
            line=line,
        )
        reconstructed_lines.append(reconstructed or line)
    lines = reconstructed_lines
    saved_annotation_count = sum(1 for line in lines if line.get("has_saved_generated_annotation"))
    saved_character_index_count = sum(1 for line in lines if line.get("has_saved_character_index_annotation"))
    return {
        "mode": "raw-source",
        "provider": payload["provider"],
        "source_url": payload["source_url"],
        "source_title": payload["source_title"],
        "chapter": chapter,
        "chapter_path": payload["chapter_path"],
        "line_count": len(lines),
        "saved_annotation_count": saved_annotation_count,
        "saved_character_index_count": saved_character_index_count,
        "lines": lines,
    }


def save_source_chapter_generated_annotations(
    source_url: str,
    chapter_id: str,
    generated_annotations: list[dict[str, Any]],
    *,
    saved_at: int | None = None,
) -> dict[str, Any]:
    if not isinstance(generated_annotations, list):
        raise ValueError("generated_annotations must be a JSON list.")

    payload = load_saved_source_chapter(source_url, chapter_id)
    if payload is None:
        payload = download_source_chapter(source_url, chapter_id)

    timestamp = int(time.time()) if saved_at is None else int(saved_at)
    annotations_by_line_id: dict[str, dict[str, Any]] = {}
    for index, annotation in enumerate(generated_annotations, start=1):
        if not isinstance(annotation, dict):
            raise ValueError(f"Generated annotation {index} must be a JSON object.")
        line_id = str(annotation.get("line_id", "")).strip()
        if not line_id:
            raise ValueError(f"Generated annotation {index} is missing line_id.")
        if line_id in annotations_by_line_id:
            raise ValueError(f"Duplicate generated annotation line_id: {line_id}")

        raw_annotation = annotation.get("generated_annotation")
        if raw_annotation is None:
            raw_annotation = {
                key: value
                for key, value in annotation.items()
                if key != "line_id"
            }

        annotations_by_line_id[line_id] = _normalized_generated_annotation(
            raw_annotation,
            line_id=line_id,
            saved_at=timestamp,
        )

    chapter = dict(payload["chapter"])
    units = [
        dict(unit)
        for unit in _normalized_units(
            chapter.get("reading_units"),
            chapter_id=str(chapter.get("id", chapter_id)),
            id_label="line",
            fallback_text=str(chapter.get("text", "")),
        )
    ]

    saved_line_ids: list[str] = []
    for unit in units:
        line_id = str(unit["id"])
        annotation = annotations_by_line_id.pop(line_id, None)
        if annotation is None:
            continue
        unit["generated_annotation"] = annotation
        saved_line_ids.append(line_id)

    if annotations_by_line_id:
        unknown_line_ids = ", ".join(sorted(annotations_by_line_id))
        raise ValueError(f"Unknown reading unit ids for chapter {chapter_id}: {unknown_line_ids}")

    chapter["reading_units"] = units
    chapter["reading_unit_count"] = len(units)
    payload["chapter"] = chapter
    chapter_file = source_chapter_path(source_url, str(chapter.get("id", chapter_id)))
    payload["chapter_path"] = str(chapter_file)
    _write_json_file(chapter_file, payload)

    return {
        "source_url": source_url,
        "chapter_id": str(chapter.get("id", chapter_id)),
        "chapter_path": str(chapter_file),
        "saved_annotation_count": len(saved_line_ids),
        "line_ids": saved_line_ids,
    }
