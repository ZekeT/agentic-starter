#!/usr/bin/env python3
"""Generate template-manifest.json for the setup-update skill.

Hashes every template-owned file so setup_update.py can tell, in a copied
project, whether a file is pristine (safe to auto-overwrite on update) or
customized (needs a guided merge).

Hash history: when a file's content changes between manifest regenerations,
the old hash is kept in that file's "previous" list. A target file matching
any previous hash is a pristine copy of an older release.

Run after changing any template-owned file, before tagging a release:

    make manifest        # or: uv run python scripts/generate_template_manifest.py

Maintainer tool for the starter repo only — never copied to target projects.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
MANIFEST_PATH = ROOT / "template-manifest.json"
VERSION_PATH = ROOT / "TEMPLATE_VERSION"

# Exact template-owned files at fixed paths.
# NOTE: pyproject.toml is deliberately excluded — migrate_to_framework.py
# merges missing [tool.*] sections into the target's own file rather than
# copying the starter's verbatim; blind-copying would clobber a non-Python
# target's project metadata entirely. Same reasoning excludes
# scripts/migrate_to_framework.py and scripts/generate_template_manifest.py
# below — both are starter-repo-only maintainer tools, never meant to be
# copied into a downstream project.
MANIFEST_FILES = [
    "CLAUDE.md",
    "Makefile",
    "setup.sh",
    ".gitignore",
    ".env.template",
    "config/models.json",
    ".claude/settings.json",
    "docs/SETUP.md",
    "docs/coding-standards.md",
    "docs/local-models.md",
    "docs/prd.md",
    "docs/architecture.md",
    "stories/STORY_TEMPLATE.md",
]

# Scripts copied into downstream projects (a curated list, not a glob —
# migrate_to_framework.py and generate_template_manifest.py are starter-only
# and must never appear here).
MANIFEST_SCRIPTS = [
    "scripts/configure.py",
]

# Glob patterns relative to the repo root (non-recursive).
MANIFEST_GLOBS = [
    ".claude/hooks/*.py",
    ".claude/commands/*.md",
    ".claude/agents/*.md",
]

# Our skills, walked recursively.
MANIFEST_SKILL_DIRS = [
    "setup-base",
    "setup-migrate",
    "setup-update",
    "rescan-docs",
    "graphify",
]

EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
EXCLUDED_NAMES = {".DS_Store"}


def sha256_of(path: Path) -> str:
    """Return the sha256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_files() -> list[Path]:
    """Collect all template-owned files that currently exist."""
    found: set[Path] = set()
    for rel in MANIFEST_FILES + MANIFEST_SCRIPTS:
        p = ROOT / rel
        if p.is_file():
            found.add(p)
    for pattern in MANIFEST_GLOBS:
        found.update(p for p in ROOT.glob(pattern) if p.is_file())
    for skill in MANIFEST_SKILL_DIRS:
        skill_dir = ROOT / ".claude" / "skills" / skill
        if skill_dir.is_dir():
            found.update(
                p
                for p in skill_dir.rglob("*")
                if p.is_file()
                and not EXCLUDED_PARTS.intersection(p.parts)
                and p.name not in EXCLUDED_NAMES
            )
    return sorted(found)


def load_previous_manifest() -> dict[str, Any]:
    """Return the existing manifest, or an empty dict if none exists."""
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text())  # type: ignore[no-any-return]


def build_manifest(previous: dict[str, Any]) -> dict[str, Any]:
    """Build the new manifest, carrying hash history forward.

    Args:
        previous: The previously generated manifest (may be empty).

    Returns:
        The new manifest dict ready to serialise.
    """
    prev_files: dict[str, Any] = previous.get("files", {})
    files: dict[str, Any] = {}
    for path in collect_files():
        rel = path.relative_to(ROOT).as_posix()
        digest = sha256_of(path)
        old_entry = prev_files.get(rel, {})
        history: list[str] = list(old_entry.get("previous", []))
        old_current = old_entry.get("sha256")
        if old_current and old_current != digest and old_current not in history:
            history.append(old_current)
        files[rel] = {"sha256": digest, "previous": history}
    version = "unknown"
    if VERSION_PATH.exists():
        version = VERSION_PATH.read_text().strip()
    return {
        "template_version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": files,
    }


def main() -> None:
    """Regenerate template-manifest.json in place."""
    previous = load_previous_manifest()
    manifest = build_manifest(previous)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    changed = sum(
        1
        for rel, entry in manifest["files"].items()
        if previous.get("files", {}).get(rel, {}).get("sha256") != entry["sha256"]
    )
    print(
        f"template-manifest.json written: {len(manifest['files'])} files, "
        f"{changed} changed since last generation "
        f"(template version {manifest['template_version']})"
    )


if __name__ == "__main__":
    main()
