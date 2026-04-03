from __future__ import annotations

import tempfile
import unittest
from unittest import mock
from pathlib import Path

from the_big_learn.bootstrap import (
    editable_install_command,
    host_install_command,
    infer_host,
    is_externally_managed_environment,
    main,
    running_in_virtualenv,
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

    def test_editable_install_command_uses_break_system_packages_when_requested(self) -> None:
        command = editable_install_command(
            Path("/tmp/the-big-learn"),
            executable="python3",
            in_virtualenv=False,
            break_system_packages=True,
        )
        self.assertEqual(
            command,
            ["python3", "-m", "pip", "install", "--user", "--break-system-packages", "-e", "/tmp/the-big-learn"],
        )

    def test_host_install_command_uses_module_invocation(self) -> None:
        self.assertEqual(
            host_install_command("claude", executable="python3"),
            ["python3", "-m", "the_big_learn", "claude", "install", "--force"],
        )

    def test_running_in_virtualenv_checks_base_prefix(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch("sys.prefix", "/tmp/venv"), mock.patch("sys.base_prefix", "/usr"):
                self.assertTrue(running_in_virtualenv())

    def test_is_externally_managed_environment_detects_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "EXTERNALLY-MANAGED").write_text("", encoding="utf-8")
            self.assertTrue(is_externally_managed_environment(in_virtualenv=False, stdlib_path=tmpdir))

    def test_is_externally_managed_environment_ignores_marker_inside_virtualenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "EXTERNALLY-MANAGED").write_text("", encoding="utf-8")
            self.assertFalse(is_externally_managed_environment(in_virtualenv=True, stdlib_path=tmpdir))

    def test_main_uses_break_system_packages_on_externally_managed_python(self) -> None:
        repo_root = Path("/tmp/the-big-learn")
        with mock.patch("builtins.print"):
            with mock.patch("the_big_learn.bootstrap.repository_root", return_value=repo_root):
                with mock.patch("the_big_learn.bootstrap.running_in_virtualenv", return_value=False):
                    with mock.patch("the_big_learn.bootstrap.is_externally_managed_environment", return_value=True):
                        with mock.patch("the_big_learn.bootstrap._run") as run:
                            self.assertEqual(main(["claude"]), 0)

        self.assertEqual(
            run.call_args_list[0].args[0],
            [
                mock.ANY,
                "-m",
                "pip",
                "install",
                "--user",
                "--break-system-packages",
                "-e",
                "/tmp/the-big-learn",
            ],
        )
        self.assertEqual(run.call_args_list[1].args[0][-4:], ["the_big_learn", "claude", "install", "--force"])


if __name__ == "__main__":
    unittest.main()
