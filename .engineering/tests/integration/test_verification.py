"""Exercise reusable verification through the CLI in disposable repositories."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOLING = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.integration


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def cli(root, *args, status=0):
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from engineering.cli import main; raise SystemExit(main())",
            "--root",
            str(root),
            "verify",
            *args,
        ],
        env={**os.environ, "PYTHONPATH": str(TOOLING)},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == status, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Fixture")
    (tmp_path / ".gitignore").write_text(".engineering/state/verification/\n")
    (tmp_path / "Makefile").write_text("check:\n\t@test -s app.txt\n")
    (tmp_path / "app.txt").write_text("before\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "baseline")
    git(tmp_path, "checkout", "-b", "feature")
    (tmp_path / "app.txt").write_text("after\n")
    state = tmp_path / ".engineering/state/verification"
    state.mkdir(parents=True)
    plan = {
        "base": "main",
        "requirement": "Implement the fixture change",
        "paths": ["app.txt"],
        "checks": [["make", "check"]],
        "tools": [[sys.executable, "--version"]],
        "inputs": [],
        "security_required": False,
        "security_reason": "Fixture text has no security-sensitive behavior",
    }
    (state / "plan.json").write_text(json.dumps(plan))
    return tmp_path


def prepare(root):
    return cli(
        root,
        "prepare",
        "--change",
        "example",
        "--plan",
        ".engineering/state/verification/plan.json",
    )


def report(root, token, role, verdict="PASS", expected=0):
    path = root / ".engineering/state/verification/report.json"
    path.write_text(
        json.dumps(
            {
                "snapshot": token,
                "role": role,
                "reviewer": f"fresh-{role}-session",
                "independent": True,
                "verdict": verdict,
                "summary": "Inspected fixture behavior against the requirement",
                "findings": [],
                "coverage_gaps": ["No live provider tested"],
            }
        )
    )
    return cli(
        root,
        "record",
        "--change",
        "example",
        "--report",
        ".engineering/state/verification/report.json",
        status=expected,
    )


def complete(root):
    token = prepare(root)["snapshot"]
    cli(root, "check", "--change", "example", "--snapshot", token)
    report(root, token, "maintainability")
    report(root, token, "behavioral")
    return token


def test_reuse_across_sessions_and_content_preserving_commit(repo):
    assert prepare(repo)["status"] == "INCOMPLETE"
    complete(repo)
    assert cli(repo, "status", "--change", "example")["status"] == "PASS"
    git(repo, "add", "app.txt")
    git(repo, "commit", "-m", "implementation")
    assert cli(repo, "status", "--change", "example")["status"] == "PASS"
    assert prepare(repo)["status"] == "PASS"
    (repo / "app.txt").write_text("new correction\n")
    assert cli(repo, "status", "--change", "example", status=1)["status"] == "STALE"


def change_plan(root, **changes):
    path = root / ".engineering/state/verification/plan.json"
    plan = json.loads(path.read_text())
    path.write_text(json.dumps({**plan, **changes}))


def test_moved_comparison_branch_invalidates_even_with_same_merge_base(repo):
    complete(repo)
    old = git(repo, "rev-parse", "main")
    tree = git(repo, "rev-parse", "main^{tree}")
    new = git(repo, "commit-tree", tree, "-p", old, "-m", "base advanced")
    git(repo, "update-ref", "refs/heads/main", new)
    assert cli(repo, "status", "--change", "example", status=1)["status"] == "STALE"


def test_untracked_and_deleted_content_survives_commit(repo):
    (repo / "new.txt").write_text("new behavior\n")
    (repo / "app.txt").unlink()
    (repo / "Makefile").write_text("check:\n\t@test -s new.txt\n")
    change_plan(repo, paths=["app.txt", "new.txt", "Makefile"])
    complete(repo)
    git(repo, "add", "app.txt", "new.txt", "Makefile")
    git(repo, "commit", "-m", "replace app")
    assert cli(repo, "status", "--change", "example")["status"] == "PASS"


def test_unrelated_edits_refuse_without_changing_files(repo):
    complete(repo)
    (repo / "unrelated.txt").write_text("must survive\n")
    result = cli(repo, "status", "--change", "example", status=1)
    assert "Unrelated" in result["error"]
    assert (repo / "unrelated.txt").read_text() == "must survive\n"


def test_failed_checks_and_missing_security_cannot_pass(repo):
    change_plan(repo, security_required=True)
    token = complete(repo)
    result = cli(repo, "status", "--change", "example", status=1)
    assert result["missing"] == ["security"]
    report(repo, token, "security", "FAIL")
    assert cli(repo, "status", "--change", "example", status=1)["status"] == "FAIL"
    (repo / "Makefile").write_text("check:\n\t@exit 7\n")
    change_plan(repo, paths=["app.txt", "Makefile"], security_required=False)
    token = prepare(repo)["snapshot"]
    assert (
        cli(repo, "check", "--change", "example", "--snapshot", token, status=1)[
            "status"
        ]
        == "FAIL"
    )


def test_tool_versions_and_ignored_explicit_inputs_invalidate(repo):
    version = repo / ".engineering/state/verification/tool-version"
    version.write_text("1.0\n")
    dependency = repo / ".engineering/state/verification/installed"
    # Input cannot live inside evidence storage; use a separately ignored location.
    (repo / ".gitignore").write_text(".engineering/state/verification/\ninstalled\n")
    dependency = repo / "installed"
    dependency.write_text("pin-a\n")
    change_plan(
        repo,
        paths=["app.txt", ".gitignore"],
        inputs=["installed"],
        tools=[["cat", str(version)]],
    )
    complete(repo)
    version.write_text("2.0\n")
    assert cli(repo, "status", "--change", "example", status=1)["status"] == "STALE"
    complete(repo)
    dependency.write_text("pin-b\n")
    assert cli(repo, "status", "--change", "example", status=1)["status"] == "STALE"


def test_check_mutations_never_produce_current_proof(repo):
    (repo / "Makefile").write_text("check:\n\t@echo mutated >> app.txt\n")
    change_plan(repo, paths=["app.txt", "Makefile"])
    token = prepare(repo)["snapshot"]
    result = cli(repo, "check", "--change", "example", "--snapshot", token, status=1)
    assert "mutated" in result["error"]
    assert cli(repo, "status", "--change", "example", status=1)["status"] == "STALE"


@pytest.mark.parametrize("kind", ["secret", "symlink", "bad-record"])
def test_unsafe_or_malformed_evidence_fails_closed(repo, kind):
    complete(repo)
    if kind == "secret":
        change_plan(repo, inputs=[".env.local"])
    elif kind == "symlink":
        (repo / "app.txt").unlink()
        (repo / "app.txt").symlink_to("Makefile")
    else:
        record = repo / ".engineering/state/verification/example.json"
        data = json.loads(record.read_text())
        data["reports"]["behavioral"] = {"verdict": "PASS"}
        record.write_text(json.dumps(data))
    args = (
        [
            "prepare",
            "--change",
            "example",
            "--plan",
            ".engineering/state/verification/plan.json",
        ]
        if kind == "secret"
        else ["status", "--change", "example"]
    )
    result = cli(repo, *args, status=1)
    assert result["status"] == "INCOMPLETE"


def test_missing_and_stale_reports_do_not_claim_verification(repo):
    assert (
        cli(repo, "status", "--change", "example", status=1)["status"] == "INCOMPLETE"
    )
    token = prepare(repo)["snapshot"]
    result = report(repo, token, "behavioral", expected=1)
    assert "successful recorded" in result["error"]
    report(repo, token, "maintainability")
    result = cli(repo, "status", "--change", "example", status=1)
    assert "behavioral" in result["missing"]
    assert "Fresh read-only reviewer" in result["handoff"]
    (repo / "app.txt").write_text("correction\n")
    prepare(repo)
    assert "STALE report" in report(repo, token, "maintainability", expected=1)["error"]


def test_status_and_reprepare_do_not_rerun_checks(repo):
    (repo / "Makefile").write_text(
        "check:\n\t@echo check >> .engineering/state/verification/calls\n"
    )
    change_plan(repo, paths=["app.txt", "Makefile"])
    complete(repo)
    for _ in range(2):
        assert cli(repo, "status", "--change", "example")["status"] == "PASS"
        assert prepare(repo)["status"] == "PASS"
    assert (repo / ".engineering/state/verification/calls").read_text() == "check\n"
