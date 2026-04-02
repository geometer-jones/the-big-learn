from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from the_big_learn import __version__
from the_big_learn.updates import (
    JUST_UPGRADED,
    UPGRADE_AVAILABLE,
    UP_TO_DATE,
    check_for_updates,
    infer_remote_version_url,
    load_config,
    set_config_value,
    snooze_path,
    update_checks_enabled,
    write_snooze,
)


class UpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "repo"
        self.root.mkdir(parents=True)
        self.state = Path(self.temp_dir.name) / "state"

        self.old_environ = {
            "THE_BIG_LEARN_ROOT": os.environ.get("THE_BIG_LEARN_ROOT"),
            "THE_BIG_LEARN_STATE_DIR": os.environ.get("THE_BIG_LEARN_STATE_DIR"),
            "THE_BIG_LEARN_REMOTE_VERSION_URL": os.environ.get("THE_BIG_LEARN_REMOTE_VERSION_URL"),
        }
        os.environ["THE_BIG_LEARN_ROOT"] = str(self.root)
        os.environ["THE_BIG_LEARN_STATE_DIR"] = str(self.state)
        os.environ.pop("THE_BIG_LEARN_REMOTE_VERSION_URL", None)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        for key, value in self.old_environ.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _set_remote_version(self, version: str) -> None:
        remote_file = self.root / "REMOTE_VERSION"
        remote_file.write_text(version + "\n", encoding="utf-8")
        os.environ["THE_BIG_LEARN_REMOTE_VERSION_URL"] = remote_file.resolve().as_uri()

    def _cache_payload(self) -> dict:
        return json.loads((self.state / "last-update-check.json").read_text(encoding="utf-8"))

    def test_root_version_file_matches_package_version(self) -> None:
        version_file = Path(__file__).resolve().parent.parent / "VERSION"
        self.assertEqual(version_file.read_text(encoding="utf-8").strip(), __version__)

    def test_update_check_is_silent_when_no_remote_source_is_available(self) -> None:
        result = check_for_updates()
        self.assertIsNone(result)
        self.assertFalse((self.state / "last-update-check.json").exists())

    def test_update_check_returns_upgrade_available_when_remote_version_differs(self) -> None:
        self._set_remote_version("0.2.0")

        result = check_for_updates()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, UPGRADE_AVAILABLE)
        self.assertEqual(result.output_line(), f"UPGRADE_AVAILABLE {__version__} 0.2.0")
        self.assertEqual(self._cache_payload()["status"], UPGRADE_AVAILABLE)

    def test_update_check_is_silent_when_remote_version_matches(self) -> None:
        self._set_remote_version(__version__)

        result = check_for_updates()

        self.assertIsNone(result)
        payload = self._cache_payload()
        self.assertEqual(payload["status"], UP_TO_DATE)
        self.assertEqual(payload["remote_version"], __version__)

    def test_update_check_respects_disabled_config(self) -> None:
        set_config_value("update_check", "false")
        self._set_remote_version("0.2.0")

        result = check_for_updates()

        self.assertIsNone(result)
        self.assertFalse((self.state / "last-update-check.json").exists())
        self.assertFalse(update_checks_enabled())

    def test_update_check_uses_fresh_upgrade_cache(self) -> None:
        self._set_remote_version("0.2.0")
        first = check_for_updates()
        self.assertIsNotNone(first)

        remote_file = self.root / "REMOTE_VERSION"
        remote_file.write_text(__version__ + "\n", encoding="utf-8")

        second = check_for_updates()
        self.assertIsNotNone(second)
        self.assertEqual(second.output_line(), f"UPGRADE_AVAILABLE {__version__} 0.2.0")

    def test_force_busts_cache_and_snooze(self) -> None:
        self._set_remote_version("0.2.0")
        self.assertIsNotNone(check_for_updates())
        write_snooze("0.2.0", 1)

        remote_file = self.root / "REMOTE_VERSION"
        remote_file.write_text(__version__ + "\n", encoding="utf-8")

        forced = check_for_updates(force=True)
        self.assertIsNone(forced)
        self.assertEqual(self._cache_payload()["status"], UP_TO_DATE)
        self.assertFalse(snooze_path().exists())

    def test_snoozed_upgrade_is_silent(self) -> None:
        self._set_remote_version("0.2.0")
        write_snooze("0.2.0", 1)

        result = check_for_updates()

        self.assertIsNone(result)
        self.assertEqual(self._cache_payload()["status"], UPGRADE_AVAILABLE)

    def test_expired_snooze_reprompts(self) -> None:
        self._set_remote_version("0.2.0")
        write_snooze("0.2.0", 1)

        payload = json.loads(snooze_path().read_text(encoding="utf-8"))
        payload["snoozed_at"] = int(time.time()) - (25 * 60 * 60)
        snooze_path().write_text(json.dumps(payload), encoding="utf-8")

        result = check_for_updates()

        self.assertIsNotNone(result)
        self.assertEqual(result.output_line(), f"UPGRADE_AVAILABLE {__version__} 0.2.0")

    def test_local_version_change_emits_just_upgraded(self) -> None:
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "installed-version").write_text("0.0.9\n", encoding="utf-8")
        self._set_remote_version("0.2.0")

        result = check_for_updates()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, JUST_UPGRADED)
        self.assertEqual(result.output_line(), f"JUST_UPGRADED 0.0.9 {__version__}")
        self.assertEqual(self._cache_payload()["status"], UP_TO_DATE)

    def test_config_list_round_trips_known_keys(self) -> None:
        set_config_value("update_check", "false")
        set_config_value("remote_version_url", "https://example.com/VERSION")

        self.assertEqual(
            load_config(),
            {
                "remote_version_url": "https://example.com/VERSION",
                "update_check": False,
            },
        )

    def test_infer_remote_version_url_from_git_origin(self) -> None:
        git_dir = self.root / ".git"
        (git_dir / "refs" / "remotes" / "origin").mkdir(parents=True)
        (git_dir / "config").write_text(
            '[remote "origin"]\n\turl = git@github.com:example/the-big-learn.git\n',
            encoding="utf-8",
        )
        (git_dir / "refs" / "remotes" / "origin" / "HEAD").write_text(
            "ref: refs/remotes/origin/main\n",
            encoding="utf-8",
        )

        self.assertEqual(
            infer_remote_version_url(self.root),
            "https://raw.githubusercontent.com/example/the-big-learn/main/VERSION",
        )


if __name__ == "__main__":
    unittest.main()
