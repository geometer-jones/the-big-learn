from __future__ import annotations

import shutil
from pathlib import Path

from .data_paths import data_root

ROOT = data_root()
GEMINI_HOST_COMMANDS_DIR = ROOT / "hosts" / "gemini" / "commands"
DEFAULT_GEMINI_COMMANDS_HOME = Path.home() / ".gemini" / "commands"


def default_gemini_target() -> Path:
    return DEFAULT_GEMINI_COMMANDS_HOME


def install_gemini_commands(target: Path | None = None, force: bool = False) -> list[Path]:
    resolved_target = (target or default_gemini_target()).expanduser()
    resolved_target.mkdir(parents=True, exist_ok=True)

    installed_paths: list[Path] = []
    if not GEMINI_HOST_COMMANDS_DIR.exists():
        return installed_paths

    for source_dir in sorted(path for path in GEMINI_HOST_COMMANDS_DIR.iterdir() if path.is_dir()):
        destination = resolved_target / source_dir.name
        if destination.exists():
            if not force:
                raise FileExistsError(
                    f"Destination already exists: {destination}. Use --force to replace existing Gemini commands."
                )
            shutil.rmtree(destination)
        shutil.copytree(source_dir, destination)
        installed_paths.append(destination)

    return installed_paths
