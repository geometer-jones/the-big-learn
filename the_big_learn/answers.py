from __future__ import annotations

from .display import format_hanzi_layers, format_hanzi_pair


def build_line_answer(question: dict, line: dict, segment: dict | None) -> dict:
    phrase = format_hanzi_pair(segment["traditional"], segment["simplified"]) if segment else format_hanzi_layers(line["layers"])
    gloss = segment["gloss_en"] if segment else line["layers"]["gloss_en"]
    direct_answer = f"{phrase} is being read here as '{gloss}'."

    variant_note = None
    if segment and segment.get("notes"):
        variant_note = segment["notes"][0]
        direct_answer = (
            f"{phrase} is being read here as '{gloss}' because this reading tradition treats the phrase "
            f"through a commentarial lens, not just the most everyday modern sense."
        )

    explanation_parts = [
        f"Line {line['id']} reads: {format_hanzi_layers(line['layers'])}",
        f"The local gloss for {phrase} is '{gloss}'.",
        f"Whole-line translation: {line['layers']['translation_en']}",
    ]
    if variant_note:
        explanation_parts.append(f"Variant note: {variant_note}")

    return {
        "question_id": question["id"],
        "question": question["question"],
        "line_id": line["id"],
        "segment_id": question.get("segment_id"),
        "phrase": phrase,
        "direct_answer": direct_answer,
        "explanation": " ".join(explanation_parts),
        "variant_note": variant_note,
        "suggest_flashcard": segment is not None,
    }
