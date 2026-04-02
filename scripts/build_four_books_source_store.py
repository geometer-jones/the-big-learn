from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from the_big_learn.bundled_sources import BUNDLED_SOURCES
from the_big_learn.source_catalog import (
    CATALOG_CACHE_FILE,
    CHAPTERS_DIRNAME,
    COMMENTARY_DIRNAME,
    CTEXT_CELL_RE,
    CTEXT_ROW_RE,
    _build_catalog_from_html,
    _count_characters,
    _extract_ctext_blocks,
    _extract_wikisource_blocks,
    _normalize_whitespace,
    _normalized_catalog_payload,
    _normalized_chapter_payload,
    _normalized_commentary_payload,
    _read_json_file,
    _source_store_dirname,
    _source_title_from_html,
    _strip_tags,
    _write_json_file,
)


ROOT = Path(__file__).resolve().parent.parent
SOURCE_STORE_DIR = ROOT / "source-store"
HTTP_USER_AGENT = "the-big-learn/0.1"
FETCH_DELAY_SECONDS = 0.25
MAX_FETCH_ATTEMPTS = 5
RETRYABLE_HTTP_CODES = {403, 429, 500, 502, 503, 504}
ANCHOR_LINK_RE = re.compile(
    r'<a\b[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE,
)
TRANSLATION_TITLE_RE = re.compile(
    r'<span\b[^>]*class="[^"]*\btranslationtitle\b[^"]*"[^>]*>.*?</span>',
    re.IGNORECASE | re.DOTALL,
)
CLASS_ATTR_RE = re.compile(r'class="(?P<class>[^"]+)"', re.IGNORECASE)
LUNYU_TITLE_RE = re.compile(r"^[\u4e00-\u9fff]+第[一二三四五六七八九十]+$")
MENGZI_TITLE_RE = re.compile(r"^[\u4e00-\u9fff]+章句[上下]$")
SUNZI_TITLE_RE = re.compile(r"^[\u4e00-\u9fff]+$")
SANGUO_WIKISOURCE_LINK_RE = re.compile(
    r'<li>\s*<a href="(?P<href>[^"]+)"[^>]*title="三國演義/第(?P<number>\d{3})回"[^>]*>(?P<label>第[^<]+回)</a>(?P<tail>.*?)</li>',
    re.IGNORECASE | re.DOTALL,
)
DA_XUE_CORE_CHAPTER_SPECS = (
    {"title": "大學之道", "summary": "在明明德，在親民，在止於至善"},
    {"title": "知止而后有定", "summary": "定而后能靜，靜而后能安，安而后能慮，慮而后能得"},
    {"title": "物有本末", "summary": "事有終始，知所先後，則近道矣"},
    {"title": "古之欲明明德於天下者", "summary": "先治其國；欲治其國者，先齊其家"},
    {"title": "物格而后知至", "summary": "知至而后意誠，意誠而后心正"},
    {"title": "自天子以至於庶人", "summary": "壹是皆以脩身為本"},
    {"title": "其本亂而末治者否矣", "summary": "其所厚者薄，而其所薄者厚，未之有也"},
)
DA_XUE_COMMENTARY_INTRO_TITLE = "朱熹序與總說"
DA_XUE_COMMENTARY_INTRO_SUMMARY = "《大學章句》序與經一章總說"
DA_XUE_CORE_TEXT_NOTE = (
    "Core reading is the Da Xue classic extracted from the former bundled chapter-001. "
    "Zhu Xi's preface, the chapter-001 commentary block, and the ten 傳 commentary chapters are stored "
    "separately under commentary_chapters and should not be presented as the learner's main chapter menu."
)


def _fetch_html(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
        request = Request(url, headers={"User-Agent": HTTP_USER_AGENT, "Referer": "https://ctext.org/"})
        try:
            with urlopen(request, timeout=30) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                html_text = response.read().decode(charset, errors="replace")
            time.sleep(FETCH_DELAY_SECONDS)
            return html_text
        except HTTPError as error:
            last_error = error
            if error.code not in RETRYABLE_HTTP_CODES or attempt == MAX_FETCH_ATTEMPTS:
                raise
        except URLError as error:
            last_error = error
            if attempt == MAX_FETCH_ATTEMPTS:
                raise
        time.sleep(attempt)

    if last_error is not None:  # pragma: no cover
        raise RuntimeError(f"Failed to fetch {url}") from last_error
    raise RuntimeError(f"Failed to fetch {url}")  # pragma: no cover


def _store_dir_for_url(source_url: str) -> Path:
    return SOURCE_STORE_DIR / _source_store_dirname(source_url)


def _chapter_payload(provider: str, source_url: str, source_title: str, chapter: dict) -> dict:
    relative_store_dir = Path("source-store") / _source_store_dirname(source_url)
    relative_chapter_file = relative_store_dir / CHAPTERS_DIRNAME / f"{chapter['id']}.json"
    return _normalized_chapter_payload(
        source_url,
        {
            "provider": provider,
            "source_url": source_url,
            "source_title": source_title,
            "chapter": chapter,
            "chapter_path": str(relative_chapter_file),
        },
        relative_chapter_file,
    )


def _commentary_payload(provider: str, source_url: str, source_title: str, commentary: dict) -> dict:
    relative_store_dir = Path("source-store") / _source_store_dirname(source_url)
    relative_commentary_file = relative_store_dir / COMMENTARY_DIRNAME / f"{commentary['id']}.json"
    return _normalized_commentary_payload(
        source_url,
        {
            "provider": provider,
            "source_url": source_url,
            "source_title": source_title,
            "commentary": commentary,
            "commentary_path": str(relative_commentary_file),
        },
        relative_commentary_file,
    )


def _chapter_record(
    *,
    order: int,
    title: str,
    text: str,
    summary: str = "",
    supplemental_text: str = "",
) -> dict:
    return {
        "id": f"chapter-{order:03d}",
        "order": order,
        "title": title,
        "summary": summary,
        "character_count": _count_characters(text),
        "text": text,
        "supplemental_text": supplemental_text,
    }


def _catalog_record(*, source_url: str, source_title: str, provider: str, chapters: list[dict]) -> dict:
    return {
        "provider": provider,
        "source_url": source_url,
        "title": source_title,
        "chapter_count": len(chapters),
        "chapters": chapters,
        "cache_dir": "",
        "catalog_path": "",
    }


def _write_catalog_and_chapters(source_url: str, catalog: dict) -> None:
    store_dir = _store_dir_for_url(source_url)
    if store_dir.exists():
        shutil.rmtree(store_dir)
    (store_dir / CHAPTERS_DIRNAME).mkdir(parents=True, exist_ok=True)
    if catalog.get("commentary_chapters"):
        (store_dir / COMMENTARY_DIRNAME).mkdir(parents=True, exist_ok=True)

    relative_store_dir = Path("source-store") / _source_store_dirname(source_url)
    bundled_catalog = _normalized_catalog_payload(source_url, catalog, relative_store_dir / CATALOG_CACHE_FILE)
    _write_json_file(store_dir / CATALOG_CACHE_FILE, bundled_catalog)

    for chapter in catalog["chapters"]:
        _write_json_file(
            store_dir / CHAPTERS_DIRNAME / f"{chapter['id']}.json",
            _chapter_payload(catalog["provider"], source_url, catalog["title"], chapter),
        )

    for commentary in catalog.get("commentary_chapters", []):
        _write_json_file(
            store_dir / COMMENTARY_DIRNAME / f"{commentary['id']}.json",
            _commentary_payload(catalog["provider"], source_url, catalog["title"], commentary),
        )


def _extract_chapter_links(
    index_html: str,
    *,
    href_prefix: str,
    title_pattern: re.Pattern[str] | None = None,
) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    seen_hrefs: set[str] = set()
    for match in ANCHOR_LINK_RE.finditer(index_html):
        href = match.group("href").strip()
        title_html = TRANSLATION_TITLE_RE.sub("", match.group("title"))
        title = _normalize_whitespace(_strip_tags(title_html))
        if not href.startswith(href_prefix):
            continue
        if href.endswith("/ens") or href.endswith("/zh"):
            continue
        if title_pattern is not None and not title_pattern.fullmatch(title):
            continue
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        links.append((title, href))
    return links


def _extract_plain_ctext_rows(html_text: str) -> list[str]:
    rows: list[str] = []
    for row_html in CTEXT_ROW_RE.findall(html_text):
        for cell_match in CTEXT_CELL_RE.finditer(row_html):
            attrs = cell_match.group("attrs")
            class_match = CLASS_ATTR_RE.search(attrs)
            if class_match is None:
                continue

            classes = set(class_match.group("class").split())
            if "ctext" not in classes or "opt" in classes:
                continue

            cleaned = _normalize_whitespace(_strip_tags(cell_match.group("content")))
            if cleaned:
                rows.append(cleaned)
            break
    return rows


def _reading_texts_from_blocks(blocks: list[dict]) -> tuple[str, str]:
    reading_blocks = [str(text) for block in blocks for text in block.get("reading_texts", []) if str(text).strip()]
    supplemental_blocks = [
        str(text) for block in blocks for text in block.get("supplemental_texts", []) if str(text).strip()
    ]
    return "\n".join(reading_blocks).strip(), "\n".join(supplemental_blocks).strip()


def _summary_from_text(text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        return candidate.split("。", 1)[0].strip()
    return ""


def _joined_wikisource_text(blocks: list[dict]) -> str:
    lines = []
    for block in blocks:
        text = str(block.get("text", "")).strip()
        if not text:
            continue
        if text.startswith("此作品在全世界都属于公有领域") or text.startswith("Public domain"):
            continue
        lines.append(text)
    return "\n".join(lines).strip()


def _harvest_indexed_book(source_url: str, *, title_pattern: re.Pattern[str]) -> dict:
    index_html = _fetch_html(source_url)
    chapters: list[dict] = []

    for order, (title, href) in enumerate(
        _extract_chapter_links(index_html, href_prefix="si-shu-zhang-ju-ji-zhu/", title_pattern=title_pattern),
        start=1,
    ):
        chapter_url = urljoin("https://ctext.org/", href)
        if "?" not in chapter_url:
            chapter_url = f"{chapter_url}?if=en"
        chapter_html = _fetch_html(chapter_url)
        text, supplemental_text = _reading_texts_from_blocks(_extract_ctext_blocks(chapter_html))
        if not text:
            continue

        chapters.append(
            {
                "id": f"chapter-{order:03d}",
                "order": order,
                "title": title,
                "summary": "",
                "character_count": _count_characters(text),
                "text": text,
                "supplemental_text": supplemental_text,
            }
        )

    return _catalog_record(
        source_url=source_url,
        source_title=_source_title_from_html(index_html),
        provider="ctext-html",
        chapters=chapters,
    )


def _harvest_indexed_plain_text_book(
    source_url: str,
    *,
    href_prefix: str,
    title_pattern: re.Pattern[str] | None = None,
) -> dict:
    index_html = _fetch_html(source_url)
    chapters: list[dict] = []

    for order, (title, href) in enumerate(
        _extract_chapter_links(index_html, href_prefix=href_prefix, title_pattern=title_pattern),
        start=1,
    ):
        chapter_url = urljoin("https://ctext.org/", href)
        if "?" not in chapter_url:
            chapter_url = f"{chapter_url}?if=en"
        chapter_html = _fetch_html(chapter_url)
        text = "\n".join(_extract_plain_ctext_rows(chapter_html)).strip()
        if not text:
            continue
        chapters.append(_chapter_record(order=order, title=title, text=text))

    return _catalog_record(
        source_url=source_url,
        source_title=_source_title_from_html(index_html),
        provider="ctext-html",
        chapters=chapters,
    )


def _harvest_single_page_ctext_book(source_url: str, *, title_template: str) -> dict:
    html_text = _fetch_html(source_url)
    chapters = [
        _chapter_record(
            order=order,
            title=title_template.format(order=order),
            summary=_summary_from_text(text),
            text=text,
        )
        for order, text in enumerate(_extract_plain_ctext_rows(html_text), start=1)
        if text
    ]
    return _catalog_record(
        source_url=source_url,
        source_title=_source_title_from_html(html_text),
        provider="ctext-html",
        chapters=chapters,
    )


def _harvest_single_chapter_ctext_book(source_url: str, *, chapter_title: str) -> dict:
    html_text = _fetch_html(source_url)
    text = "\n".join(_extract_plain_ctext_rows(html_text)).strip()
    chapters = [
        _chapter_record(
            order=1,
            title=chapter_title,
            summary=_summary_from_text(text),
            text=text,
        )
    ]
    return _catalog_record(
        source_url=source_url,
        source_title=_source_title_from_html(html_text),
        provider="ctext-html",
        chapters=chapters,
    )


def _harvest_single_chapter_wikisource_book(source_url: str, *, chapter_title: str) -> dict:
    html_text = _fetch_html(source_url)
    blocks = _extract_wikisource_blocks(html_text)
    text = _joined_wikisource_text(blocks[:1])
    chapters = [
        _chapter_record(
            order=1,
            title=chapter_title,
            summary=_summary_from_text(text),
            text=text,
        )
    ]
    return _catalog_record(
        source_url=source_url,
        source_title=_source_title_from_html(html_text),
        provider="wikisource-html",
        chapters=chapters,
    )


def _harvest_wikisource_sanguo_book(source_url: str) -> dict:
    index_html = _fetch_html(source_url)
    chapters: list[dict] = []

    for match in SANGUO_WIKISOURCE_LINK_RE.finditer(index_html):
        order = int(match.group("number"))
        href = match.group("href")
        label = _normalize_whitespace(_strip_tags(match.group("label")))
        tail = _normalize_whitespace(_strip_tags(match.group("tail")))
        title = f"{label} {tail}".strip()
        chapter_html = _fetch_html(urljoin("https://zh.wikisource.org", href))
        text = _joined_wikisource_text(_extract_wikisource_blocks(chapter_html))
        if not text:
            continue
        chapters.append(_chapter_record(order=order, title=title, text=text))

    return _catalog_record(
        source_url=source_url,
        source_title=_source_title_from_html(index_html),
        provider="wikisource-html",
        chapters=chapters,
    )


def _curate_da_xue_catalog(raw_catalog: dict) -> dict:
    raw_chapters = raw_catalog.get("chapters", [])
    expected_raw_count = int(BUNDLED_SOURCES["da-xue"]["source_chapter_count"])
    if len(raw_chapters) != expected_raw_count:
        raise ValueError(f"da-xue expected {expected_raw_count} raw chapters but harvested {len(raw_chapters)}.")

    first_chapter = raw_chapters[0]
    first_text = str(first_chapter.get("text", "")).strip()
    first_lines = [line.strip() for line in first_text.splitlines() if line.strip()]

    core_start = next(
        (index for index, line in enumerate(first_lines) if line.startswith(DA_XUE_CORE_CHAPTER_SPECS[0]["title"])),
        None,
    )
    if core_start is None:
        raise ValueError("da-xue chapter-001 did not contain the expected core text boundary.")

    introduction_lines = first_lines[:core_start]
    core_lines = first_lines[core_start:]
    if len(core_lines) != len(DA_XUE_CORE_CHAPTER_SPECS):
        raise ValueError(
            f"da-xue expected {len(DA_XUE_CORE_CHAPTER_SPECS)} core lines but found {len(core_lines)}."
        )

    core_chapters: list[dict] = []
    for order, (spec, line) in enumerate(zip(DA_XUE_CORE_CHAPTER_SPECS, core_lines), start=1):
        if not line.startswith(spec["title"]):
            raise ValueError(f"da-xue core line {order} did not start with {spec['title']!r}.")
        core_chapters.append(
            _chapter_record(
                order=order,
                title=spec["title"],
                summary=spec["summary"],
                text=line,
            )
        )

    introduction_text = "\n".join(introduction_lines).strip()
    if not introduction_text:
        raise ValueError("da-xue chapter-001 did not contain the expected Zhu Xi preface block.")

    commentary_chapters = [
        {
            "id": "commentary-introduction",
            "order": 0,
            "title": DA_XUE_COMMENTARY_INTRO_TITLE,
            "summary": DA_XUE_COMMENTARY_INTRO_SUMMARY,
            "character_count": _count_characters(introduction_text),
            "text": introduction_text,
            "supplemental_text": str(first_chapter.get("supplemental_text", "")).strip(),
        }
    ]

    for order, chapter in enumerate(raw_chapters[1:], start=1):
        commentary_chapters.append(
            {
                "id": f"commentary-chapter-{order:03d}",
                "order": order,
                "title": str(chapter.get("title", "")).strip(),
                "summary": str(chapter.get("summary", "")).strip(),
                "character_count": int(chapter.get("character_count", 0)),
                "text": str(chapter.get("text", "")).strip(),
                "supplemental_text": str(chapter.get("supplemental_text", "")).strip(),
            }
        )

    return {
        **raw_catalog,
        "chapter_count": len(core_chapters),
        "chapters": core_chapters,
        "commentary_chapter_count": len(commentary_chapters),
        "commentary_chapters": commentary_chapters,
        "core_text_note": DA_XUE_CORE_TEXT_NOTE,
    }


def _catalog_for_work(work_id: str) -> dict:
    source_url = BUNDLED_SOURCES[work_id]["source_url"]
    if work_id == "da-xue":
        return _curate_da_xue_catalog(_build_catalog_from_html(source_url, _fetch_html(source_url)))
    if work_id == "zhong-yong":
        return _build_catalog_from_html(source_url, _fetch_html(source_url))
    if work_id == "lunyu":
        return _harvest_indexed_book(source_url, title_pattern=LUNYU_TITLE_RE)
    if work_id == "mengzi":
        return _harvest_indexed_book(source_url, title_pattern=MENGZI_TITLE_RE)
    if work_id == "sunzi-bingfa":
        return _harvest_indexed_plain_text_book(
            source_url,
            href_prefix="art-of-war/",
            title_pattern=SUNZI_TITLE_RE,
        )
    if work_id == "daodejing":
        return _harvest_single_page_ctext_book(source_url, title_template="第{order}章")
    if work_id == "san-zi-jing":
        return _harvest_single_chapter_ctext_book(source_url, chapter_title="全篇")
    if work_id == "qian-zi-wen":
        return _harvest_single_chapter_wikisource_book(source_url, chapter_title="全篇")
    if work_id == "sanguo-yanyi":
        return _harvest_wikisource_sanguo_book(source_url)
    raise KeyError(f"Unknown bundled work: {work_id}")


def _assert_expected_chapter_count(work_id: str, catalog: dict) -> None:
    expected = int(BUNDLED_SOURCES[work_id]["chapter_count"])
    actual = int(catalog["chapter_count"])
    if actual != expected:
        raise ValueError(f"{work_id} expected {expected} chapters but harvested {actual}.")


def _has_complete_local_bundle(work_id: str) -> bool:
    source_url = BUNDLED_SOURCES[work_id]["source_url"]
    catalog_path = _store_dir_for_url(source_url) / CATALOG_CACHE_FILE
    payload = _read_json_file(catalog_path)
    if payload is None:
        return False
    if int(payload.get("chapter_count", 0)) != int(BUNDLED_SOURCES[work_id]["chapter_count"]):
        return False
    chapters = payload.get("chapters", [])
    if not isinstance(chapters, list) or not chapters:
        return False
    if "reading_unit_count" not in chapters[0]:
        return False

    first_chapter_path = _store_dir_for_url(source_url) / CHAPTERS_DIRNAME / f"{chapters[0]['id']}.json"
    first_chapter = _read_json_file(first_chapter_path)
    if first_chapter is None:
        return False
    chapter_payload = first_chapter.get("chapter", {})
    if not isinstance(chapter_payload, dict):
        return False
    if not chapter_payload.get("reading_units"):
        return False

    expected_commentary_count = int(BUNDLED_SOURCES[work_id].get("commentary_chapter_count", 0))
    if int(payload.get("commentary_chapter_count", 0)) != expected_commentary_count:
        return False
    if expected_commentary_count == 0:
        return True

    commentary = payload.get("commentary_chapters", [])
    if not isinstance(commentary, list) or len(commentary) != expected_commentary_count:
        return False
    if "reading_unit_count" not in commentary[0]:
        return False

    first_commentary_path = _store_dir_for_url(source_url) / COMMENTARY_DIRNAME / f"{commentary[0]['id']}.json"
    first_commentary = _read_json_file(first_commentary_path)
    if first_commentary is None:
        return False
    commentary_payload = first_commentary.get("commentary", {})
    if not isinstance(commentary_payload, dict):
        return False
    return bool(first_commentary.get("schema_version")) and bool(commentary_payload.get("reading_units"))


def build_source_store() -> None:
    SOURCE_STORE_DIR.mkdir(parents=True, exist_ok=True)

    for work_id, spec in BUNDLED_SOURCES.items():
        if _has_complete_local_bundle(work_id):
            continue
        catalog = _catalog_for_work(work_id)
        _assert_expected_chapter_count(work_id, catalog)
        _write_catalog_and_chapters(spec["source_url"], catalog)


if __name__ == "__main__":
    build_source_store()
