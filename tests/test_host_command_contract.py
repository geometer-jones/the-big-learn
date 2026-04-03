from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOST_ROOT = ROOT / "hosts"
COMMAND_PATTERN = re.compile(r"python3 -m the_big_learn (?P<command>[a-z-]+)(?: (?P<subcommand>[a-z-]+))?")
ALLOWED_TOP_LEVEL_COMMANDS = {"source", "progress-save", "flashcard-save", "flashcard-review"}
ALLOWED_SOURCE_SUBCOMMANDS = {"catalog", "read"}


class HostCommandContractTests(unittest.TestCase):
    def test_host_assets_only_reference_supported_python_commands(self) -> None:
        referenced_commands: list[tuple[Path, str, str | None]] = []
        for path in HOST_ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".toml"}:
                continue
            content = path.read_text(encoding="utf-8")
            for match in COMMAND_PATTERN.finditer(content):
                referenced_commands.append((path, match.group("command"), match.group("subcommand")))

        self.assertTrue(referenced_commands, "Expected host assets to reference the Python host-support CLI.")

        for path, command, subcommand in referenced_commands:
            with self.subTest(path=path, command=command, subcommand=subcommand):
                self.assertIn(command, ALLOWED_TOP_LEVEL_COMMANDS)
                if command == "source":
                    self.assertIn(subcommand, ALLOWED_SOURCE_SUBCOMMANDS)


if __name__ == "__main__":
    unittest.main()
