"""Authored semantic proposals exercise acceptance/refusal through the finalizer CLI."""

import json
import shutil
import subprocess

import pytest
from engineering.cli import main
from engineering.migrate.openspec import WORKSPACE
from engineering.ownership import digest

from .test_finalization import invoke, save_proposal
from .test_migration import commit, git, repo, save, snapshot
from .test_semantic_fixtures import FIXTURES

__all__ = ["repo"]


@pytest.mark.parametrize("scenario", ["A", "B", "C", "D", "E", "F"])
def test_authored_scenarios_finalize_only_resolved_work(repo, monkeypatch, scenario):
    fixture = FIXTURES / scenario
    shutil.copytree(fixture / "repo", repo, dirs_exist_ok=True)
    save(repo, ".gitignore", f"{WORKSPACE}/\n")
    commit(repo)
    expected = json.loads((fixture / "expected.json").read_text())
    assert main(["--root", str(repo), "migrate", "openspec-project", "--apply"]) == 0
    raw = (repo / WORKSPACE / "inventory.json").read_bytes()
    inventory = json.loads(raw)
    readable = "# Authored fixture proposal\n" + json.dumps(expected, indent=2) + "\n"
    save(repo, f"{WORKSPACE}/reconciliation/plan.md", readable)
    data = {
        "schema_version": 1,
        "inventory_sha256": digest(raw),
        "reviewed_head": git(repo, "rev-parse", "HEAD").stdout.decode().strip(),
        "plan": {"path": "reconciliation/plan.md", "sha256": digest(readable.encode())},
        "writes": [
            {"path": name, "before_sha256": None, "content": content}
            for name, content in expected["proposed_documents"].items()
        ],
        "deletes": [
            {"path": name, "before_sha256": sha}
            for name, sha in inventory["source_paths"].items()
            if name.startswith("openspec/")
        ],
        **{
            key: expected[key]
            for key in ("canonical", "active", "unresolved_decisions")
        },
    }
    save_proposal(repo, data)
    before = snapshot(repo)
    real_run = subprocess.run

    def checked(command, **kwargs):
        if command[0] == "git":
            return real_run(command, **kwargs)
        return subprocess.CompletedProcess(
            command, 0, stdout="fixture gate\n", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", checked)
    assert invoke(repo, "--apply") == int(bool(expected["unresolved_decisions"]))
    after = snapshot(repo)
    if expected["unresolved_decisions"]:
        assert after == before
    else:
        for name, content in expected["proposed_documents"].items():
            assert after[name] == content.encode()
        for name, content in before.items():
            if name.startswith(("src/", "tests/")):
                assert after[name] == content
        assert not any(name.startswith("openspec/") for name in after)
