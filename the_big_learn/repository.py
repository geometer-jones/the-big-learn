from __future__ import annotations

from functools import lru_cache
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from .data_paths import data_root
from .updates import state_dir


ROOT = data_root()
ANNOTATIONS_DIR = ROOT / "annotations"
FLASHCARD_POLICY_FILE = ROOT / "flashcards" / "templates" / "default-variation-policy.json"
DEFAULT_FIXTURE_FILE = ROOT / "evals" / "fixtures" / "da-xue-reading-session.json"
HTTP_USER_AGENT = "the-big-learn/0.1"
SOURCE_STORE_DIRNAME = "source-store"


class RepositoryError(ValueError):
    """Raised when repository-backed runtime data is invalid or missing."""


class _ContentParagraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._content_depth = 0
        self._paragraph_depth = 0
        self._buffer: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if tag == "div" and "mw-parser-output" in classes and self._content_depth == 0:
            self._content_depth = 1
            return

        if self._content_depth and tag == "div":
            self._content_depth += 1

        if self._content_depth and tag == "p":
            self._paragraph_depth += 1
            if self._paragraph_depth == 1:
                self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if self._content_depth and tag == "p" and self._paragraph_depth:
            self._paragraph_depth -= 1
            if self._paragraph_depth == 0:
                paragraph = "".join(self._buffer).strip()
                if paragraph:
                    self.paragraphs.append(paragraph)

        if self._content_depth and tag == "div":
            self._content_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._content_depth and self._paragraph_depth:
            self._buffer.append(data)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def annotation_spec_path_for_work(work: str) -> Path:
    if work == "da-xue":
        return ANNOTATIONS_DIR / "da-xue" / "starter.annotations.json"
    raise RepositoryError(f"Unsupported work: {work}")


def _source_url_for_variant(source_url: str, variant: str) -> str:
    parsed = urlsplit(source_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["variant"] = variant
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def source_store_dir() -> Path:
    return state_dir() / SOURCE_STORE_DIRNAME


def _variant_store_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _variant_store_path(source_url: str, variant: str) -> Path:
    return source_store_dir() / _variant_store_key(source_url) / f"{_variant_store_key(variant)}.html"


def _read_stored_variant_html(source_url: str, variant: str) -> str | None:
    path = _variant_store_path(source_url, variant)
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None


def _write_stored_variant_html(source_url: str, variant: str, html_text: str) -> None:
    if not html_text.strip():
        return

    path = _variant_store_path(source_url, variant)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html_text, encoding="utf-8")
    except OSError:
        return


def _download_variant_html(source_url: str, variant: str) -> str:
    url = _source_url_for_variant(source_url, variant)
    request = Request(url, headers={"User-Agent": HTTP_USER_AGENT})
    with urlopen(request, timeout=15) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


@lru_cache(maxsize=None)
def _fetch_variant_html(source_url: str, variant: str) -> str:
    stored_html = _read_stored_variant_html(source_url, variant)
    if stored_html is not None:
        return stored_html

    html_text = _download_variant_html(source_url, variant)
    _write_stored_variant_html(source_url, variant, html_text)
    return html_text


def _strip_irrelevant_whitespace(text: str) -> str:
    return "".join(text.replace("\xa0", " ").replace("\u200b", "").split())


def _extract_content_paragraphs(html_text: str) -> list[str]:
    parser = _ContentParagraphParser()
    parser.feed(html_text)
    return parser.paragraphs


def _extract_annotated_chunks(paragraph_text: str) -> list[str]:
    normalized = _strip_irrelevant_whitespace(paragraph_text)
    if not normalized:
        return []

    chunks: list[str] = []
    buffer: list[str] = []
    annotation_depth = 0

    for char in normalized:
        if char == "〈":
            if annotation_depth == 0:
                chunk = "".join(buffer).strip()
                if chunk:
                    chunks.append(chunk)
                buffer = []
            annotation_depth += 1
            continue

        if char == "〉":
            if annotation_depth == 0:
                raise RepositoryError("Encountered unmatched closing annotation marker while parsing source text.")
            annotation_depth -= 1
            continue

        if annotation_depth == 0:
            buffer.append(char)

    if annotation_depth:
        raise RepositoryError("Encountered unmatched opening annotation marker while parsing source text.")

    chunk = "".join(buffer).strip()
    if chunk:
        chunks.append(chunk)

    return chunks


@lru_cache(maxsize=None)
def _load_variant_paragraph_chunks(source_url: str, variant: str) -> tuple[tuple[str, ...], ...]:
    html_text = _fetch_variant_html(source_url, variant)
    paragraphs = _extract_content_paragraphs(html_text)
    return tuple(tuple(_extract_annotated_chunks(paragraph)) for paragraph in paragraphs)


def _line_text_from_lookup(spec: dict, line_spec: dict) -> tuple[str, str]:
    inline_layers = line_spec.get("layers", {})
    inline_traditional = inline_layers.get("traditional")
    inline_simplified = inline_layers.get("simplified")
    if inline_traditional is not None or inline_simplified is not None:
        if not isinstance(inline_traditional, str) or not inline_traditional.strip():
            raise RepositoryError(f"Inline traditional text is missing for {line_spec['id']}")
        if not isinstance(inline_simplified, str) or not inline_simplified.strip():
            raise RepositoryError(f"Inline simplified text is missing for {line_spec['id']}")
        if len(inline_traditional) != len(inline_simplified):
            raise RepositoryError(
                f"Inline traditional and simplified line lengths differ for {line_spec['id']}: "
                f"{len(inline_traditional)} != {len(inline_simplified)}"
            )
        return inline_traditional, inline_simplified

    provider = spec["lookup"]["provider"]
    if provider != "wikisource-html":
        raise RepositoryError(f"Unsupported annotation lookup provider: {provider}")

    source_url = spec["defaults"]["provenance"]["source_url"]
    traditional_variant = spec["lookup"]["traditional_variant"]
    simplified_variant = spec["lookup"]["simplified_variant"]
    locator = line_spec["source_locator"]
    paragraph_index = locator["paragraph_index"]
    chunk_index = locator["chunk_index"]

    try:
        traditional_chunks = _load_variant_paragraph_chunks(source_url, traditional_variant)
        simplified_chunks = _load_variant_paragraph_chunks(source_url, simplified_variant)
    except Exception as exc:  # pragma: no cover - exercised via calling code and live verification script.
        raise RepositoryError(f"Could not fetch source text for {spec['work']} from {source_url}: {exc}") from exc

    try:
        traditional = traditional_chunks[paragraph_index][chunk_index]
        simplified = simplified_chunks[paragraph_index][chunk_index]
    except IndexError as exc:
        raise RepositoryError(
            f"Source locator out of range for {line_spec['id']}: paragraph={paragraph_index} chunk={chunk_index}"
        ) from exc

    if len(traditional) != len(simplified):
        raise RepositoryError(
            f"Fetched traditional and simplified line lengths differ for {line_spec['id']}: "
            f"{len(traditional)} != {len(simplified)}"
        )

    return traditional, simplified


def _segment_text(text: str, start: int, end: int, *, line_id: str, segment_id: str, layer_name: str) -> str:
    if start < 0 or end <= start or end > len(text):
        raise RepositoryError(
            f"Invalid {layer_name} slice for {segment_id} in {line_id}: start={start} end={end} len={len(text)}"
        )
    return text[start:end]


def _hydrate_segment(line_spec: dict, segment_spec: dict, traditional: str, simplified: str) -> dict:
    inline_traditional = segment_spec.get("traditional")
    inline_simplified = segment_spec.get("simplified")
    if inline_traditional is not None or inline_simplified is not None:
        if not isinstance(inline_traditional, str) or not inline_traditional.strip():
            raise RepositoryError(f"Inline traditional text is missing for segment {segment_spec['id']}")
        if not isinstance(inline_simplified, str) or not inline_simplified.strip():
            raise RepositoryError(f"Inline simplified text is missing for segment {segment_spec['id']}")
        if len(inline_traditional) != len(inline_simplified):
            raise RepositoryError(
                f"Inline traditional and simplified segment lengths differ for {segment_spec['id']}: "
                f"{len(inline_traditional)} != {len(inline_simplified)}"
            )
        traditional_text = inline_traditional
        simplified_text = inline_simplified
    else:
        start = segment_spec["source_start"]
        end = segment_spec["source_end"]
        traditional_text = _segment_text(
            traditional,
            start,
            end,
            line_id=line_spec["id"],
            segment_id=segment_spec["id"],
            layer_name="traditional",
        )
        simplified_text = _segment_text(
            simplified,
            start,
            end,
            line_id=line_spec["id"],
            segment_id=segment_spec["id"],
            layer_name="simplified",
        )

    segment = {
        "id": segment_spec["id"],
        "traditional": traditional_text,
        "simplified": simplified_text,
        "zhuyin": segment_spec["zhuyin"],
        "pinyin": segment_spec["pinyin"],
        "gloss_en": segment_spec["gloss_en"],
    }

    if segment_spec.get("notes"):
        segment["notes"] = list(segment_spec["notes"])

    return segment


def _hydrate_line(spec: dict, line_spec: dict) -> dict:
    traditional, simplified = _line_text_from_lookup(spec, line_spec)
    defaults = spec["defaults"]

    line = {
        "id": line_spec["id"],
        "work": spec["work"],
        "source_variant": line_spec.get("source_variant", defaults["source_variant"]),
        "section": line_spec["section"],
        "order": line_spec["order"],
        "annotation_profile": line_spec.get("annotation_profile", defaults["annotation_profile"]),
        "layers": {
            "traditional": traditional,
            "simplified": simplified,
            "zhuyin": line_spec["layers"]["zhuyin"],
            "pinyin": line_spec["layers"]["pinyin"],
            "gloss_en": line_spec["layers"]["gloss_en"],
            "translation_en": line_spec["layers"]["translation_en"],
        },
        "provenance": dict(line_spec.get("provenance", defaults["provenance"])),
        "status": line_spec["status"],
    }

    if line_spec.get("segments"):
        line["segments"] = [
            _hydrate_segment(line_spec, segment_spec, traditional, simplified) for segment_spec in line_spec["segments"]
        ]

    if line_spec.get("keywords"):
        line["keywords"] = list(line_spec["keywords"])

    if line_spec.get("character_glosses_en"):
        line["character_glosses_en"] = list(line_spec["character_glosses_en"])

    if line_spec.get("notes"):
        line["notes"] = list(line_spec["notes"])

    return line


def load_lines(work: str) -> list[dict]:
    path = annotation_spec_path_for_work(work)
    spec = load_json(path)
    return [_hydrate_line(spec, line_spec) for line_spec in spec["lines"]]


def load_line_index(work: str) -> dict[str, dict]:
    return {line["id"]: line for line in load_lines(work)}


def select_lines_by_range(work: str, start: int | None = None, end: int | None = None) -> list[dict]:
    lines = load_lines(work)
    selected = []
    for line in lines:
        order = line["order"]
        if start is not None and order < start:
            continue
        if end is not None and order > end:
            continue
        selected.append(line)
    if not selected:
        raise RepositoryError(f"No lines found for work={work!r} range={start!r}:{end!r}")
    return selected


def select_lines_by_ids(work: str, line_ids: list[str]) -> list[dict]:
    index = load_line_index(work)
    missing = [line_id for line_id in line_ids if line_id not in index]
    if missing:
        raise RepositoryError(f"Unknown line ids for {work}: {missing}")
    return [index[line_id] for line_id in line_ids]


def find_segment(line: dict, segment_id: str | None = None) -> dict | None:
    if not segment_id:
        return None
    for segment in line.get("segments", []):
        if segment["id"] == segment_id:
            return segment
    raise RepositoryError(f"Unknown segment id {segment_id} for line {line['id']}")


def load_flashcard_policy() -> dict:
    return load_json(FLASHCARD_POLICY_FILE)


def load_fixture(path: str | None = None) -> dict:
    fixture_path = Path(path) if path else DEFAULT_FIXTURE_FILE
    return load_json(fixture_path)
