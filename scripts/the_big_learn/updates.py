from __future__ import annotations

import os
from pathlib import Path


ROOT_ENV_VAR = "THE_BIG_LEARN_ROOT"
STATE_DIR_ENV_VAR = "THE_BIG_LEARN_STATE_DIR"


def _discover_repository_root() -> Path:
    package_file = Path(__file__).resolve()
    for candidate in package_file.parents:
        if (candidate / "pyproject.toml").exists() and (candidate / "setup.py").exists():
            return candidate
    return package_file.parent.parent


def repository_root() -> Path:
    override = os.environ.get(ROOT_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    return _discover_repository_root()


def state_dir() -> Path:
    override = os.environ.get(STATE_DIR_ENV_VAR)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".the-big-learn").resolve()


def ensure_state_dir() -> Path:
    path = state_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path
