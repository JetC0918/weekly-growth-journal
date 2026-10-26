"""Copy the canonical Django packages into Wrangler's Python module bundle."""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKER_ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = WORKER_ROOT / "python_modules" / "backend"
PACKAGE_NAMES = ("accounts", "config", "feedback", "journal")


def _ignore_generated(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name == "__pycache__" or name.endswith(".pyc")}


def main() -> None:
    shutil.rmtree(MODULE_ROOT, ignore_errors=True)
    MODULE_ROOT.mkdir(parents=True)
    (MODULE_ROOT / "__init__.py").write_text('"""Packaged Django application."""\n', encoding="utf-8")
    for package in PACKAGE_NAMES:
        shutil.copytree(
            PROJECT_ROOT / "backend" / package,
            MODULE_ROOT / package,
            ignore=_ignore_generated,
        )


if __name__ == "__main__":
    main()
