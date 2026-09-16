"""Exercise migrations against committed fixture repositories and hostile paths."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from engineering.migrate.common import execute
from engineering.migrate.openspec import plan
from engineering.transaction import write_files


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True
    )


def save(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    save(tmp_path, "README.md", "Project\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "baseline")
    return tmp_path


def commit(root):
    git(root, "add", ".")
    git(root, "commit", "-m", "fixture")


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }


def fixture(root):
    save(root, "openspec/specs/accounts/spec.md", "# Accounts\nDomain constraint\n")
    save(root, "openspec/changes/active/intent.md", "# Intent\nDo useful work\n")
    save(
        root,
        "openspec/changes/active/program-design.md",
        "# Code Shape\nDurable constraint\n",
    )
    save(root, "openspec/changes/active/tasks.md", "- [x] one\n- [ ] two\n")
    save(root, "openspec/changes/archive/past/tasks.md", "- [x] old\n")
    save(root, "openspec/custom.bin", "unknown source\n")
    save(root, "docs/adr/database.md", "# Decision\nKeep existing\n")
    save(root, ".claude/commands/opsx/propose.md", "generated command\n")
    save(root, ".claude/skills/openspec-propose/SKILL.md", "generated skill\n")
    commit(root)


def test_empty(repo):
    before = snapshot(repo)
    assert execute(lambda: plan(repo), apply=True) == 0
    assert snapshot(repo) == before


def test_plan_and_complete_apply_idempotency(repo):
    fixture(repo)
    before = snapshot(repo)
    assert plan(repo) == plan(repo)
    assert execute(lambda: plan(repo), apply=False) == 0
    assert snapshot(repo) == before
    expected = plan(repo).changes
    assert execute(lambda: plan(repo), apply=True) == 0
    after = snapshot(repo)
    for name, raw in expected.items():
        assert after.get(name) == raw
    assert after["docs/adr/database.md"] == before["docs/adr/database.md"]
    assert b"PARTIALLY_IMPLEMENTED" in after["docs/migrations/openspec/active.md"]
    assert b"Durable constraint" in after["docs/migrations/openspec/active.md"]
    assert not (repo / "openspec").exists()
    assert execute(lambda: plan(repo), apply=True) == 0
    assert snapshot(repo) == after


def test_dirty_refuses_every_write(repo):
    fixture(repo)
    save(repo, "uncommitted.md", "user work")
    before = snapshot(repo)
    with pytest.raises(ValueError, match="git.dirty"):
        execute(lambda: plan(repo), apply=True)
    assert snapshot(repo) == before


def test_destination_conflict(repo):
    fixture(repo)
    save(repo, "docs/migrations/openspec/active.md", "manual draft")
    commit(repo)
    before = snapshot(repo)
    assert execute(lambda: plan(repo), apply=True) == 1
    assert snapshot(repo) == before


def test_edited_migration_output_is_not_overwritten(repo):
    fixture(repo)
    assert execute(lambda: plan(repo), apply=True) == 0
    save(repo, "docs/migrations/openspec/active.md", "revised draft")
    before = snapshot(repo)
    assert execute(lambda: plan(repo), apply=True) == 1
    assert snapshot(repo) == before


def test_git_only_preserves_verified_history(repo):
    fixture(repo)
    assert execute(lambda: plan(repo, "git-only"), apply=True) == 0
    assert not (repo / ".engineering/migrations/legacy-openspec").exists()
    data = json.loads(
        (repo / ".engineering/state/migrations/openspec.json").read_text()
    )
    assert data["source_head"] and data["source_paths"]


def test_git_only_refuses_uncommitted_sources(repo):
    save(repo, "openspec/specs/new/spec.md", "not committed")
    assert plan(repo, "git-only").conflicts


@pytest.mark.parametrize(
    "location", ["openspec", "openspec/specs/link", "docs/migrations"]
)
def test_symlink_paths_refuse(repo, tmp_path, location):
    if location != "openspec":
        fixture(repo)
    target = tmp_path.parent / (tmp_path.name + "-outside")
    target.mkdir()
    path = repo / location
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        plan(repo)


def test_non_directory_structure_refuses(repo):
    save(repo, "openspec", "not a directory")
    with pytest.raises(ValueError, match="directory"):
        plan(repo)


def test_write_failure_rolls_back_bytes_and_modes(repo, monkeypatch):
    save(repo, "old", "before")
    original = Path.write_bytes

    def fail(path, content):
        if path.name == "fail":
            raise OSError("simulated disk error")
        return original(path, content)

    monkeypatch.setattr(Path, "write_bytes", fail)
    before = snapshot(repo)
    with pytest.raises(ValueError, match="Affected files restored"):
        write_files(repo, {"old": b"after", "created/nested/fail": b"fail"})
    assert snapshot(repo) == before
    assert not (repo / "created").exists()


def test_openspec_wiring_without_source_and_unrelated_dependencies(repo):
    save(
        repo,
        "package.json",
        json.dumps(
            {
                "devDependencies": {"@fission-ai/openspec": "1.0.0", "keep": "2.0.0"},
                "scripts": {"test": "native"},
            }
        ),
    )
    save(
        repo,
        "package-lock.json",
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {
                        "devDependencies": {
                            "@fission-ai/openspec": "1.0.0",
                            "keep": "2.0.0",
                        }
                    },
                    "node_modules/@fission-ai/openspec": {"version": "1.0.0"},
                    "node_modules/keep": {"version": "2.0.0"},
                },
            }
        ),
    )
    save(
        repo,
        "AGENTS.md",
        "Project rules\n<!-- OPENSPEC:START -->\nOld instructions\n<!-- OPENSPEC:END -->\nKeep this.\n",
    )
    commit(repo)
    assert execute(lambda: plan(repo), apply=True) == 0
    package = json.loads((repo / "package.json").read_text())
    assert package == {
        "devDependencies": {"keep": "2.0.0"},
        "scripts": {"test": "native"},
    }
    lock = json.loads((repo / "package-lock.json").read_text())
    assert "node_modules/keep" in lock["packages"]
    assert "node_modules/@fission-ai/openspec" not in lock["packages"]
    assert (repo / "AGENTS.md").read_text() == "Project rules\nKeep this.\n"
    assert execute(lambda: plan(repo), apply=True) == 0


def test_unsupported_lockfile_surfaces_conflict_without_mutation(repo):
    save(repo, "package.json", '{"devDependencies":{"@fission-ai/openspec":"1.0.0"}}')
    save(repo, "pnpm-lock.yaml", "project-owned lock")
    commit(repo)
    before = snapshot(repo)
    assert execute(lambda: plan(repo), apply=True) == 1
    assert snapshot(repo) == before


def test_validation_failure_rolls_back(repo):
    before = snapshot(repo)

    def fail():
        raise ValueError("post-apply validation failed")

    with pytest.raises(ValueError, match="Affected files restored"):
        write_files(repo, {"README.md": b"modified", "new/file": b"new"}, validate=fail)
    assert snapshot(repo) == before
