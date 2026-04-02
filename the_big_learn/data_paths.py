from __future__ import annotations

from pathlib import Path

from .updates import repository_root


BUNDLE_DIRNAME = "bundle"


def package_root() -> Path:
    return Path(__file__).resolve().parent


def bundled_data_root() -> Path:
    return package_root() / BUNDLE_DIRNAME


def data_root() -> Path:
    root = repository_root()
    if (root / "annotations").exists():
        return root

    bundled = bundled_data_root()
    if bundled.exists():
        return bundled

    return root
