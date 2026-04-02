from __future__ import annotations

from .answers import build_line_answer
from .flashcards import build_bank_entry, build_variations
from .repository import (
    find_segment,
    load_fixture,
    load_flashcard_policy,
    load_lines,
    select_lines_by_ids,
    select_lines_by_range,
)


def _annotate_container_positions(work: str, lines: list[dict]) -> list[dict]:
    section_positions: dict[str, tuple[int, int]] = {}
    section_counts: dict[str, int] = {}
    full_lines = load_lines(work)
    section_by_line_id: dict[str, str] = {}

    for full_line in full_lines:
        section = str(full_line["section"])
        line_id = str(full_line["id"])
        section_counts[section] = section_counts.get(section, 0) + 1
        section_by_line_id[line_id] = section
        section_positions[line_id] = (
            section_counts[section],
            0,
        )

    for line_id, (line_index, _) in tuple(section_positions.items()):
        section = section_by_line_id.get(line_id)
        if section is not None:
            section_positions[line_id] = (line_index, section_counts[section])

    annotated_lines: list[dict] = []
    for line in lines:
        payload = dict(line)
        line_id = str(line["id"])
        if line_id in section_positions:
            line_index, line_count = section_positions[line_id]
            payload["container_id"] = str(line["section"])
            payload["container_kind"] = "section"
            payload["line_index_in_container"] = line_index
            payload["container_line_count"] = line_count
        annotated_lines.append(payload)

    return annotated_lines


def render_reading_pass(work: str, start: int | None = None, end: int | None = None) -> dict:
    lines = _annotate_container_positions(work, select_lines_by_range(work, start=start, end=end))
    return {
        "work": work,
        "lines": lines,
    }


def run_guided_reading_session(fixture_path: str | None = None) -> dict:
    fixture = load_fixture(fixture_path)
    work = fixture["source"]["work"]
    lines = _annotate_container_positions(work, select_lines_by_ids(work, fixture["source"]["line_ids"]))
    line_index = {line["id"]: line for line in lines}
    flashcard_policy = load_flashcard_policy()
    learner_questions = fixture.get("learner_questions")
    if not isinstance(learner_questions, list):
        learner_questions = []

    answers = []
    flashcard_entries = []
    flashcard_variations = []

    for question in learner_questions:
        line = line_index[question["line_id"]]
        segment = find_segment(line, question.get("segment_id"))
        answer = build_line_answer(question, line, segment)
        answers.append(answer)

        if answer["suggest_flashcard"]:
            entry = build_bank_entry(question, line, segment)
            flashcard_entries.append(entry)
            flashcard_variations.extend(build_variations(entry, flashcard_policy))

    return {
        "session_id": fixture["session_id"],
        "workflow": fixture["workflow"],
        "source": fixture["source"],
        "lines": lines,
        "learner_translations": fixture.get("learner_translations", []),
        "answers": answers,
        "flashcard_entries": flashcard_entries,
        "flashcard_variations": flashcard_variations,
    }
