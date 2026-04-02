from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Callable

from . import __version__
from .claude_host import default_claude_target, install_claude_skills
from .display import canonical_layer_name, format_hanzi_layers, format_reading_layers
from .codex_host import default_codex_target, install_codex_skills
from .flashcards import run_flashcard_review_step, save_flashcard_artifacts
from .gemini_host import default_gemini_target, install_gemini_commands
from .progress import (
    guided_reading_catalog,
    load_progress,
    progress_path,
    save_book_progress,
    save_chapter_generated_annotations,
    save_chapter_progress,
    save_learner_style,
)
from .rendering import DEFAULT_CHARACTER_LAYOUT, render_json, render_lines_markdown
from .runtime import render_reading_pass, run_guided_reading_session
from .source_catalog import build_source_catalog, build_source_reading_pass, download_source_chapter
from .updates import check_for_updates, config_value_to_text, get_config_value, load_config, set_config_value, write_snooze


def _run_install_command(
    installer: Callable[..., list[Path]],
    *,
    label: str,
    target: Path | None,
    force: bool,
) -> int:
    try:
        installed = installer(target=target, force=force)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Installed {len(installed)} {label}:")
    for path in installed:
        print(f"- {path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="the_big_learn", description="Runtime tools for The Big Learn.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a passage from the local annotations.")
    render_parser.add_argument("--work", default="da-xue")
    render_parser.add_argument("--start", type=int)
    render_parser.add_argument("--end", type=int)
    render_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    render_parser.add_argument(
        "--character-layout",
        choices=["table", "stacked"],
        default=DEFAULT_CHARACTER_LAYOUT,
    )

    session_parser = subparsers.add_parser("session", help="Run the starter guided-reading fixture.")
    session_parser.add_argument("--fixture")
    session_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    session_parser.add_argument(
        "--character-layout",
        choices=["table", "stacked"],
        default=DEFAULT_CHARACTER_LAYOUT,
    )

    progress_parser = subparsers.add_parser("progress", help="Show saved guided-reading progress.")
    progress_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    progress_save_parser = subparsers.add_parser(
        "progress-save",
        help="Save guided-reading chapter or book artifacts from JSON.",
    )
    progress_save_parser.add_argument(
        "--input",
        default="-",
        help="Path to a JSON payload file, or - to read JSON from stdin.",
    )
    progress_save_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    source_parser = subparsers.add_parser("source", help="Inspect and save externally sourced chapter catalogs.")
    source_subparsers = source_parser.add_subparsers(dest="source_command", required=True)

    source_catalog_parser = source_subparsers.add_parser(
        "catalog",
        help="Build a chapter catalog from a source URL and save it locally.",
    )
    source_catalog_parser.add_argument("--url", required=True)
    source_catalog_parser.add_argument("--refresh", action="store_true")
    source_catalog_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    source_download_parser = source_subparsers.add_parser(
        "download",
        help="Download one chapter from a source URL and save it locally.",
    )
    source_download_parser.add_argument("--url", required=True)
    source_download_parser.add_argument("--chapter", required=True)
    source_download_parser.add_argument("--refresh", action="store_true")
    source_download_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    source_read_parser = source_subparsers.add_parser(
        "read",
        help="Load one saved source chapter into raw reading units.",
    )
    source_read_parser.add_argument("--url", required=True)
    source_read_parser.add_argument("--chapter", required=True)
    source_read_parser.add_argument("--refresh", action="store_true")
    source_read_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    version_parser = subparsers.add_parser("version", help="Show the installed The Big Learn version.")
    version_parser.add_argument("--json", action="store_true")

    update_check_parser = subparsers.add_parser("update-check", help="Check whether a newer The Big Learn version is available.")
    update_check_parser.add_argument("--force", action="store_true")

    update_snooze_parser = subparsers.add_parser("update-snooze", help="Snooze prompts for a specific remote version.")
    update_snooze_parser.add_argument("--version", required=True)
    update_snooze_parser.add_argument("--level", type=int, default=1)

    config_parser = subparsers.add_parser("config", help="Read or write local The Big Learn configuration.")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)

    config_get_parser = config_subparsers.add_parser("get", help="Read one config value.")
    config_get_parser.add_argument("key")

    config_set_parser = config_subparsers.add_parser("set", help="Write one config value.")
    config_set_parser.add_argument("key")
    config_set_parser.add_argument("value")

    config_subparsers.add_parser("list", help="Show the full config payload.")

    codex_parser = subparsers.add_parser("codex", help="Codex host integration commands.")
    codex_subparsers = codex_parser.add_subparsers(dest="codex_command", required=True)

    codex_install_parser = codex_subparsers.add_parser("install", help="Install The Big Learn skills into Codex.")
    codex_install_parser.add_argument("--target")
    codex_install_parser.add_argument("--force", action="store_true")

    codex_path_parser = codex_subparsers.add_parser("path", help="Show the default Codex skills install path.")
    codex_path_parser.add_argument("--json", action="store_true")

    claude_parser = subparsers.add_parser("claude", help="Claude Code host integration commands.")
    claude_subparsers = claude_parser.add_subparsers(dest="claude_command", required=True)

    claude_install_parser = claude_subparsers.add_parser(
        "install", help="Install The Big Learn skills into Claude Code."
    )
    claude_install_parser.add_argument("--target")
    claude_install_parser.add_argument("--force", action="store_true")

    claude_path_parser = claude_subparsers.add_parser("path", help="Show the default Claude Code skills install path.")
    claude_path_parser.add_argument("--json", action="store_true")

    gemini_parser = subparsers.add_parser("gemini", help="Gemini CLI host integration commands.")
    gemini_subparsers = gemini_parser.add_subparsers(dest="gemini_command", required=True)

    gemini_install_parser = gemini_subparsers.add_parser(
        "install", help="Install The Big Learn commands into Gemini CLI."
    )
    gemini_install_parser.add_argument("--target")
    gemini_install_parser.add_argument("--force", action="store_true")

    gemini_path_parser = gemini_subparsers.add_parser("path", help="Show the default Gemini CLI commands install path.")
    gemini_path_parser.add_argument("--json", action="store_true")

    flashcard_save_parser = subparsers.add_parser(
        "flashcard-save",
        help="Save a flashcard bank entry and optional variations from JSON.",
    )
    flashcard_save_parser.add_argument(
        "--input",
        default="-",
        help="Path to a JSON payload file, or - to read JSON from stdin.",
    )
    flashcard_save_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    flashcard_review_parser = subparsers.add_parser(
        "flashcard-review",
        help="Step through weighted flashcard review, alternating prompt and reveal.",
    )
    flashcard_review_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    flashcard_review_parser.add_argument("--seed", type=int)
    flashcard_review_parser.add_argument("--reset", action="store_true")

    return parser


def _read_json_input(input_path: str) -> dict:
    if input_path == "-":
        raw_payload = sys.stdin.read()
    else:
        raw_payload = Path(input_path).read_text(encoding="utf-8")

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input payload is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Input payload must be a JSON object.")

    return payload


def _render_session_markdown(result: dict, *, character_layout: str = DEFAULT_CHARACTER_LAYOUT) -> str:
    chunks = [
        f"# Session {result['session_id']}",
        "",
        "## Reading Pass",
        render_lines_markdown(
            result["lines"],
            result.get("learner_translations"),
            character_layout=character_layout,
        ),
        "",
        "## Immediate Answers",
    ]
    if not result["answers"]:
        chunks.append("- No line questions in this fixture.")
    for answer in result["answers"]:
        chunks.append(f"### {answer['question_id']}")
        if answer.get("question"):
            chunks.append(f"- Question: {answer['question']}")
        chunks.append(f"- Phrase: {answer['phrase']}")
        chunks.append(f"- Direct answer: {answer['direct_answer']}")
        chunks.append(f"- Explanation: {answer['explanation']}")
        if answer.get("variant_note"):
            chunks.append(f"- Variant note: {answer['variant_note']}")

    chunks.append("")
    chunks.append("## Flashcard Entries")
    for entry in result["flashcard_entries"]:
        chunks.append(f"### {entry['id']}")
        chunks.append(f"- Hanzi: {format_hanzi_layers(entry['layers'])}")
        chunks.append(f"- Reading: {format_reading_layers(entry['layers'])}")
        chunks.append(f"- Gloss EN: {entry['layers']['gloss_en']}")

    chunks.append("")
    chunks.append("## Flashcard Variations")
    for variation in result["flashcard_variations"]:
        prompt_layer = canonical_layer_name(variation["prompt_layer"])
        answer_layer = canonical_layer_name(variation["answer_layer"])
        chunks.append(
            f"- {prompt_layer} -> {answer_layer}: "
            f"{variation['prompt_text']} => {variation['answer_text']}"
        )

    return "\n".join(chunks).strip()


def _render_progress_markdown(result: dict) -> str:
    chunks = ["# Reading Progress", ""]
    for book in result["books"]:
        chunks.append(f"## {book['title']}")
        chunks.append(f"- Book summary saved: {'yes' if book.get('has_personal_summary') else 'no'}")
        chunks.append(f"- Book response saved: {'yes' if book.get('has_book_personal_response') else 'no'}")
        chunks.append(
            f"- Chapters/containers with personal translations: {book['translated_chapter_count']}/{book['chapter_count']}"
        )
        chunks.append(
            f"- Chapters/containers with personal responses: {book['responded_chapter_count']}/{book['chapter_count']}"
        )
        for chapter in book["chapters"]:
            chunks.append(
                f"- {chapter['title']}: {chapter['status_label']} "
                f"({chapter['line_count']} lines, about {chapter['character_count']} Chinese characters)"
            )
        chunks.append("")
    return "\n".join(chunks).strip()


def _render_progress_save_markdown(result: dict) -> str:
    chunks = [
        "# Guided Reading Progress Saved",
        "",
        f"- Saved file: {result['progress_path']}",
    ]
    if isinstance(result.get("work"), str):
        chunks.append(f"- Work: {result['work']}")
    if isinstance(result.get("section"), str):
        chunks.append(f"- Chapter/container: {result['section']}")
    if "saved_translation" in result:
        chunks.append(f"- Saved translation: {'yes' if result['saved_translation'] else 'no'}")
    if "saved_response" in result:
        chunks.append(f"- Saved response: {'yes' if result['saved_response'] else 'no'}")
    if "saved_summary" in result:
        chunks.append(f"- Saved summary: {'yes' if result['saved_summary'] else 'no'}")
    if "saved_book_response" in result:
        chunks.append(f"- Saved book response: {'yes' if result['saved_book_response'] else 'no'}")
    if result.get("saved_learner_style"):
        chunks.append("- Saved learner style: yes")

    saved_generated_annotations = result.get("saved_generated_annotations")
    if isinstance(saved_generated_annotations, int):
        chunks.append(f"- Saved generated annotations: {saved_generated_annotations}")

    saved_character_index_cards = result.get("saved_character_index_cards")
    if isinstance(saved_character_index_cards, int):
        chunks.append(f"- Character index cards touched: {saved_character_index_cards}")

    saved_character_index_citations = result.get("saved_character_index_citations")
    if isinstance(saved_character_index_citations, int):
        chunks.append(f"- Character index citations added: {saved_character_index_citations}")

    generated_annotation_chapter_path = result.get("generated_annotation_chapter_path")
    if isinstance(generated_annotation_chapter_path, str) and generated_annotation_chapter_path.strip():
        chunks.append(f"- Generated annotation chapter file: {generated_annotation_chapter_path}")

    return "\n".join(chunks).strip()


def _render_source_catalog_markdown(result: dict) -> str:
    chunks = [
        f"# {result['title']}",
        "",
        f"- Provider: {result['provider']}",
        f"- Source URL: {result['source_url']}",
        f"- Chapters detected: {result['chapter_count']}",
        f"- Saved catalog: {result['catalog_path']}",
        "",
    ]

    if result["chapters"]:
        chunks.append("## Chapters")
        for chapter in result["chapters"]:
            summary = f" - {chapter['summary']}" if chapter.get("summary") else ""
            chunks.append(
                f"- {chapter['order']}. {chapter['title']}{summary} "
                f"({chapter['character_count']} Chinese characters)"
            )
    else:
        chunks.append("No chapter markers were detected for this source.")

    return "\n".join(chunks).strip()


def _render_downloaded_source_chapter_markdown(result: dict) -> str:
    chapter = result["chapter"]
    return "\n".join(
        [
            f"# {result['source_title']}",
            "",
            f"- Chapter: {chapter['order']}. {chapter['title']}",
            f"- Source URL: {result['source_url']}",
            f"- Saved chapter: {result['chapter_path']}",
            f"- Character count: {chapter['character_count']}",
        ]
    ).strip()


def _render_source_reading_pass_markdown(result: dict) -> str:
    chapter = result["chapter"]
    chunks = [
        f"# {result['source_title']}",
        "",
        f"- Chapter: {chapter['order']}. {chapter['title']}",
        f"- Source URL: {result['source_url']}",
        f"- Saved chapter: {result['chapter_path']}",
        f"- Reading mode: {result['mode']}",
        f"- Reading units: {result['line_count']}",
    ]

    saved_annotation_count = result.get("saved_annotation_count")
    if isinstance(saved_annotation_count, int) and saved_annotation_count:
        chunks.append(f"- Reading units with saved generated annotations: {saved_annotation_count}")

    saved_character_index_count = result.get("saved_character_index_count")
    if isinstance(saved_character_index_count, int) and saved_character_index_count:
        chunks.append(f"- Reading units reconstructed from character index: {saved_character_index_count}")

    chunks.append("")

    for index, line in enumerate(result["lines"], start=1):
        line_index = line.get("line_index_in_container", index)
        line_count = line.get("container_line_count", result["line_count"])
        chunks.append(f"## {line['id']}")
        chunks.append(f"Line {line_index}/{line_count}")
        if line.get("has_saved_generated_annotation"):
            chunks.append("Saved generated annotation: yes")
        if line.get("has_saved_character_index_annotation"):
            chunks.append("Reconstructed from character index: yes")
        chunks.append(line["text"])
        chunks.append("")

    return "\n".join(chunks).strip()


def _render_flashcard_save_markdown(result: dict) -> str:
    chunks = [
        "# Flashcard Saved",
        "",
        f"- Bank entry id: {result['bank_entry_id']}",
    ]

    if "bank_entry_path" in result:
        chunks.append(f"- Bank entry file: {result['bank_entry_path']}")

    if "variations_path" in result:
        chunks.append(f"- Variations file: {result['variations_path']}")
        chunks.append(f"- Saved variations: {result['variation_count']}")

    if "significance_flag_count" in result:
        chunks.append(f"- Significance flags: {result['significance_flag_count']}")

    return "\n".join(chunks).strip()


def _render_flashcard_review_markdown(result: dict) -> str:
    chunks = [
        "# Flashcard Review",
        "",
        f"- Phase: {result['phase']}",
        f"- Bank entry id: {result['bank_entry_id']}",
        f"- Status: {result['status']}",
        f"- Origin: {result['origin_kind']}",
        f"- Weight: {result['weight']}",
        f"- Significance flags: {result['significance_flag_count']}",
        f"- Occurrences: {result['occurrence_count']}",
        "",
        "## Visible",
    ]
    for face in result["visible_faces"]:
        label = "Reading + definitions" if face["name"] == "reading" else "Hanzi"
        chunks.append(f"- {label}: {face['text']}")

    if result["phase"] == "prompt":
        hidden_label = "reading + definitions" if result["hidden_face_name"] == "reading" else "hanzi"
        chunks.append("")
        chunks.append(f"Next step reveals: {hidden_label}")
    else:
        chunks.append("")
        chunks.append("Next step draws a new card.")

    return "\n".join(chunks).strip()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "render":
        result = render_reading_pass(args.work, start=args.start, end=args.end)
        output = (
            render_lines_markdown(result["lines"], character_layout=args.character_layout)
            if args.format == "markdown"
            else render_json(result)
        )
        print(output)
        return 0

    if args.command == "session":
        result = run_guided_reading_session(args.fixture)
        output = (
            _render_session_markdown(result, character_layout=args.character_layout)
            if args.format == "markdown"
            else render_json(result)
        )
        print(output)
        return 0

    if args.command == "progress":
        saved_progress = load_progress()
        result = {"books": guided_reading_catalog()}
        learner_style = saved_progress.get("learner_style")
        if isinstance(learner_style, dict):
            result["learner_style"] = learner_style
        output = _render_progress_markdown(result) if args.format == "markdown" else render_json(result)
        print(output)
        return 0

    if args.command == "progress-save":
        try:
            payload = _read_json_input(args.input)
            work = payload.get("work")
            section = payload.get("section")
            learner_style = payload.get("learner_style")
            has_chapter_artifacts = any(
                key in payload
                for key in (
                    "personal_translation_en",
                    "personal_response_en",
                    "learner_translation_log",
                    "learner_response_log",
                    "generated_annotations",
                )
            )
            has_book_artifacts = any(
                key in payload
                for key in (
                    "personal_book_summary_en",
                    "personal_book_response_en",
                )
            )

            generated_annotation_result = None
            result = {"progress_path": str(progress_path())}
            saved_chapter_scope = False

            if has_chapter_artifacts or (learner_style is not None and (work is not None or section is not None)):
                if not isinstance(work, str) or not work.strip() or not isinstance(section, str) or not section.strip():
                    raise ValueError(
                        "progress-save requires `work` and `section` when saving chapter artifacts or work-scoped learner style."
                    )

                saved_chapter = save_chapter_progress(
                    work,
                    section,
                    personal_translation_en=payload.get("personal_translation_en"),
                    personal_response_en=payload.get("personal_response_en"),
                    learner_translation_log=payload.get("learner_translation_log"),
                    learner_response_log=payload.get("learner_response_log"),
                    learner_style=learner_style,
                    saved_at=payload.get("saved_at"),
                )
                if "generated_annotations" in payload:
                    generated_annotation_result = save_chapter_generated_annotations(
                        work,
                        section,
                        payload.get("generated_annotations"),
                        saved_at=payload.get("saved_at"),
                    )
                result.update(
                    {
                        "work": work,
                        "section": section,
                        "saved_translation": (
                            "learner_translation_log" in saved_chapter or "personal_translation_en" in saved_chapter
                        ),
                        "saved_response": (
                            "learner_response_log" in saved_chapter or "personal_response_en" in saved_chapter
                        ),
                        "saved_learner_style": learner_style is not None,
                        "chapter": saved_chapter,
                    }
                )
                saved_chapter_scope = True

            if has_book_artifacts:
                if not isinstance(work, str) or not work.strip():
                    raise ValueError("progress-save requires `work` when saving book artifacts.")
                saved_book = save_book_progress(
                    work,
                    personal_summary_en=payload.get("personal_book_summary_en"),
                    personal_response_en=payload.get("personal_book_response_en"),
                    saved_at=payload.get("saved_at"),
                )
                result.update(
                    {
                        "work": work,
                        "saved_summary": "personal_summary_en" in saved_book,
                        "saved_book_response": "personal_response_en" in saved_book,
                        "book": saved_book,
                    }
                )

            if not saved_chapter_scope and not has_book_artifacts:
                if learner_style is None:
                    raise ValueError(
                        "progress-save payload must include chapter artifacts, book artifacts, or a `learner_style` object."
                    )
                merged_learner_style = save_learner_style(learner_style, saved_at=payload.get("saved_at"))
                result.update(
                    {
                        "saved_learner_style": True,
                        "learner_style": merged_learner_style,
                    }
                )

            merged_progress = load_progress()
            merged_learner_style = merged_progress.get("learner_style")
            if isinstance(merged_learner_style, dict):
                result["learner_style"] = merged_learner_style
            if generated_annotation_result is not None:
                result["saved_generated_annotations"] = generated_annotation_result["saved_annotation_count"]
                result["generated_annotation_chapter_path"] = generated_annotation_result["chapter_path"]
                if "saved_character_index_cards" in generated_annotation_result:
                    result["saved_character_index_cards"] = generated_annotation_result["saved_character_index_cards"]
                if "saved_character_index_citations" in generated_annotation_result:
                    result["saved_character_index_citations"] = generated_annotation_result[
                        "saved_character_index_citations"
                    ]
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        output = _render_progress_save_markdown(result) if args.format == "markdown" else render_json(result)
        print(output)
        return 0

    if args.command == "source":
        if args.source_command == "catalog":
            result = build_source_catalog(args.url, refresh=args.refresh)
            output = _render_source_catalog_markdown(result) if args.format == "markdown" else render_json(result)
            print(output)
            return 0

        if args.source_command == "download":
            result = download_source_chapter(args.url, args.chapter, refresh=args.refresh)
            output = (
                _render_downloaded_source_chapter_markdown(result)
                if args.format == "markdown"
                else render_json(result)
            )
            print(output)
            return 0

        if args.source_command == "read":
            result = build_source_reading_pass(args.url, args.chapter, refresh=args.refresh)
            output = _render_source_reading_pass_markdown(result) if args.format == "markdown" else render_json(result)
            print(output)
            return 0

    if args.command == "version":
        if args.json:
            print(render_json({"version": __version__}))
        else:
            print(__version__)
        return 0

    if args.command == "update-check":
        result = check_for_updates(force=args.force)
        if result is not None:
            print(result.output_line())
        return 0

    if args.command == "update-snooze":
        write_snooze(args.version, args.level)
        print(f"Snoozed update prompts for {args.version} at level {max(1, args.level)}.")
        return 0

    if args.command == "config":
        if args.config_command == "get":
            value = get_config_value(args.key)
            if value is not None:
                print(config_value_to_text(value))
            return 0

        if args.config_command == "set":
            set_config_value(args.key, args.value)
            value = load_config().get(args.key)
            if value is None:
                print(f"Cleared {args.key}.")
            else:
                print(f"{args.key}={config_value_to_text(value)}")
            return 0

        if args.config_command == "list":
            print(render_json(load_config()))
            return 0

    if args.command == "codex":
        if args.codex_command == "path":
            path = str(default_codex_target())
            if args.json:
                print(render_json({"target": path}))
            else:
                print(path)
            return 0

        if args.codex_command == "install":
            target = None if args.target is None else Path(args.target)
            return _run_install_command(
                install_codex_skills,
                label="Codex skills",
                target=target,
                force=args.force,
            )

    if args.command == "claude":
        if args.claude_command == "path":
            path = str(default_claude_target())
            if args.json:
                print(render_json({"target": path}))
            else:
                print(path)
            return 0

        if args.claude_command == "install":
            target = None if args.target is None else Path(args.target)
            return _run_install_command(
                install_claude_skills,
                label="Claude Code skills",
                target=target,
                force=args.force,
            )

    if args.command == "gemini":
        if args.gemini_command == "path":
            path = str(default_gemini_target())
            if args.json:
                print(render_json({"target": path}))
            else:
                print(path)
            return 0

        if args.gemini_command == "install":
            target = None if args.target is None else Path(args.target)
            return _run_install_command(
                install_gemini_commands,
                label="Gemini CLI command trees",
                target=target,
                force=args.force,
            )

    if args.command == "flashcard-save":
        payload = _read_json_input(args.input)
        bank_entry = payload.get("bank_entry") if "bank_entry" in payload else None
        if bank_entry is None and "id" in payload and "layers" in payload:
            bank_entry = payload

        saved = save_flashcard_artifacts(
            bank_entry=bank_entry,
            bank_entry_id=payload.get("bank_entry_id"),
            variations=payload.get("variations"),
            significance_flag_increment=payload.get("significance_flag_increment"),
        )
        result = {
            "bank_entry_id": saved.get("bank_entry", {}).get("id", saved.get("bank_entry_id")),
        }
        if "bank_entry_path" in saved:
            result["bank_entry_path"] = saved["bank_entry_path"]
        if "variations_path" in saved:
            result["variations_path"] = saved["variations_path"]
            result["variation_count"] = saved["variation_count"]
        if "significance_flag_count" in saved:
            result["significance_flag_count"] = saved["significance_flag_count"]
        elif "bank_entry" in saved and "significance_flag_count" in saved["bank_entry"]:
            result["significance_flag_count"] = saved["bank_entry"]["significance_flag_count"]
        output = _render_flashcard_save_markdown(result) if args.format == "markdown" else render_json(result)
        print(output)
        return 0

    if args.command == "flashcard-review":
        try:
            result = run_flashcard_review_step(
                rng=random.Random(args.seed) if args.seed is not None else None,
                reset=args.reset,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        output = _render_flashcard_review_markdown(result) if args.format == "markdown" else render_json(result)
        print(output)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
