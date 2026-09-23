"""Accepted migration cleanup through the public CLI in disposable repositories."""

import re
import subprocess

import pytest
from engineering.cli import main
from engineering.migrate.openspec import WORKSPACE

from .test_finalization import invoke, proposal
from .test_migration import repo, save, snapshot

__all__ = ["repo"]


def closure(root, *args):
    return main(["--root", str(root), "migrate", "openspec-project", *args])


@pytest.fixture
def validated(repo, monkeypatch):
    proposal(repo)
    real_run = subprocess.run

    def checked(command, **kwargs):
        if command[0] == "git":
            return real_run(command, **kwargs)
        return subprocess.CompletedProcess(
            command, 0, stdout="fixture gate\n", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", checked)
    assert invoke(repo, "--apply") == 0
    return repo


def preview(root, capsys, *choices):
    capsys.readouterr()
    assert closure(root, "--cleanup", "--plan", *choices) == 0
    output = capsys.readouterr().out
    return re.search(r"Cleanup SHA-256: ([0-9a-f]{64})", output)[1]


def test_acceptance_then_authorized_cleanup_and_safe_retry(validated, capsys):
    root = validated
    before = snapshot(root)
    assert closure(root, "--accept", "--plan") == 0
    assert snapshot(root) == before
    assert closure(root, "--cleanup", "--apply") == 1
    assert closure(root, "--accept", "--apply") == 0
    assert "Migration accepted; cleanup pending" in capsys.readouterr().out
    token = preview(root, capsys)
    assert closure(root, "--cleanup", "--apply", "--approved-cleanup", token) == 0
    assert "Migration closed" in capsys.readouterr().out
    assert not (root / WORKSPACE).exists()
    after = snapshot(root)
    assert closure(root, "--cleanup", "--apply", "--approved-cleanup", token) == 0
    assert snapshot(root) == after
    assert (root / "docs/context/accounts.md").exists()


def test_explicit_retention_closes_and_allows_development(validated, capsys):
    root = validated
    save(root, f"{WORKSPACE}/snapshot/source.md", "requested historical snapshot")
    assert closure(root, "--accept", "--apply") == 0
    save(root, "docs/context/accounts.md", "ordinary development after acceptance")
    token = preview(root, capsys, "--retain", "snapshot")
    assert (
        closure(
            root,
            "--cleanup",
            "--apply",
            "--retain",
            "snapshot",
            "--approved-cleanup",
            token,
        )
        == 0
    )
    assert (
        root / WORKSPACE / "snapshot/source.md"
    ).read_text() == "requested historical snapshot"
    assert not (root / WORKSPACE / "validation.json").exists()
    assert closure(root, "--cleanup", "--plan") == 0
    assert "Migration closed" in capsys.readouterr().out


@pytest.mark.parametrize("change", ["bytes", "mode", "new", "symlink", "missing"])
def test_changed_artifacts_preserved_without_false_closure(validated, capsys, change):
    root = validated
    assert closure(root, "--accept", "--apply") == 0
    token = preview(root, capsys)
    path = root / WORKSPACE / "canonical-spec-index.md"
    if change == "bytes":
        path.write_text("human edits")
    elif change == "mode":
        path.chmod(0o755)
    elif change == "new":
        save(root, f"{WORKSPACE}/notes.md", "new notes")
    elif change == "symlink":
        path.unlink()
        path.symlink_to(root / "README.md")
    else:
        path.unlink()
    before = snapshot(root)
    assert closure(root, "--cleanup", "--apply", "--approved-cleanup", token) == 1
    assert snapshot(root) == before
    assert "Migration closed" not in capsys.readouterr().out
    if change in {"bytes", "mode", "new"}:
        token = preview(root, capsys, "--retain", ".")
        assert (
            closure(
                root,
                "--cleanup",
                "--apply",
                "--retain",
                ".",
                "--approved-cleanup",
                token,
            )
            == 0
        )
        assert path.exists()


@pytest.mark.parametrize("failure", ["missing", "failed", "unresolved", "output"])
def test_acceptance_refuses_invalid_validation(validated, capsys, failure):
    import json

    root = validated
    receipt = root / WORKSPACE / "validation.json"
    if failure == "missing":
        receipt.unlink()
    elif failure == "failed":
        data = json.loads(receipt.read_text())
        data["checks"][0]["exit_code"] = 1
        receipt.write_text(json.dumps(data))
    elif failure == "unresolved":
        path = root / WORKSPACE / "reconciliation/application.json"
        data = json.loads(path.read_text())
        data["unresolved_decisions"] = ["human decision still needed"]
        path.write_text(json.dumps(data))
    else:
        save(root, "docs/context/accounts.md", "changed output before acceptance")
    before = snapshot(root)
    assert closure(root, "--accept", "--apply") == 1
    assert snapshot(root) == before
    assert "Migration accepted" not in capsys.readouterr().out


def test_cleanup_write_failure_rolls_back_and_retries(validated, monkeypatch, capsys):
    from pathlib import Path

    root = validated
    assert closure(root, "--accept", "--apply") == 0
    token = preview(root, capsys)
    before = snapshot(root)
    real_unlink = Path.unlink

    def unlink(path, *args, **kwargs):
        if path.name == "inventory.json":
            raise OSError("fixture cleanup failure")
        return real_unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", unlink)
        assert closure(root, "--cleanup", "--apply", "--approved-cleanup", token) == 1
    assert snapshot(root) == before
    assert "Migration closed" not in capsys.readouterr().out
    assert closure(root, "--cleanup", "--apply", "--approved-cleanup", token) == 0


def test_cleanup_requires_exact_approved_choices_and_refuses_reappeared_files(
    validated, capsys
):
    root = validated
    assert closure(root, "--accept", "--apply") == 0
    token = preview(root, capsys, "--retain", ".")
    before = snapshot(root)
    assert closure(root, "--cleanup", "--apply", "--approved-cleanup", token) == 1
    assert snapshot(root) == before
    assert (
        closure(
            root, "--cleanup", "--apply", "--retain", ".", "--approved-cleanup", token
        )
        == 0
    )
    save(root, f"{WORKSPACE}/unexpected.md", "new work")
    before = snapshot(root)
    capsys.readouterr()
    assert closure(root, "--cleanup", "--apply", "--approved-cleanup", token) == 1
    assert snapshot(root) == before
    assert "Migration closed" not in capsys.readouterr().out
