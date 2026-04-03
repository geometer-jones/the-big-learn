from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from the_big_learn.bundled_sources import BUNDLED_SOURCES


REPO_ROOT = Path(__file__).resolve().parent.parent


def _bundled_asset_paths() -> list[str]:
    module = ast.parse((REPO_ROOT / "setup.py").read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "BUNDLED_ASSET_PATHS" for target in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            raise AssertionError("BUNDLED_ASSET_PATHS must stay a list literal.")
        return [
            element.value
            for element in node.value.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
    raise AssertionError("setup.py must define BUNDLED_ASSET_PATHS.")


class PackagingTests(unittest.TestCase):
    def test_gitignore_ignores_build_output(self) -> None:
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertRegex(gitignore, r"(?m)^build/$")

    def test_pyproject_declares_setuptools_build_backend(self) -> None:
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("[build-system]", pyproject)
        self.assertIn('build-backend = "setuptools.build_meta"', pyproject)

    def test_setup_uses_scripts_package_dir(self) -> None:
        setup_py = (REPO_ROOT / "setup.py").read_text(encoding="utf-8")
        self.assertIn('packages=find_packages(where="scripts"', setup_py)
        self.assertIn('package_dir={"": "scripts"}', setup_py)

    def test_bundle_assets_include_design_doc(self) -> None:
        self.assertIn("DESIGN.md", _bundled_asset_paths())

    def test_bundle_assets_include_references_dir(self) -> None:
        self.assertIn("references", _bundled_asset_paths())

    def test_manifest_includes_design_doc(self) -> None:
        manifest = (REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("include DESIGN.md", manifest)

    def test_manifest_includes_references_dir(self) -> None:
        manifest = (REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("graft references", manifest)

    def test_bundled_source_store_uses_readable_work_ids(self) -> None:
        bundled_source_dirs = sorted(
            path.name
            for path in (REPO_ROOT / "books").iterdir()
            if path.is_dir()
        )
        self.assertEqual(bundled_source_dirs, sorted(BUNDLED_SOURCES))
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", name) is None for name in bundled_source_dirs))


if __name__ == "__main__":
    unittest.main()
