"""Exercise real Git publication and fake hosting through the public CLI."""

import json
import os
import subprocess
import sys

import pytest

from .test_verification import TOOLING, change_plan, complete, git, prepare
from .test_verification import repo as repo

pytestmark = pytest.mark.integration
STATE = ".engineering/state/verification"


def publish(root, operation, *args, status=0):
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from engineering.cli import main; raise SystemExit(main())",
            "--root",
            str(root),
            "publish",
            operation,
            "--change",
            "example",
            *args,
        ],
        env={**os.environ, "PYTHONPATH": str(TOOLING)},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == status, proc.stdout + proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture
def hosting(repo, tmp_path):
    remote = tmp_path / "remote.git"
    git(repo, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "origin", "main")
    adapter = repo / STATE / "host.py"
    adapter.write_text(
        "import json, pathlib, sys\n"
        "p = json.loads(pathlib.Path(sys.argv[2]).read_text())\n"
        "p['body'] = pathlib.Path(p['body_file']).read_text()\n"
        f"pathlib.Path({str(repo / STATE / 'created.json')!r}).write_text(json.dumps(p))\n"
        "print(json.dumps({'url': 'https://hosting.invalid/project/pulls/1'}))\n"
    )
    return remote, [sys.executable, str(adapter)]


def review(repo, hosting, **overrides):
    token = complete(repo)
    plan = {
        "snapshot": token,
        "summary": "Change fixture behavior after independent review.",
        "blockers": [],
        "branch": "feature",
        "remote": "origin",
        "remote_url": str(hosting[0]),
        "base": "main",
        "provider": hosting[1],
        "title": "feat: change fixture behavior",
        **overrides,
    }
    path = repo / STATE / "acceptance.json"
    path.write_text(json.dumps(plan))
    return publish(repo, "review", "--plan", f"{STATE}/acceptance.json")


def test_committed_implementation_and_uncommitted_fix_publish_once(repo, hosting):
    git(repo, "add", "app.txt")
    git(repo, "commit", "-m", "implementation")
    implementation = git(repo, "rev-parse", "HEAD")
    (repo / "app.txt").write_text("accepted correction\n")
    (repo / "Makefile").write_text(f"check:\n\t@echo check >> {STATE}/calls\n")
    change_plan(repo, paths=["app.txt", "Makefile"])
    review(repo, hosting)
    checkout = repo / prepare(repo)["checkout"]
    (repo / "unrelated.txt").write_text("staged\n")
    git(repo, "add", "unrelated.txt")
    (repo / "unrelated.txt").write_text("working\n")
    staged = git(repo, "diff", "--cached", "--binary", "--", "unrelated.txt")
    result = publish(repo, "run", "--authorize", "pr")
    assert result["status"] == "PUBLISHED"
    assert result["url"] == "https://hosting.invalid/project/pulls/1"
    assert git(repo, "rev-parse", "HEAD^") == implementation
    assert git(hosting[0], "show", "feature:app.txt") == "accepted correction"
    assert git(repo, "diff", "--cached", "--binary", "--", "unrelated.txt") == staged
    assert (repo / "unrelated.txt").read_text() == "working\n"
    assert (checkout / STATE / "calls").read_text() == "check\n"
    receipt = json.loads((repo / STATE / "created.json").read_text())
    assert "make check" in receipt["body"]
    assert "No live provider tested" in receipt["body"]
    assert "unrelated.txt" not in receipt["body"]


@pytest.mark.parametrize(
    "failure",
    [
        "missing-review",
        "missing-evidence",
        "stale",
        "blockers",
        "authorization",
        "branch",
        "remote",
        "base",
    ],
)
def test_preflight_rejects_without_mutation(repo, hosting, failure):
    review(
        repo,
        hosting,
        blockers=["Defect awaiting human instruction"] if failure == "blockers" else [],
    )
    if failure == "missing-review":
        (repo / STATE / "example-review.json").unlink()
    elif failure == "missing-evidence":
        (repo / STATE / "example.json").unlink()
    elif failure == "stale":
        (repo / "app.txt").write_text("not accepted\n")
    elif failure == "branch":
        git(repo, "checkout", "-b", "other")
    elif failure == "remote":
        git(repo, "remote", "set-url", "--push", "origin", "/missing")
    elif failure == "base":
        old = git(repo, "rev-parse", "main")
        tree = git(repo, "rev-parse", "main^{tree}")
        new = git(repo, "commit-tree", tree, "-p", old, "-m", "remote base moves")
        git(repo, "push", "origin", f"{new}:main")
    before = git(repo, "status", "--porcelain=v1")
    head = git(repo, "rev-parse", "HEAD")
    args = [] if failure == "authorization" else ["--authorize", "pr"]
    result = publish(repo, "run", *args, status=1)
    assert result["status"] == "STOPPED"
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain=v1") == before
    assert not (repo / STATE / "created.json").exists()
    assert git(hosting[0], "branch", "--list", "feature") == ""


@pytest.mark.parametrize(
    "hook,script",
    [
        ("pre-commit", "exit 7"),
        ("pre-commit", "echo mutation > app.txt\ngit add app.txt"),
        ("post-commit", "echo mutation > app.txt"),
        ("pre-push", "exit 7"),
        ("pre-push", "echo mutation > app.txt"),
        (
            "pre-push",
            "echo mutation > app.txt\ngit add app.txt\ngit commit -m mutation",
        ),
    ],
)
def test_hooks_enforced_and_mutations_stop_before_transport(
    repo, hosting, hook, script
):
    review(repo, hosting)
    hooks = repo / STATE / "custom-hooks"
    hooks.mkdir()
    git(repo, "config", "core.hooksPath", str(hooks))
    path = hooks / hook
    path.write_text("#!/bin/sh\n" + script + "\n")
    path.chmod(0o755)
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["status"] == "STOPPED"
    assert "push" not in result["completed"]
    assert not (repo / STATE / "created.json").exists()
    assert git(hosting[0], "branch", "--list", "feature") == ""


@pytest.mark.parametrize("authorization", ["commit", "push"])
def test_narrow_authorization(repo, hosting, authorization):
    review(repo, hosting)
    result = publish(repo, "run", "--authorize", authorization)
    assert result["completed"] == ["preflight", "commit"] + (
        ["push"] if authorization == "push" else []
    )
    assert result["url"] is None
    assert not (repo / STATE / "created.json").exists()


def test_provider_failure_reports_successful_commit_and_push(repo, hosting):
    hosting[1].append("wrong-argument")
    review(repo, hosting)
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["completed"] == ["preflight", "commit", "push"]
    assert git(hosting[0], "rev-parse", "feature") == git(repo, "rev-parse", "HEAD")


def test_reverification_does_not_transfer_acceptance(repo, hosting):
    review(repo, hosting)
    (repo / "app.txt").write_text("fresh correction\n")
    complete(repo)
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert "STALE acceptance" in result["error"]
    assert result["completed"] == []


def test_prior_committed_deletion_with_remaining_fix(repo, hosting):
    (repo / "extra.txt").write_text("temporary\n")
    git(repo, "add", "app.txt", "extra.txt")
    git(repo, "commit", "-m", "implementation")
    git(repo, "rm", "extra.txt")
    git(repo, "commit", "-m", "remove extra")
    (repo / "app.txt").write_text("accepted correction\n")
    change_plan(repo, paths=["app.txt", "extra.txt"])
    review(repo, hosting)
    assert publish(repo, "run", "--authorize", "pr")["status"] == "PUBLISHED"


def test_successful_pre_push_hook_receives_arguments_and_stdin(repo, hosting):
    review(repo, hosting)
    hook = repo / ".git/hooks/pre-push"
    hook.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$@" > {STATE}/hook-args\ncat > {STATE}/hook-input\n'
    )
    hook.chmod(0o755)
    publish(repo, "run", "--authorize", "pr")
    assert (repo / STATE / "hook-args").read_text().splitlines() == [
        "origin",
        str(hosting[0]),
    ]
    assert "refs/heads/feature" in (repo / STATE / "hook-input").read_text()
