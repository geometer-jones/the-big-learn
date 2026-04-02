from __future__ import annotations

import shutil
from pathlib import Path

from .data_paths import data_root

ROOT = data_root()
REPO_SKILLS_DIR = ROOT / "skills"
CODEX_HOST_SKILLS_DIR = ROOT / "hosts" / "codex" / "skills"
DEFAULT_CODEX_SKILLS_HOME = Path.home() / ".codex" / "skills"


def default_codex_target() -> Path:
    return DEFAULT_CODEX_SKILLS_HOME


def _codex_skill_name(source_dir: Path) -> str:
    if source_dir.name.startswith("the-big-learn-"):
        return source_dir.name
    return f"the-big-learn-{source_dir.name}"


def source_skill_dirs() -> list[Path]:
    directories: list[Path] = []

    if CODEX_HOST_SKILLS_DIR.exists():
        directories.extend(
            sorted(path for path in CODEX_HOST_SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists())
        )

    if REPO_SKILLS_DIR.exists():
        directories.extend(
            sorted(path for path in REPO_SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists())
        )

    return directories


def install_codex_skills(target: Path | None = None, force: bool = False) -> list[Path]:
    resolved_target = (target or default_codex_target()).expanduser()
    resolved_target.mkdir(parents=True, exist_ok=True)

    installed_paths: list[Path] = []
    for source_dir in source_skill_dirs():
        destination = resolved_target / _codex_skill_name(source_dir)
        if destination.exists():
            if not force:
                raise FileExistsError(
                    f"Destination already exists: {destination}. Use --force to replace existing Codex skills."
                )
            shutil.rmtree(destination)
        shutil.copytree(source_dir, destination)
        installed_paths.append(destination)

    return installed_paths
