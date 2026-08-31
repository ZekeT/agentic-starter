"""Tests for scripts/generate_template_manifest.py.

Focused on the non-negotiable constraint: files owned by the OpenSpec CLI must
never be hashed into template-manifest.json. If they were, every OpenSpec
release would show up in downstream projects as a "CUSTOMIZED" file needing a
guided merge, and setup-update would fight `openspec update` for ownership.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# These exercise real filesystem, git, and subprocess behaviour — that IS the
# unit under test here. Per docs/harness/testing.md they are integration tests.
pytestmark = pytest.mark.integration

SCRIPTS = Path(__file__).parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import generate_template_manifest as g  # noqa: E402


@pytest.mark.parametrize(
    "rel",
    [
        "openspec/config.yaml",
        "openspec/specs/auth/spec.md",
        "openspec/changes/add-thing/proposal.md",
        "openspec/changes/archive/2026-01-01-old/proposal.md",
        ".claude/commands/opsx/propose.md",
        ".claude/skills/openspec-propose/SKILL.md",
        ".claude/skills/openspec-archive-change/SKILL.md",
    ],
)
def test_openspec_paths_are_excluded(rel: str) -> None:
    assert g.is_openspec_owned(rel)


@pytest.mark.parametrize(
    "rel",
    [
        "CLAUDE.md",
        ".env.template",
        ".claude/commands/review.md",
        ".claude/hooks/post_tool_lint.py",
        ".claude/skills/python-standards/SKILL.md",
        "docs/harness/setup.md",
        # Near-misses: similar prefixes that are ours, not OpenSpec's.
        "openspecs/notes.md",
        ".claude/commands/opsx.md",
        ".claude/skills/openspec.md",
    ],
)
def test_template_paths_are_not_excluded(rel: str) -> None:
    assert not g.is_openspec_owned(rel)


def test_collect_files_returns_no_openspec_paths() -> None:
    """Run the real collector against the real repo."""
    rels = [p.relative_to(g.ROOT).as_posix() for p in g.collect_files()]
    assert rels, "collector found nothing — the allowlists are broken"
    assert not [r for r in rels if g.is_openspec_owned(r)]


def test_collect_files_still_finds_template_files() -> None:
    """Guard against the exclusion filter being too greedy."""
    rels = {p.relative_to(g.ROOT).as_posix() for p in g.collect_files()}
    assert "CLAUDE.md" in rels
    assert ".env.template" in rels
    assert any(r.startswith(".claude/skills/setup-update/") for r in rels)
