from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Callable

from .claude_host import default_claude_target, install_claude_skills
from .codex_host import default_codex_target, install_codex_skills
from .flashcards import run_flashcard_review_step, save_flashcard_artifacts
from .gemini_host import default_gemini_target, install_gemini_commands
from .progress import (
    progress_artifact_paths,
    progress_path,
    save_book_progress,
    save_chapter_generated_annotations,
    save_chapter_progress,
    save_learner_style,
)
from .source_catalog import build_source_catalog, build_source_reading_pass


def _render_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


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


def _render_progress_save_markdown(result: dict) -> str:
    chunks = [
        "# Guided Reading Progress Saved",
        "",
        f"- Saved file: {result['progress_path']}",
    ]
    artifact_paths = result.get("artifact_paths")
    if isinstance(artifact_paths, dict):
        if isinstance(artifact_paths.get("root"), str):
            chunks.append(f"- Browsable artifacts root: {artifact_paths['root']}")
        if isinstance(artifact_paths.get("book"), str):
            chunks.append(f"- Book artifact file: {artifact_paths['book']}")
        if isinstance(artifact_paths.get("chapter"), str):
            chunks.append(f"- Chapter artifact file: {artifact_paths['chapter']}")
        if isinstance(artifact_paths.get("learner_translation_log"), str):
            chunks.append(f"- Translation log file: {artifact_paths['learner_translation_log']}")
        if isinstance(artifact_paths.get("learner_response_log"), str):
            chunks.append(f"- Response log file: {artifact_paths['learner_response_log']}")
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="the_big_learn",
        description="Host support tools for The Big Learn.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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

    source_parser = subparsers.add_parser(
        "source",
        help="Build or read source-backed chapter data for host-driven guided reading.",
    )
    source_subparsers = source_parser.add_subparsers(dest="source_command", required=True)

    source_catalog_parser = source_subparsers.add_parser(
        "catalog",
        help="Build a chapter catalog from a source URL and save it locally.",
    )
    source_catalog_parser.add_argument("--url", required=True)
    source_catalog_parser.add_argument("--refresh", action="store_true")
    source_catalog_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    source_read_parser = source_subparsers.add_parser(
        "read",
        help="Load one saved source chapter into raw reading units.",
    )
    source_read_parser.add_argument("--url", required=True)
    source_read_parser.add_argument("--chapter", required=True)
    source_read_parser.add_argument("--refresh", action="store_true")
    source_read_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

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
        "install",
        help="Install The Big Learn skills into Claude Code.",
    )
    claude_install_parser.add_argument("--target")
    claude_install_parser.add_argument("--force", action="store_true")
    claude_path_parser = claude_subparsers.add_parser("path", help="Show the default Claude Code skills install path.")
    claude_path_parser.add_argument("--json", action="store_true")

    gemini_parser = subparsers.add_parser("gemini", help="Gemini CLI host integration commands.")
    gemini_subparsers = gemini_parser.add_subparsers(dest="gemini_command", required=True)
    gemini_install_parser = gemini_subparsers.add_parser(
        "install",
        help="Install The Big Learn commands into Gemini CLI.",
    )
    gemini_install_parser.add_argument("--target")
    gemini_install_parser.add_argument("--force", action="store_true")
    gemini_path_parser = gemini_subparsers.add_parser(
        "path",
        help="Show the default Gemini CLI commands install path.",
    )
    gemini_path_parser.add_argument("--json", action="store_true")

    flashcard_save_parser = subparsers.add_parser(
        "flashcard-save",
        help="Save a flashcard bank entry and optional significance update from JSON.",
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


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

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
            result = {
                "progress_path": str(progress_path()),
                "artifact_paths": progress_artifact_paths(),
            }
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
                        "artifact_paths": progress_artifact_paths(work, section),
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
                        "artifact_paths": progress_artifact_paths(work),
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

        output = _render_progress_save_markdown(result) if args.format == "markdown" else _render_json(result)
        print(output)
        return 0

    if args.command == "source":
        if args.source_command == "catalog":
            result = build_source_catalog(args.url, refresh=args.refresh)
            output = _render_source_catalog_markdown(result) if args.format == "markdown" else _render_json(result)
            print(output)
            return 0

        if args.source_command == "read":
            result = build_source_reading_pass(args.url, args.chapter, refresh=args.refresh)
            output = _render_source_reading_pass_markdown(result) if args.format == "markdown" else _render_json(result)
            print(output)
            return 0

    if args.command == "codex":
        if args.codex_command == "path":
            path = str(default_codex_target())
            print(_render_json({"target": path}) if args.json else path)
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
            print(_render_json({"target": path}) if args.json else path)
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
            print(_render_json({"target": path}) if args.json else path)
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
        try:
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
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

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

        output = _render_flashcard_save_markdown(result) if args.format == "markdown" else _render_json(result)
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

        output = _render_flashcard_review_markdown(result) if args.format == "markdown" else _render_json(result)
        print(output)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
