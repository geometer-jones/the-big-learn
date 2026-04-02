from __future__ import annotations

import configparser
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from . import __version__


ROOT_ENV_VAR = "THE_BIG_LEARN_ROOT"
STATE_DIR_ENV_VAR = "THE_BIG_LEARN_STATE_DIR"
REMOTE_URL_ENV_VAR = "THE_BIG_LEARN_REMOTE_VERSION_URL"

UPDATE_CHECK_KEY = "update_check"
REMOTE_VERSION_URL_KEY = "remote_version_url"
KNOWN_CONFIG_KEYS = {UPDATE_CHECK_KEY, REMOTE_VERSION_URL_KEY}

UP_TO_DATE = "UP_TO_DATE"
UPGRADE_AVAILABLE = "UPGRADE_AVAILABLE"
JUST_UPGRADED = "JUST_UPGRADED"

UP_TO_DATE_TTL_SECONDS = 60 * 60
UPGRADE_AVAILABLE_TTL_SECONDS = 12 * 60 * 60
VERSION_PATTERN = re.compile(r"^\d+\.\d+(?:\.\d+)*$")


@dataclass(frozen=True)
class UpdateResult:
    status: str
    local_version: str
    remote_version: str | None = None
    previous_version: str | None = None

    def output_line(self) -> str:
        if self.status == JUST_UPGRADED:
            if not self.previous_version:
                raise ValueError("JUST_UPGRADED results require previous_version.")
            return f"{JUST_UPGRADED} {self.previous_version} {self.local_version}"
        if self.status == UPGRADE_AVAILABLE:
            if not self.remote_version:
                raise ValueError("UPGRADE_AVAILABLE results require remote_version.")
            return f"{UPGRADE_AVAILABLE} {self.local_version} {self.remote_version}"
        raise ValueError(f"Unsupported output status: {self.status}")


def repository_root() -> Path:
    override = os.environ.get(ROOT_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def state_dir() -> Path:
    override = os.environ.get(STATE_DIR_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".the-big-learn").resolve()


def config_path() -> Path:
    return state_dir() / "config.json"


def cache_path() -> Path:
    return state_dir() / "last-update-check.json"


def snooze_path() -> Path:
    return state_dir() / "update-snoozed.json"


def installed_version_path() -> Path:
    return state_dir() / "installed-version"


def read_local_version() -> str:
    return __version__.strip()


def ensure_state_dir() -> Path:
    path = state_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    ensure_state_dir()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_config() -> dict[str, Any]:
    return _read_json_file(config_path())


def _parse_config_value(raw_value: str) -> Any:
    lowered = raw_value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    return raw_value


def config_value_to_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def get_config_value(key: str) -> Any:
    if key not in KNOWN_CONFIG_KEYS:
        raise ValueError(f"Unknown config key: {key}")
    return load_config().get(key)


def set_config_value(key: str, raw_value: str) -> dict[str, Any]:
    if key not in KNOWN_CONFIG_KEYS:
        raise ValueError(f"Unknown config key: {key}")

    config = load_config()
    parsed_value = _parse_config_value(raw_value)
    if parsed_value is None:
        config.pop(key, None)
    else:
        config[key] = parsed_value
    _write_json_file(config_path(), config)
    return config


def update_checks_enabled() -> bool:
    return get_config_value(UPDATE_CHECK_KEY) is not False


def write_snooze(version: str, level: int) -> None:
    _write_json_file(
        snooze_path(),
        {
            "version": version,
            "level": max(1, level),
            "snoozed_at": int(time.time()),
        },
    )


def clear_snooze() -> None:
    try:
        snooze_path().unlink()
    except FileNotFoundError:
        pass


def _snooze_duration_seconds(level: int) -> int:
    if level <= 1:
        return 24 * 60 * 60
    if level == 2:
        return 48 * 60 * 60
    return 7 * 24 * 60 * 60


def snoozed_for_version(version: str) -> bool:
    payload = _read_json_file(snooze_path())
    if payload.get("version") != version:
        return False

    level = payload.get("level")
    snoozed_at = payload.get("snoozed_at")
    if not isinstance(level, int) or not isinstance(snoozed_at, int):
        return False

    return int(time.time()) < snoozed_at + _snooze_duration_seconds(level)


def _read_seen_version() -> str | None:
    try:
        payload = installed_version_path().read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    return payload or None


def _write_seen_version(version: str) -> None:
    ensure_state_dir()
    installed_version_path().write_text(version + "\n", encoding="utf-8")


def _ttl_for_status(status: str) -> int:
    if status == UP_TO_DATE:
        return UP_TO_DATE_TTL_SECONDS
    if status == UPGRADE_AVAILABLE:
        return UPGRADE_AVAILABLE_TTL_SECONDS
    return 0


def _load_cache() -> dict[str, Any]:
    return _read_json_file(cache_path())


def _write_cache(status: str, local_version: str, remote_version: str) -> None:
    _write_json_file(
        cache_path(),
        {
            "status": status,
            "local_version": local_version,
            "remote_version": remote_version,
            "checked_at": int(time.time()),
        },
    )


def _fresh_cache_for_local_version(local_version: str) -> dict[str, Any] | None:
    payload = _load_cache()
    status = payload.get("status")
    checked_at = payload.get("checked_at")
    cached_local = payload.get("local_version")
    cached_remote = payload.get("remote_version")
    if not isinstance(status, str) or not isinstance(checked_at, int):
        return None
    if cached_local != local_version or not isinstance(cached_remote, str):
        return None

    ttl = _ttl_for_status(status)
    if ttl <= 0:
        return None
    if int(time.time()) >= checked_at + ttl:
        return None
    return payload


def _clear_cache() -> None:
    try:
        cache_path().unlink()
    except FileNotFoundError:
        pass


def _resolve_git_dir(root: Path) -> Path | None:
    git_entry = root / ".git"
    if git_entry.is_dir():
        return git_entry
    if not git_entry.is_file():
        return None

    content = git_entry.read_text(encoding="utf-8").strip()
    if not content.startswith("gitdir:"):
        return None
    return (root / content.split(":", 1)[1].strip()).resolve()


def _read_git_origin_url(root: Path) -> str | None:
    git_dir = _resolve_git_dir(root)
    if git_dir is None:
        return None

    parser = configparser.ConfigParser()
    try:
        parser.read(git_dir / "config", encoding="utf-8")
    except configparser.Error:
        return None

    section = 'remote "origin"'
    if not parser.has_option(section, "url"):
        return None
    return parser.get(section, "url").strip()


def _read_default_branch(root: Path) -> str:
    git_dir = _resolve_git_dir(root)
    if git_dir is None:
        return "main"

    head_file = git_dir / "refs" / "remotes" / "origin" / "HEAD"
    try:
        content = head_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "main"

    marker = "refs/remotes/origin/"
    if marker not in content:
        return "main"
    branch = content.split(marker, 1)[1].strip()
    return branch or "main"


def _github_owner_repo(remote_url: str) -> tuple[str, str] | None:
    patterns = [
        r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
        r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
        r"^ssh://git@github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, remote_url)
        if match:
            return match.group("owner"), match.group("repo")
    return None


def infer_remote_version_url(root: Path | None = None) -> str | None:
    env_override = os.environ.get(REMOTE_URL_ENV_VAR)
    if env_override:
        return env_override.strip()

    configured = get_config_value(REMOTE_VERSION_URL_KEY)
    if isinstance(configured, str) and configured.strip():
        return configured.strip()

    candidate_root = root or repository_root()
    origin_url = _read_git_origin_url(candidate_root)
    if not origin_url:
        return None

    owner_repo = _github_owner_repo(origin_url)
    if owner_repo is None:
        return None

    owner, repo = owner_repo
    branch = _read_default_branch(candidate_root)
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/VERSION"


def _fetch_remote_version(remote_url: str) -> str | None:
    try:
        with urlopen(remote_url, timeout=5) as response:
            payload = response.read().decode("utf-8").strip()
    except (OSError, URLError, ValueError):
        return None
    if not VERSION_PATTERN.match(payload):
        return None
    return payload


def check_for_updates(force: bool = False) -> UpdateResult | None:
    local_version = read_local_version()
    if not local_version:
        return None

    if force:
        _clear_cache()
        clear_snooze()

    enabled = update_checks_enabled()
    previous_version = _read_seen_version()
    if previous_version is None:
        _write_seen_version(local_version)
    elif previous_version != local_version:
        _write_seen_version(local_version)
        clear_snooze()
        if not enabled:
            return None
        _write_cache(UP_TO_DATE, local_version, local_version)
        return UpdateResult(
            status=JUST_UPGRADED,
            local_version=local_version,
            remote_version=local_version,
            previous_version=previous_version,
        )

    if not enabled:
        return None

    cached = _fresh_cache_for_local_version(local_version)
    if cached:
        if cached["status"] == UP_TO_DATE:
            return None
        remote_version = cached["remote_version"]
        if snoozed_for_version(remote_version):
            return None
        return UpdateResult(status=UPGRADE_AVAILABLE, local_version=local_version, remote_version=remote_version)

    remote_url = infer_remote_version_url()
    if not remote_url:
        return None

    remote_version = _fetch_remote_version(remote_url)
    if remote_version is None:
        _write_cache(UP_TO_DATE, local_version, local_version)
        return None

    if remote_version == local_version:
        _write_cache(UP_TO_DATE, local_version, remote_version)
        return None

    _write_cache(UPGRADE_AVAILABLE, local_version, remote_version)
    if snoozed_for_version(remote_version):
        return None
    return UpdateResult(status=UPGRADE_AVAILABLE, local_version=local_version, remote_version=remote_version)
