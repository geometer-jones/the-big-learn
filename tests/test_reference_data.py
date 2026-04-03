from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DATASET_PATH = (
    REPO_ROOT / "references" / "hanzi" / "modern-common-components-gf0014-2009-grouped.json"
)


class ReferenceDataTests(unittest.TestCase):
    def test_grouped_component_dataset_has_expected_counts(self) -> None:
        payload = json.loads(COMPONENT_DATASET_PATH.read_text(encoding="utf-8"))

        self.assertEqual(payload["standard"], "GF 0014-2009")
        self.assertEqual(payload["grouped_component_count"], 441)
        self.assertEqual(payload["raw_component_count"], 514)
        self.assertEqual(payload["default_sort_field"], "group_occurrence_count")
        self.assertEqual(payload["default_sort_direction"], "descending")
        self.assertEqual(payload["default_page_size"], 100)
        self.assertIn("ties broken by ascending group_id", payload["sort_note"])
        self.assertIn("source example characters", payload["presentation_note"])

        entries = payload["entries"]
        self.assertEqual(len(entries), 441)
        self.assertEqual([entry["group_id"] for entry in entries], list(range(1, 442)))
        self.assertEqual(sum(len(entry["members"]) for entry in entries), 514)

    def test_grouped_component_dataset_keeps_variants_under_one_entry(self) -> None:
        payload = json.loads(COMPONENT_DATASET_PATH.read_text(encoding="utf-8"))

        for entry in payload["entries"]:
            members = entry["members"]
            self.assertGreaterEqual(len(members), 1)
            self.assertEqual(entry["canonical_form"], members[0]["form"])
            self.assertEqual(entry["canonical_name"], members[0]["short_name"])
            self.assertEqual(entry["forms"], [member["form"] for member in members])
            self.assertEqual(entry["variant_forms"], [member["form"] for member in members[1:]])
            self.assertEqual(entry["names"], [member["short_name"] for member in members])
            self.assertGreaterEqual(len(entry["source_example_characters"]), 1)
            seen_examples: list[str] = []
            for member in members:
                for char in member["source_example_characters"]:
                    if char not in seen_examples:
                        seen_examples.append(char)
            self.assertEqual(entry["source_example_characters"], seen_examples)
            for member in members:
                self.assertIn("source_examples_text", member)
                self.assertIn("source_example_characters", member)
                self.assertEqual(member["source_example_characters"], list(member["source_examples_text"]))

    def test_grouped_component_dataset_exposes_frequency_ranks(self) -> None:
        payload = json.loads(COMPONENT_DATASET_PATH.read_text(encoding="utf-8"))

        entries = payload["entries"]
        self.assertTrue(all("frequency_rank" in entry for entry in entries))
        self.assertTrue(all("group_occurrence_count" in entry for entry in entries))
        self.assertTrue(all("group_construction_count" in entry for entry in entries))

        ranked_entries = sorted(entries, key=lambda entry: entry["frequency_rank"])
        self.assertEqual(
            [entry["canonical_form"] for entry in ranked_entries[:10]],
            ["口", "人", "日", "木", "水", "手", "月", "一", "艹", "土"],
        )
        self.assertEqual(
            [entry["group_occurrence_count"] for entry in ranked_entries[:5]],
            [581, 378, 244, 238, 231],
        )
        self.assertEqual(
            [entry["frequency_rank"] for entry in ranked_entries],
            list(range(1, 442)),
        )


if __name__ == "__main__":
    unittest.main()
