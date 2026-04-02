from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = list((ROOT / "skills").glob("*/SKILL.md"))
PREFIX = "the-big-learn-"


def read_skill_name(skill_file: Path) -> str:
    for line in skill_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("name: "):
            return line.removeprefix("name: ").strip()
    raise AssertionError(f"Missing skill name in {skill_file}")


class SkillMetadataTests(unittest.TestCase):
    def test_repo_skills_use_the_big_learn_prefix(self) -> None:
        self.assertTrue(SKILL_FILES, "Expected repo skill definitions under skills/")

        for skill_file in SKILL_FILES:
            with self.subTest(skill=skill_file.parent.name):
                self.assertTrue(read_skill_name(skill_file).startswith(PREFIX))

    def test_repo_skills_use_workspace_files_instead_of_runtime_commands(self) -> None:
        for skill_file in SKILL_FILES:
            with self.subTest(skill=skill_file.parent.name):
                content = skill_file.read_text(encoding="utf-8")
                self.assertIn("No startup command is required.", content)

    def test_update_skill_targets_package_updates(self) -> None:
        content = (ROOT / "skills" / "update" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("python3 -m the_big_learn update-check --force", content)
        self.assertIn("git pull --ff-only origin <default-branch>", content)
        self.assertIn("python3 -m the_big_learn claude install --force", content)
        self.assertIn("deleted skills can linger", content)
        self.assertNotIn("Learner Translation Log", content)
        self.assertNotIn("queued questions", content)

    def test_flashcard_repo_skills_call_flashcard_persistence_command(self) -> None:
        bank_add = (ROOT / "skills" / "flashcard-bank-add" / "SKILL.md").read_text(encoding="utf-8")
        review = (ROOT / "skills" / "flashcard-review" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("python3 -m the_big_learn flashcard-save --format json", bank_add)
        self.assertIn("~/.the-big-learn/flashcards/bank/", bank_add)
        self.assertIn("translation_en` may legitimately be identical to `gloss_en`", bank_add)
        self.assertIn("python3 -m the_big_learn flashcard-review --format json", review)
        self.assertIn("weight = 10 * significance_flag_count + occurrence_count", review)
        self.assertIn("~/.the-big-learn/flashcards/review-state.json", review)

    def test_explode_char_uses_simplified_primary_display(self) -> None:
        content = (ROOT / "skills" / "explode-char" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "show the simplified form in the primary position and append the traditional form in parentheses only when it differs",
            content,
        )
        self.assertIn(
            "keep simplified primary at every node and append traditional in parentheses only when it differs",
            content,
        )
        self.assertIn(
            "do not end the exploder with flashcard save suggestions or candidate lists",
            content,
        )
        self.assertIn(
            "show a short `## Simplified | Traditional` block before `## Analysis`",
            content,
        )
        self.assertIn(
            "make `## Definition` the first visible section of the explosion",
            content,
        )
        self.assertIn(
            "Lead with a compact definition block before any script note or decomposition",
            content,
        )
        self.assertIn(
            "Place the meaning map after structural analysis and synthesis",
            content,
        )
        self.assertIn(
            "if the learner came from guided reading, end with a short return cue",
            content,
        )
        self.assertIn(
            "keep it inline as `pinyin (zhuyin)` rather than splitting pinyin and zhuyin into separate lines",
            content,
        )
        self.assertIn(
            "Do not print separate pinyin or Zhuyin lines in the synthesis subsections.",
            content,
        )
        self.assertIn(
            "Do not stop after same-tone matches when honest different-tone homophones are available.",
            content,
        )
        self.assertIn("#### Different Tone", content)
        self.assertLess(
            content.index("2. `## Definition`"),
            content.index("3. `## Simplified | Traditional`"),
        )
        self.assertLess(
            content.index("4. `## Analysis`"),
            content.index("5. `## Synthesis`"),
        )
        self.assertLess(
            content.index("6. `## Meaning Map`"),
            content.index("## Rules"),
        )
        self.assertLess(
            content.index("1. `### Containing Characters`"),
            content.index("2. `### Phrase Use`"),
        )
        self.assertLess(
            content.index("1. `#### Same Tone`"),
            content.index("2. `#### Different Tone`"),
        )
        self.assertLess(
            content.index("3. `### Homophones`"),
            content.index("### Meaning Map"),
        )
        self.assertNotIn("### Flashcard Candidates", content)
        self.assertNotIn(
            "show the traditional form as the decomposition root and list the simplified form alongside it",
            content,
        )
        self.assertNotIn(
            "always print both script forms at every node so the learner can compare them directly",
            content,
        )
        self.assertNotIn(
            "Do not print a Zhuyin line under `#### Synonyms`.",
            content,
        )
        self.assertNotIn("the-big-learn-flashcard-bank-add", content)


if __name__ == "__main__":
    unittest.main()
