#!/usr/bin/env python3
"""Require feature documentation at the final gate, without per-edit reminders."""

from __future__ import annotations

import os
import sys
from pathlib import Path

IGNORED_NAMES = {"CLAUDE.md", "CONTEXT.md", "__init__.py"}
IGNORED_DIRS = {"__pycache__", "node_modules"}


def has_feature_files(feature: Path) -> bool:
    """Ignore empty package scaffolds, caches and hidden directories."""
    for _, dirs, files in os.walk(feature):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in IGNORED_DIRS]
        if any(
            name not in IGNORED_NAMES
            and not name.startswith(".")
            and not name.endswith((".pyc", ".pyo"))
            for name in files
        ):
            return True
    return False


def main() -> int:
    """Report all missing feature CLAUDE.md files, without creating any state."""
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "src")
    if not src.is_dir():
        return 0
    missing = [
        feature / "CLAUDE.md"
        for feature in sorted(src.iterdir())
        if feature.is_dir()
        and not feature.is_symlink()
        and not feature.name.startswith(".")
        and feature.name not in IGNORED_DIRS
        and has_feature_files(feature)
        and not (feature / "CLAUDE.md").is_file()
    ]
    for path in missing:
        print(
            f"Missing {path}: document purpose, entry points, invariants and gotchas. "
            "Stable facts only; task status belongs in tasks.md.",
            file=sys.stderr,
        )
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
