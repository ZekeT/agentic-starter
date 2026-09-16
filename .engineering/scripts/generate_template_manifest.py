#!/usr/bin/env python3
"""Generate template-manifest.json for the setup-update skill.

Hashes every template-owned file so setup_update.py can tell, in a copied
project, whether a file is pristine (safe to auto-overwrite on update) or
customized (needs a guided merge).

Hash history: when a file's content changes between manifest regenerations,
the old hash is kept in that file's "previous" list. A target file matching
any previous hash is a pristine copy of an older release.

Run after changing any template-owned file, before tagging a release:

    make manifest        # or: uv run python .engineering/scripts/generate_template_manifest.py

Maintainer tool for the starter repo only — never copied to target projects.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / ".engineering"))
from engineering.config import DEFAULTS  # noqa: E402
from engineering.installation import build_state  # noqa: E402
from engineering.ownership import (  # noqa: E402
    digest,
    distribution_ownership,
    encoded,
    owned_content,
)

MANIFEST_PATH = ROOT / ".engineering" / "manifest.json"
VERSION_PATH = ROOT / ".engineering" / "TEMPLATE_VERSION"

# Exact template-owned files at fixed paths.
# NOTE: pyproject.toml is deliberately excluded — migrate_to_framework.py
# merges missing [tool.*] sections into the target's own file rather than
# copying the starter's verbatim; blind-copying would clobber a non-Python
# target's project metadata entirely. Same reasoning excludes
# scripts/migrate_to_framework.py and scripts/generate_template_manifest.py
# — both are starter-repo-only maintainer tools, never meant to be
# copied into a downstream project.
MANIFEST_FILES = [
    "engineering",
    "ENGINEERING.md",
    "CLAUDE.md",
    "AGENTS.md",
    "REVIEW.md",
    "Makefile",
    ".gitignore",
    ".claude/settings.json",
    ".claude/statusline.sh",
    ".engineering/config.toml",
    ".engineering/dependencies.toml",
    ".engineering/TEMPLATE_VERSION",
    ".engineering/setup.sh",
    ".engineering/bin/graft",
    ".engineering/graft/package.json",
    ".engineering/graft/package-lock.json",
    ".engineering/migrations/baselines/v2-manifest.json",
    "docs/agents/issue-tracker.md",
    "docs/agents/domain.md",
]
MANIFEST_GLOBS = [
    ".engineering/engineering/**/*.py",
    ".engineering/scripts/**/*.sh",
    ".engineering/scripts/check_feature_docs.py",
    ".engineering/docs/*.md",
    ".engineering/evals/*.py",
    ".engineering/evals/*.md",
    ".engineering/evals/cases/*.yaml",
    ".claude/hooks/*.py",
    ".claude/commands/*.md",
    ".claude/agents/*.md",
]
MANIFEST_SKILL_DIRS = []

EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}
EXCLUDED_NAMES = {".DS_Store"}

# Paths owned by `openspec init` / `openspec update`, never by this template.
# Hashing them would make setup-update fight the OpenSpec CLI for ownership:
# every OpenSpec release would land in downstream projects as "CUSTOMIZED".
#
# The collectors above are allowlists, so today nothing here would be picked up
# anyway — .claude/commands/*.md is non-recursive and misses commands/opsx/, and
# the skill dirs are named explicitly. This filter makes that a guarantee rather
# than a side effect, so widening a glob later can't silently capture them.
OPENSPEC_OWNED_PREFIXES = (
    "openspec/",
    ".claude/commands/opsx/",
    ".claude/skills/openspec-",
)

# Starter-repo-only maintainer tooling — never shipped to a fork. Same
# guarantee-not-accident reasoning as OPENSPEC_OWNED_PREFIXES above.
# Named file by file, not by directory: .engineering/scripts/ also holds the
# cmd_*.sh command preambles, which every shipped command calls and which a
# fork therefore needs.
STARTER_ONLY_PREFIXES = (
    ".engineering/tests/",
    ".engineering/scripts/generate_template_manifest.py",
    ".engineering/scripts/migrate_to_framework.py",
)


def is_openspec_owned(rel: str) -> bool:
    """Return True if a repo-relative path belongs to the OpenSpec CLI."""
    return rel.startswith(OPENSPEC_OWNED_PREFIXES)


def is_starter_only(rel: str) -> bool:
    """Return True if a repo-relative path is starter-repo tooling, never shipped."""
    return rel.startswith(STARTER_ONLY_PREFIXES)


def sha256_of(path: Path) -> str:
    """Return the sha256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_files() -> list[Path]:
    """Collect all template-owned files that currently exist."""
    found: set[Path] = set()
    for rel in MANIFEST_FILES:
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
    return sorted(
        p
        for p in found
        if not is_openspec_owned(p.relative_to(ROOT).as_posix())
        and not is_starter_only(p.relative_to(ROOT).as_posix())
    )


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
    if "schema_version" in previous and (
        type(previous["schema_version"]) is not int or previous["schema_version"] != 1
    ):
        raise ValueError(
            "Unsupported manifest schema_version; use engineering tooling compatible "
            "with this manifest before regenerating it"
        )
    prev_files: dict[str, Any] = previous.get("files", {})
    files: dict[str, Any] = {}
    for path in collect_files():
        rel = path.relative_to(ROOT).as_posix()
        current_digest = sha256_of(path)
        old_entry = prev_files.get(rel, {})
        history: list[str] = list(old_entry.get("previous", []))
        old_current = old_entry.get("sha256")
        if old_current and old_current != current_digest and old_current not in history:
            history.append(old_current)
        ownership = distribution_ownership(rel)
        owned = owned_content(path.read_bytes(), rel, ownership)
        files[rel] = {
            "sha256": current_digest,
            "previous": history,
            "ownership": ownership,
            "owned_sha256": digest(owned),
            "executable": bool(path.stat().st_mode & 0o111),
        }
    version = "unknown"
    if VERSION_PATH.exists():
        version = VERSION_PATH.read_text().strip()
    return {
        "schema_version": 1,
        "defaults": {"maintainability": dict(DEFAULTS)},
        "project": previous.get("project", {}),
        "template_version": version,
        "ownership_version": 1,
        "files": files,
    }


def main() -> None:
    """Regenerate template-manifest.json in place."""
    try:
        previous = load_previous_manifest()
        manifest = build_manifest(previous)
    except ValueError as exc:
        sys.exit(str(exc))
    MANIFEST_PATH.write_bytes(encoded(manifest))
    entries = {
        name: {"ownership": entry["ownership"], "upstream": entry["owned_sha256"]}
        for name, entry in manifest["files"].items()
        if entry["ownership"]["mode"] != "preserve"
    }
    state_path = ROOT / ".engineering/state/install.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_bytes(encoded(build_state(manifest["template_version"], entries)))
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
