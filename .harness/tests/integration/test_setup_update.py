"""Tests for .claude/skills/setup-update/scripts/setup_update.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# These exercise real filesystem, git, and subprocess behaviour — that IS the
# unit under test here. Per .harness/docs/testing.md they are integration tests.
pytestmark = pytest.mark.integration

# Add the skill's scripts/ dir to path so we can import without installing.
SKILL_SCRIPTS = (
    Path(__file__).parents[3] / ".claude" / "skills" / "setup-update" / "scripts"
)
sys.path.insert(0, str(SKILL_SCRIPTS))

import setup_update as u  # noqa: E402

# ── fixtures ──────────────────────────────────────────────────────────────────


def make_starter(tmp_path: Path, files: dict[str, str]) -> Path:
    """Create a fake starter repo with the given files and a manifest."""
    starter = tmp_path / "starter"
    starter.mkdir()
    manifest_files = {}
    for rel, content in files.items():
        p = starter / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        manifest_files[rel] = {"sha256": u.sha256_of(p), "previous": []}
    (starter / u.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "template_version": "1.0.0",
                "generated_at": "2026-01-01T00:00:00+00:00",
                "files": manifest_files,
            }
        )
    )
    return starter


def make_target(tmp_path: Path) -> Path:
    """Create a bare target project directory."""
    target = tmp_path / "target"
    target.mkdir()
    return target


# ── classify() ───────────────────────────────────────────────────────────────


def test_classify_new_when_file_missing(tmp_path: Path) -> None:
    starter = make_starter(tmp_path, {"a.txt": "hello"})
    target = make_target(tmp_path)
    manifest = u.load_manifest(starter)
    entry = manifest["files"]["a.txt"]
    assert u.classify("a.txt", entry, target) == "new"


def test_classify_current_when_hash_matches(tmp_path: Path) -> None:
    starter = make_starter(tmp_path, {"a.txt": "hello"})
    target = make_target(tmp_path)
    (target / "a.txt").write_text("hello")
    manifest = u.load_manifest(starter)
    entry = manifest["files"]["a.txt"]
    assert u.classify("a.txt", entry, target) == "current"


def test_classify_auto_update_when_matches_previous_hash(tmp_path: Path) -> None:
    starter = make_starter(tmp_path, {"a.txt": "hello v2"})
    target = make_target(tmp_path)
    (target / "a.txt").write_text("hello v1")
    manifest = u.load_manifest(starter)
    entry = manifest["files"]["a.txt"]
    entry["previous"] = [u.sha256_of(target / "a.txt")]
    assert u.classify("a.txt", entry, target) == "auto-update"


def test_classify_customized_when_hash_unknown(tmp_path: Path) -> None:
    starter = make_starter(tmp_path, {"a.txt": "hello v2"})
    target = make_target(tmp_path)
    (target / "a.txt").write_text("user's own content")
    manifest = u.load_manifest(starter)
    entry = manifest["files"]["a.txt"]
    assert u.classify("a.txt", entry, target) == "customized"


# ── run_update() ─────────────────────────────────────────────────────────────


def test_run_update_copies_new_and_auto_update_but_not_customized(
    tmp_path: Path,
) -> None:
    starter = make_starter(
        tmp_path,
        {"new.txt": "new content", "pristine.txt": "v2", "custom.txt": "v2"},
    )
    target = make_target(tmp_path)
    manifest = u.load_manifest(starter)
    manifest["files"]["pristine.txt"]["previous"] = ["oldhash"]

    (target / "pristine.txt").write_text("v1")
    # Force pristine.txt to actually classify as auto-update by matching the
    # real old hash rather than a fake placeholder.
    old_hash = u.sha256_of(target / "pristine.txt")
    (starter / u.MANIFEST_NAME).write_text(
        json.dumps(
            {
                "template_version": "1.0.0",
                "files": {
                    "new.txt": {
                        "sha256": u.sha256_of(starter / "new.txt"),
                        "previous": [],
                    },
                    "pristine.txt": {
                        "sha256": u.sha256_of(starter / "pristine.txt"),
                        "previous": [old_hash],
                    },
                    "custom.txt": {
                        "sha256": u.sha256_of(starter / "custom.txt"),
                        "previous": [],
                    },
                },
            }
        )
    )
    (target / "custom.txt").write_text("the user's own text")

    results = u.run_update(starter, target, dry=False)

    assert results["new"] == ["new.txt"]
    assert results["auto-update"] == ["pristine.txt"]
    assert results["customized"] == ["custom.txt"]

    assert (target / "new.txt").read_text() == "new content"
    assert (target / "pristine.txt").read_text() == "v2"
    assert (target / "custom.txt").read_text() == "the user's own text"


def test_run_update_dry_run_writes_nothing(tmp_path: Path) -> None:
    starter = make_starter(tmp_path, {"new.txt": "new content"})
    target = make_target(tmp_path)

    results = u.run_update(starter, target, dry=True)

    assert results["new"] == ["new.txt"]
    assert not (target / "new.txt").exists()


# ── merge_gitignore() ────────────────────────────────────────────────────────


def test_merge_gitignore_appends_missing_lines(tmp_path: Path) -> None:
    starter = tmp_path / "starter"
    starter.mkdir()
    (starter / ".gitignore").write_text("*.pyc\n.env\nnode_modules/\n")

    target = tmp_path / "target"
    target.mkdir()
    (target / ".gitignore").write_text("*.pyc\n")

    added = u.merge_gitignore(starter, target, dry=False)

    assert set(added) == {".env", "node_modules/"}
    content = (target / ".gitignore").read_text()
    assert ".env" in content
    assert "node_modules/" in content
    assert "*.pyc" in content  # original preserved


def test_merge_gitignore_no_target_file_creates_one(tmp_path: Path) -> None:
    starter = tmp_path / "starter"
    starter.mkdir()
    (starter / ".gitignore").write_text("*.pyc\n")

    target = tmp_path / "target"
    target.mkdir()

    added = u.merge_gitignore(starter, target, dry=False)

    assert added == ["*.pyc"]
    assert (target / ".gitignore").exists()


def test_merge_gitignore_dry_run_writes_nothing(tmp_path: Path) -> None:
    starter = tmp_path / "starter"
    starter.mkdir()
    (starter / ".gitignore").write_text("*.pyc\n")

    target = tmp_path / "target"
    target.mkdir()

    added = u.merge_gitignore(starter, target, dry=True)

    assert added == ["*.pyc"]
    assert not (target / ".gitignore").exists()


# ── read_target_version() ────────────────────────────────────────────────────


def test_read_target_version_prefers_stamp(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    stamp = target / ".claude" / "template-version.json"
    stamp.parent.mkdir(parents=True)
    stamp.write_text(json.dumps({"template_version": "2.0.0"}))
    (target / ".claude" / "migration-report.json").write_text(
        json.dumps({"starter_version": "1.0.0"})
    )
    assert u.read_target_version(target) == "2.0.0"


def test_read_target_version_falls_back_to_migration_report(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    report_dir = target / ".claude"
    report_dir.mkdir()
    (report_dir / "migration-report.json").write_text(
        json.dumps({"starter_version": "1.0.0"})
    )
    assert u.read_target_version(target) == "1.0.0"


def test_read_target_version_unknown_when_nothing_recorded(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    assert u.read_target_version(target) == "unknown"


# ── load_manifest() ──────────────────────────────────────────────────────────


def test_load_manifest_missing_exits(tmp_path: Path) -> None:
    starter = tmp_path / "starter"
    starter.mkdir()
    with pytest.raises(SystemExit):
        u.load_manifest(starter)


def test_load_manifest_finds_new_harness_location(tmp_path: Path) -> None:
    """The .harness/ layout (current) is checked first."""
    starter = make_starter(tmp_path, {"a.txt": "hello"})
    manifest_body = json.loads((starter / u.MANIFEST_NAME).read_text())
    (starter / u.MANIFEST_NAME).unlink()
    (starter / ".harness").mkdir()
    (starter / ".harness" / u.MANIFEST_NAME).write_text(json.dumps(manifest_body))
    assert u.load_manifest(starter) == manifest_body


def test_load_manifest_falls_back_to_old_root_location(tmp_path: Path) -> None:
    """A pre-.harness/ starter (older template version) still works."""
    starter = make_starter(tmp_path, {"a.txt": "hello"})
    manifest = u.load_manifest(starter)
    assert manifest["files"]["a.txt"]["sha256"] == u.sha256_of(starter / "a.txt")


# ── OpenSpec ownership ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "rel",
    [
        "openspec/config.yaml",
        "openspec/specs/auth/spec.md",
        "openspec/changes/add-thing/proposal.md",
        ".claude/commands/opsx/propose.md",
        ".claude/skills/openspec-propose/SKILL.md",
    ],
)
def test_is_openspec_owned_true(rel: str) -> None:
    assert u.is_openspec_owned(rel)


@pytest.mark.parametrize(
    "rel",
    [
        "CLAUDE.md",
        ".claude/commands/review.md",
        ".claude/skills/setup-update/SKILL.md",
        ".claude/skills/python-standards/SKILL.md",
        "docs/product.md",
        # Near-misses that must NOT be treated as OpenSpec-owned.
        "openspecs/thing.md",
        ".claude/commands/opsx.md",
    ],
)
def test_is_openspec_owned_false(rel: str) -> None:
    assert not u.is_openspec_owned(rel)


def test_run_update_never_copies_openspec_files(tmp_path: Path) -> None:
    """A stale manifest listing OpenSpec paths must not overwrite the target's."""
    starter = make_starter(
        tmp_path,
        {
            "CLAUDE.md": "starter claude\n",
            "openspec/config.yaml": "schema: starter-version\n",
            ".claude/skills/openspec-propose/SKILL.md": "starter skill\n",
        },
    )
    target = make_target(tmp_path)
    (target / "openspec").mkdir()
    (target / "openspec" / "config.yaml").write_text("schema: target-version\n")

    u.run_update(starter, target, dry=False)

    # CLAUDE.md is template-owned and should land.
    assert (target / "CLAUDE.md").read_text() == "starter claude\n"
    # OpenSpec files are owned by the CLI — left exactly as they were.
    assert (
        target / "openspec" / "config.yaml"
    ).read_text() == "schema: target-version\n"
    assert not (target / ".claude" / "skills" / "openspec-propose").exists()
