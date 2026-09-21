"""Finalization CLI behavior against committed repositories and exact proposals."""

import json
from pathlib import Path

import pytest
from engineering.cli import main
from engineering.migrate.openspec import WORKSPACE
from engineering.ownership import digest

from .test_migration import commit, git, repo, save, snapshot

__all__ = ["repo"]


def invoke(root, *args):
    return main(
        ["--root", str(root), "migrate", "openspec-project", "--finalize", *args]
    )


def proposal(root):
    save(root, ".gitignore", f"{WORKSPACE}/\n")
    save(root, "openspec/specs/accounts/spec.md", "# Accounts\nA domain rule.\n")
    save(root, "CLAUDE.md", "Project rules\nOpenSpec wiring\n")
    commit(root)
    assert main(["--root", str(root), "migrate", "openspec-project", "--apply"]) == 0
    raw = (root / WORKSPACE / "inventory.json").read_bytes()
    inventory = json.loads(raw)
    plan = "# Reviewed migration\nKeep the domain rule; remove OpenSpec wiring.\n"
    save(root, f"{WORKSPACE}/reconciliation/plan.md", plan)
    data = {
        "schema_version": 1,
        "inventory_sha256": digest(raw),
        "reviewed_head": git(root, "rev-parse", "HEAD").stdout.decode().strip(),
        "plan": {"path": "reconciliation/plan.md", "sha256": digest(plan.encode())},
        "writes": [
            {
                "path": "docs/context/accounts.md",
                "before_sha256": None,
                "content": "# Accounts\nA domain rule.\n",
            },
            {
                "path": "CLAUDE.md",
                "before_sha256": inventory["source_paths"]["CLAUDE.md"],
                "content": "Project rules\n",
            },
        ],
        "deletes": [
            {
                "path": "openspec/specs/accounts/spec.md",
                "before_sha256": inventory["source_paths"][
                    "openspec/specs/accounts/spec.md"
                ],
            }
        ],
        "canonical": [
            {
                "source": "openspec/specs/accounts/spec.md",
                "classification": "KEEP_AS_CONTEXT",
                "evidence": ["README.md"],
                "reason": "Domain context",
            }
        ],
        "active": [],
        "unresolved_decisions": [],
    }
    save_proposal(root, data)
    return data


def save_proposal(root, data):
    save(root, f"{WORKSPACE}/reconciliation/application.json", json.dumps(data))


def test_preview_displays_exact_diff_and_digest_without_writes(repo, capsys):
    proposal(repo)
    before = snapshot(repo)
    assert invoke(repo, "--plan") == 0
    assert snapshot(repo) == before
    output = capsys.readouterr().out
    assert "Manifest SHA-256:" in output
    assert "-OpenSpec wiring" in output
    assert "+A domain rule." in output
    assert "Recovery commit:" in output


def test_apply_validates_and_retries_without_duplicate_outputs(
    repo, monkeypatch, capsys
):
    import subprocess

    proposal(repo)
    real_run = subprocess.run
    commands = []

    def checked(command, **kwargs):
        if command[0] != "git":
            commands.append(command)
            return subprocess.CompletedProcess(
                command, 0, stdout="fixture gate passed\n", stderr=""
            )
        return real_run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", checked)
    assert invoke(repo, "--apply") == 0
    assert not (repo / "openspec").exists()
    assert (
        repo / "docs/context/accounts.md"
    ).read_text() == "# Accounts\nA domain rule.\n"
    assert (repo / "CLAUDE.md").read_text() == "Project rules\n"
    assert any("doctor" in cmd for cmd in commands)
    assert ["make", "check"] in commands
    after = snapshot(repo)
    assert invoke(repo, "--apply") == 0
    assert snapshot(repo) == after
    assert "Already finalized" in capsys.readouterr().out
    save(repo, "docs/context/accounts.md", "User customization\n")
    before = snapshot(repo)
    assert invoke(repo, "--apply") == 1
    assert snapshot(repo) == before


@pytest.mark.parametrize(
    "mutation",
    [
        "dirty",
        "head",
        "source",
        "destination",
        "plan",
        "unresolved",
        "omitted",
        "shared-delete",
        "traversal",
        "symlink",
        "history",
        "new-source",
    ],
)
def test_refuses_unsafe_or_stale_proposals_without_writes(repo, mutation, capsys):
    data = proposal(repo)
    if mutation == "dirty":
        save(repo, "README.md", "dirty")
    elif mutation == "head":
        save(repo, "README.md", "new code")
        commit(repo)
    elif mutation == "source":
        save(repo, "openspec/specs/accounts/spec.md", "changed source")
    elif mutation == "destination":
        save(repo, "docs/context/accounts.md", "customized")
    elif mutation == "plan":
        save(repo, f"{WORKSPACE}/reconciliation/plan.md", "changed plan")
    elif mutation == "unresolved":
        data["unresolved_decisions"] = ["Which rule wins?"]
    elif mutation == "omitted":
        data["deletes"] = []
    elif mutation == "shared-delete":
        data["deletes"].append(
            {
                key: value
                for key, value in data["writes"].pop().items()
                if key != "content"
            }
        )
    elif mutation == "traversal":
        data["writes"][0]["path"] = "docs/context/../../README.md"
    elif mutation == "symlink":
        (repo / "docs").symlink_to(repo.parent, target_is_directory=True)
    elif mutation == "history":
        path = repo / WORKSPACE / "inventory.json"
        inventory = json.loads(path.read_bytes())
        inventory["source_head"] = "0" * 40
        path.write_text(json.dumps(inventory))
        data["inventory_sha256"] = digest(path.read_bytes())
    elif mutation == "new-source":
        save(repo, "openspec/new.md", "unreviewed source")
    save_proposal(repo, data)
    before = snapshot(repo)
    assert invoke(repo, "--apply") == 1
    assert snapshot(repo) == before
    assert "✗ migrate:" in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["doctor", "check", "navigation", "write"])
def test_failed_gates_or_writes_restore_sources_outputs_and_modes(
    repo, monkeypatch, failure, capsys
):
    import subprocess

    proposal(repo)
    (repo / "CLAUDE.md").chmod(0o755)
    # Mode changes are tracked; bind the proposal to the new clean commit.
    commit(repo)
    data = json.loads(
        (repo / WORKSPACE / "reconciliation/application.json").read_bytes()
    )
    data["reviewed_head"] = git(repo, "rev-parse", "HEAD").stdout.decode().strip()
    save_proposal(repo, data)
    before = snapshot(repo)
    real_run = subprocess.run
    real_write = Path.write_bytes

    def checked(command, **kwargs):
        if command[0] == "git":
            return real_run(command, **kwargs)
        return subprocess.CompletedProcess(
            command, int(failure in command), stdout="", stderr="fixture check"
        )

    def write(path, content):
        if failure == "write" and path.name == "accounts.md":
            raise OSError("disk full")
        return real_write(path, content)

    monkeypatch.setattr(subprocess, "run", checked)
    monkeypatch.setattr(Path, "write_bytes", write)
    assert invoke(repo, "--apply") == 1
    assert snapshot(repo) == before
    assert (repo / "CLAUDE.md").stat().st_mode & 0o777 == 0o755
    assert not (repo / WORKSPACE / "validation.json").exists()
    assert "Affected files restored" in capsys.readouterr().err


def test_real_validation_failure_is_reported_and_rolled_back(repo, capsys):
    proposal(repo)
    before = snapshot(repo)
    assert invoke(repo, "--apply") == 1
    assert snapshot(repo) == before
    output = capsys.readouterr().out
    assert "Engineering System Doctor" in output
    assert "Validation doctor: FAIL" in output
    assert "Finalization FAILED" in output


def test_snapshot_policy_retains_exact_sources(repo, monkeypatch):
    import subprocess

    proposal(repo)
    raw_path = repo / WORKSPACE / "inventory.json"
    inventory = json.loads(raw_path.read_bytes())
    inventory["history_policy"] = "snapshot"
    for name in inventory["source_paths"]:
        path = repo / WORKSPACE / "snapshot" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((repo / name).read_bytes())
    raw_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
    data = json.loads(
        (repo / WORKSPACE / "reconciliation/application.json").read_bytes()
    )
    data["inventory_sha256"] = digest(raw_path.read_bytes())
    save_proposal(repo, data)
    real_run = subprocess.run

    def checked(command, **kwargs):
        if command[0] == "git":
            return real_run(command, **kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", checked)
    assert invoke(repo, "--apply") == 0
    assert (
        repo / WORKSPACE / "snapshot/openspec/specs/accounts/spec.md"
    ).read_text() == "# Accounts\nA domain rule.\n"


@pytest.mark.parametrize("effect", ["receipt-symlink", "new-openspec"])
def test_project_checks_cannot_redirect_receipt_or_restore_integration(
    repo, monkeypatch, effect, capsys
):
    import subprocess

    proposal(repo)
    external = repo.parent / f"{repo.name}-external"
    external.write_text("outside bytes")
    real_run = subprocess.run

    def checked(command, **kwargs):
        if command[0] == "git":
            return real_run(command, **kwargs)
        if command == ["make", "check"]:
            if effect == "receipt-symlink":
                (repo / WORKSPACE / "validation.json").symlink_to(external)
            else:
                save(repo, "openspec/recreated.md", "check side effect")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", checked)
    assert invoke(repo, "--apply") == 1
    assert external.read_text() == "outside bytes"
    assert (
        repo / "openspec/specs/accounts/spec.md"
    ).read_text() == "# Accounts\nA domain rule.\n"
    assert (repo / "CLAUDE.md").read_text() == "Project rules\nOpenSpec wiring\n"
    assert not (repo / "docs/context/accounts.md").exists()
    assert "Finalization validation PASS" not in capsys.readouterr().out
