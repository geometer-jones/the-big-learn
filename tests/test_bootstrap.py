from __future__ import annotations

import unittest
from pathlib import Path

from the_big_learn.bootstrap import (
    editable_install_command,
    host_install_command,
    infer_host,
)


class BootstrapTests(unittest.TestCase):
    def test_infer_host_prefers_checkout_parent(self) -> None:
        home = Path("/tmp/home")
        self.assertEqual(infer_host(home / ".claude" / "skills" / "the-big-learn", home=home), "claude")
        self.assertEqual(infer_host(home / ".codex" / "skills" / "the-big-learn", home=home), "codex")
        self.assertEqual(infer_host(home / ".gemini" / "commands" / "the-big-learn", home=home), "gemini")

    def test_infer_host_defaults_to_claude(self) -> None:
        home = Path("/tmp/home")
        self.assertEqual(infer_host(home / "src" / "the-big-learn", home=home), "claude")

    def test_editable_install_command_uses_user_site_outside_virtualenv(self) -> None:
        command = editable_install_command(Path("/tmp/the-big-learn"), executable="python3", in_virtualenv=False)
        self.assertEqual(command, ["python3", "-m", "pip", "install", "--user", "-e", "/tmp/the-big-learn"])

    def test_editable_install_command_omits_user_inside_virtualenv(self) -> None:
        command = editable_install_command(Path("/tmp/the-big-learn"), executable="python3", in_virtualenv=True)
        self.assertEqual(command, ["python3", "-m", "pip", "install", "-e", "/tmp/the-big-learn"])

    def test_host_install_command_uses_module_invocation(self) -> None:
        self.assertEqual(
            host_install_command("claude", executable="python3"),
            ["python3", "-m", "the_big_learn", "claude", "install", "--force"],
        )


if __name__ == "__main__":
    unittest.main()
