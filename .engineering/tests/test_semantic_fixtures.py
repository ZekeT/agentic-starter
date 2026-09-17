"""Authored examples verify fixture evidence, never autonomous model judgment."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from engineering.cli import main
from engineering.migrate.application import CANONICAL, ROUTES

from .test_migration import commit, repo, snapshot

__all__ = ["repo"]
FIXTURES = Path(__file__).parent / "fixtures" / "openspec-brownfield"


@pytest.mark.parametrize("scenario", ["A", "B", "C", "D", "E", "F"])
def test_brownfield_fixture_evidence_executes(scenario: str, tmp_path: Path) -> None:
    fixture = FIXTURES / scenario
    expected = json.loads((fixture / "expected.json").read_text())
    assert expected["authored_example"] is True
    repo = shutil.copytree(fixture / "repo", tmp_path / "project")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for record in expected["canonical"] + expected["active"]:
        assert record["evidence"]
        for path in record["evidence"]:
            assert (repo / path).is_file(), path
    if scenario == "B":
        assert expected["unresolved_decisions"]
        assert expected["canonical"][0]["classification"] == "CONFLICT_REQUIRES_HUMAN"
    if scenario == "F":
        assert not (repo / ".engineering").exists()
        assert not (repo / "CLAUDE.md").exists()


@pytest.mark.parametrize(
    ("scenario", "state", "route", "blocked"),
    [
        ("A", None, None, False),
        ("B", None, None, True),
        ("C", "DECIDED_NOT_IMPLEMENTED", "to-spec", False),
        ("D", "PARTIALLY_IMPLEMENTED", "to-spec", False),
        ("E", "PLANNING", "wayfinder", True),
        ("F", None, None, False),
    ],
)
def test_authored_handoff_covers_prepared_inventory(
    repo, scenario, state, route, blocked
):
    fixture = FIXTURES / scenario
    shutil.copytree(fixture / "repo", repo, dirs_exist_ok=True)
    commit(repo)
    before = snapshot(repo)
    assert main(["--root", str(repo), "migrate", "openspec-project", "--apply"]) == 0
    inventory = json.loads(
        (repo / ".engineering/migration-work/openspec/inventory.json").read_text()
    )
    expected = json.loads((fixture / "expected.json").read_text())
    assert {record["source"] for record in expected["canonical"]} == {
        capability["path"] for capability in inventory["canonical"]
    }
    assert sorted(record["source"] for record in expected["active"]) == sorted(
        change["name"] for change in inventory["active_changes"]
    )
    for record in expected["canonical"]:
        assert record["classification"] in CANONICAL
        assert record["reason"].strip()
    for record in expected["active"]:
        assert record["state"] == state
        assert record["route"] == route
        assert route in ROUTES[state]
        assert record["implemented"] and record["remaining"] and record["missing_tests"]
    assert bool(expected["unresolved_decisions"]) is blocked
    after = snapshot(repo)
    assert all(after[name] == raw for name, raw in before.items())
    # Authored output stays a proposal, never destination writes during preparation.
    assert all(name not in after for name in expected["proposed_documents"])


def test_migration_skill_and_contract_are_in_distribution():
    root = Path(__file__).parents[2]
    manifest = json.loads((root / ".engineering/manifest.json").read_text())
    prefix = ".claude/skills/migrate-from-openspec/"
    for relative in ("SKILL.md", "references/application-manifest.md"):
        entry = manifest["files"][prefix + relative]
        assert entry["ownership"]["mode"] == "file"
