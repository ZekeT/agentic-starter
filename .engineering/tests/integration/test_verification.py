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


INSTALL_STATE = ".engineering/state/install.json"


def record_role(root, role):
    state = {"schema_version": 1, "installed_version": "3.0.0", "entries": {}}
    if role is not None:
        state["role"] = role
    path = root / INSTALL_STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Fixture")
    (tmp_path / ".gitignore").write_text(".engineering/state/verification/\n")
    (tmp_path / "Makefile").write_text("check:\n\t@test -s app.txt\n")
    (tmp_path / "app.txt").write_text("before\n")
    record_role(tmp_path, "consumer")
    # Ownership comes from the installation manifest; this fixture owns nothing.
    (tmp_path / ".engineering/manifest.json").write_text('{"files": {}}')
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


def prepare(root, status=0):
    return cli(
        root,
        "prepare",
        "--change",
        "example",
        "--plan",
        ".engineering/state/verification/plan.json",
        status=status,
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


def test_unrelated_edits_preserve_current_evidence(repo):
    complete(repo)
    (repo / "unrelated.txt").write_text("must survive\n")
    result = cli(repo, "status", "--change", "example")
    assert result["status"] == "PASS"
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
    assert (
        cli(repo, "status", "--change", "example", status=1)["status"] == "INCOMPLETE"
    )
    assert (repo / "app.txt").read_text() == "after\n"
    assert prepare(repo)["status"] == "INCOMPLETE"


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
    checkout = repo / prepare(repo)["checkout"]
    for _ in range(2):
        assert cli(repo, "status", "--change", "example")["status"] == "PASS"
        assert prepare(repo)["status"] == "PASS"
    assert (checkout / ".engineering/state/verification/calls").read_text() == "check\n"


def test_unrelated_local_fix_cannot_make_proposal_pass(repo):
    (repo / "Makefile").write_text("check:\n\t@test -f unrelated.txt\n")
    change_plan(repo, paths=["app.txt", "Makefile"])
    (repo / "unrelated.txt").write_text("local rescue\n")
    subprocess.run(["make", "check"], cwd=repo, check=True)
    before = git(repo, "status", "--porcelain=v1")
    token = prepare(repo)["snapshot"]
    result = cli(repo, "check", "--change", "example", "--snapshot", token, status=1)
    assert result["status"] == "FAIL"
    assert (repo / "unrelated.txt").read_text() == "local rescue\n"
    assert git(repo, "status", "--porcelain=v1") == before


def test_checkout_contains_intended_layers_and_preserves_index(repo):
    (repo / "committed.txt").write_text("committed\n")
    git(repo, "add", "committed.txt")
    git(repo, "commit", "-m", "intended commit")
    (repo / "staged.txt").write_text("staged\n")
    git(repo, "add", "staged.txt")
    (repo / "new.sh").write_text("#!/bin/sh\nexit 0\n")
    (repo / "new.sh").chmod(0o755)
    (repo / "Makefile").write_text(
        "check:\n\t@test -s committed.txt && test -s staged.txt && "
        'test -x new.sh && test "`cat app.txt`" = after\n'
    )
    change_plan(
        repo, paths=["app.txt", "Makefile", "committed.txt", "staged.txt", "new.sh"]
    )
    (repo / ".gitignore").write_text(
        "unrelated staged edit\n.engineering/state/verification/\n"
    )
    git(repo, "add", ".gitignore")
    (repo / ".gitignore").write_text(
        "unrelated unstaged edit\n.engineering/state/verification/\n"
    )
    before = git(repo, "diff", "--cached", "--binary")
    working = git(repo, "diff", "--binary")
    token = complete(repo)
    assert cli(repo, "status", "--change", "example")["snapshot"] == token
    checkout = repo / prepare(repo)["checkout"]
    assert (checkout / ".gitignore").read_text() == ".engineering/state/verification/\n"
    assert git(repo, "diff", "--cached", "--binary") == before
    assert git(repo, "diff", "--binary") == working


def test_committed_changes_cannot_be_omitted_from_proposed_pr(repo):
    (repo / "omitted.txt").write_text("part of PR\n")
    git(repo, "add", "omitted.txt")
    git(repo, "commit", "-m", "cannot exclude committed content")
    result = cli(
        repo,
        "prepare",
        "--change",
        "example",
        "--plan",
        ".engineering/state/verification/plan.json",
        status=1,
    )
    assert "Committed PR changes missing" in result["error"]
    assert (repo / "app.txt").read_text() == "after\n"


def test_review_checkout_mutation_invalidates_reports_and_reprepare_recovers(repo):
    token = complete(repo)
    checkout = repo / prepare(repo)["checkout"]
    (checkout / "unexpected.txt").write_text("review mutation\n")
    assert (
        cli(repo, "status", "--change", "example", status=1)["status"] == "INCOMPLETE"
    )
    assert report(repo, token, "maintainability", expected=1)["status"] == "INCOMPLETE"
    assert prepare(repo)["status"] == "INCOMPLETE"
    assert (repo / "app.txt").read_text() == "after\n"


def test_failed_preparation_preserves_unrelated_work(repo):
    (repo / "unrelated.txt").write_text("preserved\n")
    change_plan(repo, tools=[["missing-verification-tool", "--version"]])
    before = git(repo, "status", "--porcelain=v1")
    result = cli(
        repo,
        "prepare",
        "--change",
        "example",
        "--plan",
        ".engineering/state/verification/plan.json",
        status=1,
    )
    assert result["status"] == "INCOMPLETE"
    assert git(repo, "status", "--porcelain=v1") == before
    assert (repo / "unrelated.txt").read_text() == "preserved\n"


def test_legacy_evidence_is_reprepared_without_reusing_reports(repo):
    complete(repo)
    path = repo / ".engineering/state/verification/example.json"
    legacy = json.loads(path.read_text())
    del legacy["checkout"]
    path.write_text(json.dumps(legacy))
    assert (
        cli(repo, "status", "--change", "example", status=1)["status"] == "INCOMPLETE"
    )
    result = prepare(repo)
    assert result["status"] == "INCOMPLETE"
    assert result["reports"] == {}
    assert result["checks"] == []
    assert (repo / result["checkout"] / "app.txt").read_text() == "after\n"


def test_bounded_correction_preserves_history_but_requires_fresh_proof(repo):
    old_token = complete(repo)
    (repo / "app.txt").write_text("authorized correction\n")
    current = prepare(repo)
    assert current["snapshot"] != old_token
    assert current["status"] == "INCOMPLETE"
    assert current["checks"] == []
    assert current["reports"] == {}
    history = repo / current["previous_evidence"]
    previous = json.loads(history.read_text())
    assert previous["snapshot"] == old_token
    assert previous["reports"]["behavioral"]["verdict"] == "PASS"
    assert "STALE report" in report(repo, old_token, "behavioral", expected=1)["error"]
    assert (
        "successful recorded"
        in report(repo, current["snapshot"], "behavioral", expected=1)["error"]
    )
    cli(repo, "check", "--change", "example", "--snapshot", current["snapshot"])
    report(repo, current["snapshot"], "behavioral")
    assert cli(repo, "status", "--change", "example", status=1)["missing"] == [
        "maintainability"
    ]
    report(repo, current["snapshot"], "maintainability")
    assert prepare(repo)["status"] == "PASS"
    assert prepare(repo)["previous_evidence"] == current["previous_evidence"]
    assert json.loads(history.read_text()) == previous
    assert git(repo, "diff", "--name-only") == "app.txt"


def commit_base_role(root, role):
    """Advance the base with committed install state; the feature follows it."""
    git(root, "checkout", "--quiet", "main")
    if role == "absent":
        git(root, "rm", "--quiet", INSTALL_STATE)
    else:
        record_role(root, role)
        git(root, "add", INSTALL_STATE)
    git(root, "commit", "--quiet", "-m", "install state")
    git(root, "checkout", "--quiet", "feature")
    git(root, "merge", "--quiet", "--ff-only", "main")


@pytest.mark.parametrize("role", [None, "absent"])
def test_missing_installation_role_blocks_planning_with_next_step(repo, role):
    commit_base_role(repo, role)
    result = prepare(repo, 1)
    assert result["status"] == "INCOMPLETE"
    assert "role" in result["error"] and "engineering update" in result["error"]
    assert not (repo / ".engineering/state/verification/example.json").exists()


def test_invalid_installation_role_fails_visibly(repo):
    commit_base_role(repo, "owner")
    result = prepare(repo, 1)
    assert result["status"] == "INCOMPLETE" and "owner" in result["error"]


def test_out_of_scope_role_edit_is_ignored(repo):
    # The committed role governs; an uncommitted edit outside the plan cannot remove it.
    record_role(repo, None)
    assert prepare(repo)["status"] == "INCOMPLETE"
    assert cli(repo, "status", "--change", "example", status=1)["missing"]
    # Nor can such an edit supply a role the committed state lacks.
    commit_base_role(repo, None)
    record_role(repo, "consumer")
    assert "not recorded" in prepare(repo, 1)["error"]
    assert cli(repo, "status", "--change", "example", status=1)["status"] != "PASS"
    # A proposed role counts when the install state is within the plan's scope.
    change_plan(
        repo,
        paths=["app.txt", INSTALL_STATE],
        checks=[
            ["make", "check"],
            ["make", "engineering-test"],
            ["make", "engineering-evals"],
        ],
    )
    assert prepare(repo)["status"] == "INCOMPLETE"


@pytest.mark.parametrize(
    "provider,roots,required",
    [("graft", ["src"], True), ("graft", [], False), ("none", ["src"], False)],
)
def test_graft_check_required_only_when_selected_with_roots(
    repo, provider, roots, required
):
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("VALUE = 1\n")
    (repo / ".engineering/config.toml").write_text(
        f'schema_version = 1\n[navigation]\nprovider = "{provider}"\n'
        f"application_roots = {json.dumps(roots)}\n"
    )
    # Configuration changes may carry further checks; this asserts only Graft's.
    checks = [["make", target] for target in ("check", "engineering-check")]
    checks += [["make", "engineering-test"], ["make", "engineering-evals"]]
    change_plan(
        repo,
        paths=["app.txt", ".engineering/config.toml", "src/app.py"],
        checks=checks,
    )
    if required:
        result = cli(
            repo,
            "prepare",
            "--change",
            "example",
            "--plan",
            ".engineering/state/verification/plan.json",
            status=1,
        )
        assert "Graft check" in result["error"]
    else:
        assert prepare(repo)["status"] == "INCOMPLETE"
