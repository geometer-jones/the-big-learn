from __future__ import annotations

import shutil
from pathlib import Path

from .data_paths import data_root

ROOT = data_root()
REPO_SKILLS_DIR = ROOT / "skills"
CLAUDE_HOST_SKILLS_DIR = ROOT / "hosts" / "claude" / "skills"
DEFAULT_CLAUDE_SKILLS_HOME = Path.home() / ".claude" / "skills"
SKILL_PREFIX = "the-big-learn-"


def default_claude_target() -> Path:
    return DEFAULT_CLAUDE_SKILLS_HOME


def _claude_skill_name(source_dir: Path) -> str:
    if source_dir.name.startswith(SKILL_PREFIX):
        return source_dir.name
    return f"{SKILL_PREFIX}{source_dir.name}"


def source_skill_dirs() -> list[Path]:
    directories: list[Path] = []

    if CLAUDE_HOST_SKILLS_DIR.exists():
        directories.extend(
            sorted(path for path in CLAUDE_HOST_SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists())
        )

    if REPO_SKILLS_DIR.exists():
        directories.extend(
            sorted(path for path in REPO_SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists())
        )

    return directories


def _remove_existing_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


def _remove_stale_claude_skills(target: Path, expected_names: set[str]) -> None:
    for path in target.iterdir():
        if not path.name.startswith(SKILL_PREFIX):
            continue
        if path.name in expected_names:
            continue
        _remove_existing_path(path)


def install_claude_skills(target: Path | None = None, force: bool = False) -> list[Path]:
    resolved_target = (target or default_claude_target()).expanduser()
    resolved_target.mkdir(parents=True, exist_ok=True)
    expected_names = {_claude_skill_name(source_dir) for source_dir in source_skill_dirs()}

    if force:
        _remove_stale_claude_skills(resolved_target, expected_names)

    installed_paths: list[Path] = []
    for source_dir in source_skill_dirs():
        destination = resolved_target / _claude_skill_name(source_dir)
        if destination.exists():
            if not force:
                raise FileExistsError(
                    f"Destination already exists: {destination}. Use --force to replace existing Claude Code skills."
                )
            _remove_existing_path(destination)
        shutil.copytree(source_dir, destination)
        installed_paths.append(destination)

    return installed_paths
