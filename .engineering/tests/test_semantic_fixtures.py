"""Authored examples verify fixture evidence, never autonomous model judgment."""

import json
import subprocess
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "openspec-brownfield"


@pytest.mark.parametrize("scenario", ["A", "B", "C", "D", "E", "F"])
def test_brownfield_fixture_evidence_executes(scenario: str) -> None:
    fixture = FIXTURES / scenario
    expected = json.loads((fixture / "expected.json").read_text())
    assert expected["authored_example"] is True
    repo = fixture / "repo"
    result = subprocess.run(
        ["python3", "-m", "unittest", "discover", "-s", "tests"],
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
