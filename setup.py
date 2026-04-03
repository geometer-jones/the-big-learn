from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py as _build_py


ROOT = Path(__file__).resolve().parent
BUNDLE_DIRNAME = "bundle"
BUNDLED_ASSET_PATHS = [
    "evals",
    "flashcards",
    "hosts",
    "references",
    "skills",
    "books",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "CURRICULUM.md",
    "DESIGN.md",
    "PRODUCT.md",
    "README.md",
    "README_RUNTIME.md",
]


class build_py(_build_py):
    def run(self) -> None:
        super().run()

        bundle_root = Path(self.build_lib) / "the_big_learn" / BUNDLE_DIRNAME
        if bundle_root.exists():
            shutil.rmtree(bundle_root)
        bundle_root.mkdir(parents=True, exist_ok=True)

        for relative_path in BUNDLED_ASSET_PATHS:
            source = ROOT / relative_path
            destination = bundle_root / relative_path
            if not source.exists():
                continue

            if source.is_dir():
                shutil.copytree(source, destination)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)


setup(
    name="the-big-learn",
    version="0.3.2",
    description="Open-source agent skill pack and runtime for learning Chinese inside coding assistants.",
    packages=find_packages(where="scripts", include=["the_big_learn", "the_big_learn.*"]),
    package_dir={"": "scripts"},
    cmdclass={"build_py": build_py},
    entry_points={
        "console_scripts": [
            "the-big-learn=the_big_learn.cli:main",
        ]
    },
    python_requires=">=3.9",
)
