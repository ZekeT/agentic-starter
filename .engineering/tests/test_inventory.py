"""Observe safe OpenSpec preparation through the public command boundary."""

import json

import pytest
from engineering.cli import main

from .test_migration import fixture, repo, snapshot

__all__ = ["repo"]
WORK = ".engineering/migration-work/openspec"


def test_prepare_preserves_sources_and_only_writes_temporary_evidence(repo):
    fixture(repo)
    before = snapshot(repo)
    args = ["--root", str(repo), "migrate", "openspec-project"]
    assert main(args) == 0
    assert snapshot(repo) == before
    assert main([*args, "--plan"]) == 0
    assert snapshot(repo) == before
    assert main([*args, "--apply"]) == 0
    after = snapshot(repo)
    assert all(after[name] == raw for name, raw in before.items())
    assert all(name.startswith(WORK + "/") for name in after.keys() - before.keys())
    data = json.loads(after[WORK + "/inventory.json"])
    assert data["source_head"]
    assert data["history_policy"] == "git-only"
    assert data["canonical"][0]["title"] == "Accounts"
    assert data["canonical"][0]["related_tests"] == []
    assert data["active_changes"][0]["name"] == "active"
    assert data["archived_changes"][0]["name"] == "past"
    assert main([*args, "--apply"]) == 0
    assert snapshot(repo) == after


def test_alias_is_safe_and_dirty_tree_refuses(repo, capsys):
    fixture(repo)
    before = snapshot(repo)
    assert main(["--root", str(repo), "migrate", "openspec", "--apply"]) == 0
    assert "Deprecated alias" in capsys.readouterr().out
    assert all(snapshot(repo)[name] == raw for name, raw in before.items())


def test_dirty_source_and_symlink_workspace_refuse(repo, tmp_path):
    from .test_migration import save

    fixture(repo)
    save(repo, "new.md", "user work")
    before = snapshot(repo)
    args = ["--root", str(repo), "migrate", "openspec-project", "--apply"]
    assert main(args) == 1
    assert snapshot(repo) == before
    workspace = repo / ".engineering/migration-work"
    workspace.parent.mkdir(parents=True)
    workspace.symlink_to(tmp_path.parent, target_is_directory=True)
    assert main(args) == 1


def test_existing_inventory_cannot_be_overwritten(repo):
    from .test_migration import commit, save

    fixture(repo)
    save(repo, WORK + "/inventory.json", '{"human": "draft"}')
    commit(repo)
    before = snapshot(repo)
    assert main(["--root", str(repo), "migrate", "openspec-project", "--apply"]) == 1
    assert snapshot(repo) == before


def test_adoption_reports_openspec_without_config(repo):
    from engineering.inspection import inspect_target

    fixture(repo)
    assert any(
        "Recommended: ./engineering migrate openspec-project" in row
        for row in inspect_target(repo)
    )


def test_committed_preparation_retry_and_changed_source_refusal(repo):
    from .test_migration import commit, save

    fixture(repo)
    args = ["--root", str(repo), "migrate", "openspec-project", "--apply"]
    assert main(args) == 0
    commit(repo)
    prepared = snapshot(repo)
    assert main(args) == 0
    assert snapshot(repo) == prepared
    save(repo, "openspec/specs/accounts/spec.md", "# Changed requirements\n")
    commit(repo)
    before = snapshot(repo)
    assert main(args) == 1
    assert snapshot(repo) == before


def test_explicit_snapshot_is_temporary_and_byte_complete(repo):
    fixture(repo)
    before = snapshot(repo)
    args = [
        "--root",
        str(repo),
        "migrate",
        "openspec-project",
        "--apply",
        "--legacy-history",
        "snapshot",
    ]
    assert main(args) == 0
    after = snapshot(repo)
    assert (
        after[WORK + "/snapshot/openspec/custom.bin"] == before["openspec/custom.bin"]
    )
    assert all(after[name] == raw for name, raw in before.items())


def test_source_changes_between_preview_and_write_are_refused(repo, monkeypatch):
    import pytest
    from engineering.migrate.common import execute
    from engineering.migrate.openspec import plan

    from .test_migration import save

    fixture(repo)
    calls = 0

    def changing_plan():
        nonlocal calls
        calls += 1
        if calls == 2:
            save(repo, "openspec/specs/accounts/spec.md", "changed during preflight")
        return plan(repo)

    with pytest.raises(ValueError, match="migration.stale"):
        execute(changing_plan, apply=True)
    assert not (repo / WORK).exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [("source_head", "0" * 40), ("branches", ["fabricated"])],
)
def test_invalid_recorded_git_evidence_refuses_retry(repo, field, value):
    from engineering.ownership import encoded

    from .test_migration import commit

    fixture(repo)
    args = ["--root", str(repo), "migrate", "openspec-project", "--apply"]
    assert main(args) == 0
    path = repo / WORK / "inventory.json"
    inventory = json.loads(path.read_text())
    inventory[field] = value
    path.write_bytes(encoded(inventory))
    commit(repo)
    before = snapshot(repo)
    assert main(args) == 1
    assert snapshot(repo) == before


@pytest.mark.parametrize("policy", ["git-only", "snapshot"])
def test_ignored_source_history_is_recorded_and_retry_is_identical(repo, policy):
    from .test_migration import commit, save

    fixture(repo)
    save(repo, ".gitignore", "openspec/local.md\n")
    commit(repo)
    save(repo, "openspec/local.md", "Ignored local requirements\n")
    args = [
        "--root",
        str(repo),
        "migrate",
        "openspec-project",
        "--apply",
        "--legacy-history",
        policy,
    ]
    assert main(args) == 0
    inventory = json.loads((repo / WORK / "inventory.json").read_text())
    assert inventory["committed_at_head"]["openspec/local.md"] is False
    before = snapshot(repo)
    assert main(args) == 0
    assert snapshot(repo) == before
