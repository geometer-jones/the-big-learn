#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from the_big_learn.repository import load_lines

ANNOTATION_FILE = ROOT / "annotations" / "da-xue" / "starter.annotations.json"
POLICY_FILE = ROOT / "flashcards" / "templates" / "default-variation-policy.json"
FIXTURE_FILE = ROOT / "evals" / "fixtures" / "da-xue-reading-session.json"

REQUIRED_LOOKUP_FIELDS = {
    "work",
    "lookup",
    "defaults",
    "lines",
}
REQUIRED_DEFAULTS = {
    "source_variant",
    "annotation_profile",
    "provenance",
}
REQUIRED_LOOKUP_CONFIG = {
    "provider",
    "traditional_variant",
    "simplified_variant",
}
REQUIRED_LOOKUP_LINE_FIELDS = {
    "id",
    "section",
    "order",
    "source_locator",
    "layers",
    "status",
}
REQUIRED_LOOKUP_LAYERS = {
    "traditional",
    "simplified",
    "zhuyin",
    "pinyin",
    "gloss_en",
    "translation_en",
}
REQUIRED_RUNTIME_LAYERS = {
    "traditional",
    "simplified",
    *REQUIRED_LOOKUP_LAYERS,
}
REQUIRED_LOOKUP_SEGMENT_FIELDS = {
    "id",
    "source_start",
    "source_end",
    "traditional",
    "simplified",
    "zhuyin",
    "pinyin",
    "gloss_en",
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def ids(items: Iterable[dict], key: str = "id") -> set[str]:
    return {item[key] for item in items}


def verify_lookup_spec(spec: dict) -> str:
    missing = REQUIRED_LOOKUP_FIELDS - set(spec)
    expect(not missing, f"Lookup spec missing fields: {sorted(missing)}")

    lookup_missing = REQUIRED_LOOKUP_CONFIG - set(spec["lookup"])
    expect(not lookup_missing, f"Lookup config missing fields: {sorted(lookup_missing)}")

    defaults_missing = REQUIRED_DEFAULTS - set(spec["defaults"])
    expect(not defaults_missing, f"Lookup defaults missing fields: {sorted(defaults_missing)}")

    provenance = spec["defaults"]["provenance"]
    expect("source_url" in provenance, "Lookup defaults must include provenance.source_url.")
    expect(str(provenance["source_url"]).strip(), "Lookup defaults must include a non-empty provenance.source_url.")

    return spec["work"]


def verify_lookup_lines(lines: list[dict]) -> tuple[set[str], set[str]]:
    expect(bool(lines), "No line records found.")

    line_ids = set()
    segment_ids = set()
    previous_order = 0

    for line in lines:
        missing = REQUIRED_LOOKUP_LINE_FIELDS - set(line)
        expect(not missing, f"Line {line.get('id', '<missing-id>')} missing fields: {sorted(missing)}")
        expect(line["id"] not in line_ids, f"Duplicate line id: {line['id']}")
        line_ids.add(line["id"])
        expect(line["order"] > previous_order, f"Line order not strictly increasing at {line['id']}")
        previous_order = line["order"]

        layer_keys = set(line["layers"])
        missing_layers = REQUIRED_LOOKUP_LAYERS - layer_keys
        expect(not missing_layers, f"Line {line['id']} missing layers: {sorted(missing_layers)}")

        for layer_name in REQUIRED_LOOKUP_LAYERS:
            expect(str(line["layers"][layer_name]).strip(), f"Line {line['id']} has empty layer: {layer_name}")

        locator = line["source_locator"]
        expect(locator["paragraph_index"] >= 0, f"Line {line['id']} has negative paragraph index.")
        expect(locator["chunk_index"] >= 0, f"Line {line['id']} has negative chunk index.")

        for segment in line.get("segments", []):
            missing_segment_fields = REQUIRED_LOOKUP_SEGMENT_FIELDS - set(segment)
            expect(
                not missing_segment_fields,
                f"Segment {segment.get('id', '<missing-id>')} missing fields: {sorted(missing_segment_fields)}",
            )
            expect(segment["id"] not in segment_ids, f"Duplicate segment id: {segment['id']}")
            segment_ids.add(segment["id"])
            expect(segment["source_start"] >= 0, f"Segment {segment['id']} has negative source_start.")
            expect(segment["source_end"] > segment["source_start"], f"Segment {segment['id']} has invalid source slice.")

    return line_ids, segment_ids


def verify_runtime_lines(lines: list[dict]) -> tuple[set[str], set[str]]:
    expect(bool(lines), "No runtime line records found.")

    line_ids = set()
    segment_ids = set()

    for line in lines:
        expect(line["id"] not in line_ids, f"Duplicate runtime line id: {line['id']}")
        line_ids.add(line["id"])

        layer_keys = set(line["layers"])
        missing_layers = REQUIRED_RUNTIME_LAYERS - layer_keys
        expect(not missing_layers, f"Runtime line {line['id']} missing layers: {sorted(missing_layers)}")

        for layer_name in REQUIRED_RUNTIME_LAYERS:
            expect(str(line["layers"][layer_name]).strip(), f"Runtime line {line['id']} has empty layer: {layer_name}")

        for segment in line.get("segments", []):
            expect(segment["id"] not in segment_ids, f"Duplicate runtime segment id: {segment['id']}")
            segment_ids.add(segment["id"])
            expect(str(segment["traditional"]).strip(), f"Runtime segment {segment['id']} missing traditional text.")
            expect(str(segment["simplified"]).strip(), f"Runtime segment {segment['id']} missing simplified text.")

    return line_ids, segment_ids


def verify_policy(policy: dict) -> set[str]:
    supported = set(policy["supported_layers"])
    expect(supported == REQUIRED_RUNTIME_LAYERS, "Supported flashcard layers do not match the six-layer model.")

    for pair in policy["default_priority_pairs"]:
        prompt = pair["prompt_layer"]
        answer = pair["answer_layer"]
        expect(prompt in supported, f"Unsupported prompt layer: {prompt}")
        expect(answer in supported, f"Unsupported answer layer: {answer}")
        expect(prompt != answer, f"Invalid same-layer flashcard pair: {prompt} -> {answer}")

    return supported


def verify_fixture(fixture: dict, line_ids: set[str], segment_ids: set[str], supported_layers: set[str]) -> None:
    for line_id in fixture["source"]["line_ids"]:
        expect(line_id in line_ids, f"Fixture references unknown line id: {line_id}")

    learner_questions = fixture.get("learner_questions", [])
    for question in learner_questions:
        expect(question["line_id"] in line_ids, f"Question references unknown line id: {question['line_id']}")
        if "segment_id" in question:
            expect(question["segment_id"] in segment_ids, f"Question references unknown segment id: {question['segment_id']}")

    card = fixture["expected_flashcard_entry"]
    for line_id in card.get("source_line_ids", []):
        expect(line_id in line_ids, f"Flashcard entry references unknown line id: {line_id}")
    for segment_id in card.get("source_segment_ids", []):
        expect(segment_id in segment_ids, f"Flashcard entry references unknown segment id: {segment_id}")

    prompt_layers = set(card["eligible_prompt_layers"])
    expect(prompt_layers.issubset(supported_layers), "Flashcard entry has unsupported prompt layers.")
    expect(bool(prompt_layers), "Flashcard entry must support at least one prompt layer.")

    missing_layers = REQUIRED_RUNTIME_LAYERS - set(card["layers"])
    expect(not missing_layers, f"Flashcard entry missing layers: {sorted(missing_layers)}")


def main() -> None:
    lookup = load_json(ANNOTATION_FILE)
    policy = load_json(POLICY_FILE)
    fixture = load_json(FIXTURE_FILE)

    work = verify_lookup_spec(lookup)
    line_ids, segment_ids = verify_lookup_lines(lookup["lines"])
    runtime_line_ids, runtime_segment_ids = verify_runtime_lines(load_lines(work))
    supported_layers = verify_policy(policy)
    expect(line_ids == runtime_line_ids, "Runtime lookup did not return the expected line ids.")
    expect(segment_ids == runtime_segment_ids, "Runtime lookup did not return the expected segment ids.")
    verify_fixture(fixture, runtime_line_ids, runtime_segment_ids, supported_layers)

    print("Starter data verification passed.")
    print(f"Verified {len(runtime_line_ids)} annotation-backed line records and {len(runtime_segment_ids)} segment records.")


if __name__ == "__main__":
    main()
