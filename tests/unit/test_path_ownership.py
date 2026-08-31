"""Unit tests for OpenSpec path-ownership classification.

This is the one piece of genuinely pure logic in the harness's tooling: given a
repo-relative path string, decide whether the OpenSpec CLI owns it. No
filesystem, no subprocess — so it belongs in tests/unit/ per
docs/harness/testing.md, while everything else in tests/ drives real files and
lives in tests/integration/.

The rule is duplicated deliberately in two places — the manifest generator and
the setup-update script — because each must hold even if the other is absent or
stale. These tests assert both copies agree.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "setup-update" / "scripts"))

import generate_template_manifest as gen  # noqa: E402
import setup_update as upd  # noqa: E402

OWNED = [
    "openspec/config.yaml",
    "openspec/specs/auth/spec.md",
    "openspec/changes/add-thing/proposal.md",
    "openspec/changes/archive/2026-01-01-old/proposal.md",
    ".claude/commands/opsx/propose.md",
    ".claude/skills/openspec-propose/SKILL.md",
    ".claude/skills/openspec-archive-change/SKILL.md",
]

NOT_OWNED = [
    "CLAUDE.md",
    "REVIEW.md",
    "config/models.json",
    ".claude/commands/review.md",
    ".claude/commands/dev-change.md",
    ".claude/hooks/post_tool_lint.py",
    ".claude/skills/python-standards/SKILL.md",
    ".claude/skills/crystallize/SKILL.md",
    "docs/harness/testing.md",
    # Near-misses: similar prefixes that are ours, not OpenSpec's. A substring
    # check instead of a prefix check would wrongly claim all three.
    "openspecs/notes.md",
    ".claude/commands/opsx.md",
    ".claude/skills/openspec.md",
]


@pytest.mark.parametrize("rel", OWNED)
def test_openspec_owned_paths_are_recognised(rel: str) -> None:
    assert gen.is_openspec_owned(rel)
    assert upd.is_openspec_owned(rel)


@pytest.mark.parametrize("rel", NOT_OWNED)
def test_template_owned_paths_are_not_claimed(rel: str) -> None:
    assert not gen.is_openspec_owned(rel)
    assert not upd.is_openspec_owned(rel)


@pytest.mark.parametrize("rel", OWNED + NOT_OWNED)
def test_both_implementations_agree(rel: str) -> None:
    """The two copies must never drift — a disagreement means one is stale."""
    assert gen.is_openspec_owned(rel) == upd.is_openspec_owned(rel)
