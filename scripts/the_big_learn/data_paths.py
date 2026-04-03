from __future__ import annotations

from pathlib import Path

from .updates import repository_root


BUNDLE_DIRNAME = "bundle"
BOOKS_DIRNAME = "books"
LEGACY_BOOKS_DIRNAME = "source-store"


def package_root() -> Path:
    return Path(__file__).resolve().parent


def bundled_data_root() -> Path:
    return package_root() / BUNDLE_DIRNAME


def candidate_books_dirs(root: Path) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(root / dirname for dirname in (BOOKS_DIRNAME, LEGACY_BOOKS_DIRNAME)))


def preferred_books_dir(root: Path) -> Path:
    for candidate in candidate_books_dirs(root):
        if candidate.exists():
            return candidate
    return root / BOOKS_DIRNAME


def data_root() -> Path:
    root = repository_root()
    if any(candidate.exists() for candidate in candidate_books_dirs(root)):
        return root

    bundled = bundled_data_root()
    if any(candidate.exists() for candidate in candidate_books_dirs(bundled)):
        return bundled

    return root
