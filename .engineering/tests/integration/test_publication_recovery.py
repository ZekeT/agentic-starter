"""Resume publication at the public CLI boundary without repeating completed work."""

import json
import os
import shutil
import sys

import pytest

from .test_publication import STATE, publish, review
from .test_publication import hosting as hosting
from .test_verification import change_plan, git, prepare
from .test_verification import repo as repo

pytestmark = pytest.mark.integration


def test_failed_push_reuses_commit_authorization_and_evidence(repo, hosting):
    (repo / "Makefile").write_text(f"check:\n\t@echo check >> {STATE}/calls\n")
    change_plan(repo, paths=["app.txt", "Makefile"])
    review(repo, hosting)
    checkout = repo / prepare(repo)["checkout"]
    evidence = (repo / STATE / "example.json").read_bytes()
    hook = hosting[0] / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["completed"] == ["preflight", "commit"]
    assert result["failed"] == "push"
    assert "publish run --change example" in result["handoff"]
    head = git(repo, "rev-parse", "HEAD")
    hook.unlink()
    result = publish(repo, "run")
    assert result["status"] == "PUBLISHED"
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "rev-list", "--count", "main..HEAD") == "1"
    assert git(hosting[0], "rev-parse", "feature") == head
    assert (checkout / STATE / "calls").read_text() == "check\n"
    assert (repo / STATE / "example.json").read_bytes() == evidence


def test_later_provider_failure_and_uncertain_success_reconcile(repo, hosting):
    review(repo, hosting)
    adapter = repo / STATE / "host.py"
    source = adapter.read_text()
    # Simulate a request that did not create anything on its first attempt.
    adapter.write_text(source.replace("p['body'] =", "sys.exit(7)\np['body'] ="))
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["completed"] == ["preflight", "commit", "push"]
    assert result["failed"] == "pr creation"
    head = git(repo, "rev-parse", "HEAD")
    hook = repo / ".git/hooks/pre-push"
    hook.write_text("#!/bin/sh\nexit 9\n")
    hook.chmod(0o755)
    # The next create succeeds remotely but loses its response.
    adapter.write_text(
        source.replace(
            "print(json.dumps({'url': 'https://hosting.invalid/project/pulls/1'}))",
            "sys.exit(8)",
        )
    )
    result = publish(repo, "run", status=1)
    assert result["failed"] == "pr creation"
    receipt = (repo / STATE / "created.json").read_bytes()
    assert json.loads(receipt)["head"] == head
    # Lookup still works. A duplicate creation would fail (and rewrite receipt).
    result = publish(repo, "run")
    assert result["status"] == "PUBLISHED"
    assert result["url"] == "https://hosting.invalid/project/pulls/1"
    assert (repo / STATE / "created.json").read_bytes() == receipt
    assert git(repo, "rev-parse", "HEAD") == head


def test_failed_lookup_never_creates_and_retry_retains_narrow_scope(repo, hosting):
    review(repo, hosting)
    publish(repo, "run", "--authorize", "commit")
    assert publish(repo, "run")["completed"] == ["preflight", "commit"]
    assert git(hosting[0], "branch", "--list", "feature") == ""
    adapter = repo / STATE / "host.py"
    adapter.write_text("raise SystemExit(9)\n")
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["failed"] == "pr lookup"
    assert not (repo / STATE / "created.json").exists()
    result = publish(repo, "run", "--authorize", "push")
    assert result["completed"] == ["preflight", "commit", "push"]
    assert publish(repo, "run")["completed"] == result["completed"]


def test_changed_content_and_new_review_cannot_reuse_old_authorization(repo, hosting):
    review(repo, hosting)
    publish(repo, "run", "--authorize", "commit")
    (repo / "app.txt").write_text("new unaccepted behavior\n")
    result = publish(repo, "run", status=1)
    assert "STALE evidence" in result["error"]
    review(repo, hosting)
    result = publish(repo, "run", status=1)
    assert "Missing human authorization" in result["error"]
    assert git(hosting[0], "branch", "--list", "feature") == ""


def test_uncertain_push_is_discovered_before_retry(repo, hosting, monkeypatch):
    review(repo, hosting)
    tools = repo / STATE / "bin"
    tools.mkdir()
    wrapper = tools / "git"
    wrapper.write_text(
        f"#!{sys.executable}\nimport subprocess, sys\n"
        f"result = subprocess.run([{shutil.which('git')!r}, *sys.argv[1:]])\n"
        "sys.exit(8 if 'push' in sys.argv else result.returncode)\n"
    )
    wrapper.chmod(0o755)
    monkeypatch.setenv("PATH", str(tools) + ":" + os.environ["PATH"])
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["failed"] == "push"
    assert git(hosting[0], "rev-parse", "feature") == git(repo, "rev-parse", "HEAD")
    assert publish(repo, "run")["status"] == "PUBLISHED"


@pytest.mark.parametrize(
    "reply", [{}, {"url": "bad"}, [], {"url": None, "error": "offline"}]
)
def test_malformed_lookup_cannot_trigger_creation(repo, hosting, reply):
    review(repo, hosting)
    adapter = repo / STATE / "host.py"
    adapter.write_text(f"print({json.dumps(reply)!r})\n")
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["failed"] == "pr lookup"
    assert not (repo / STATE / "created.json").exists()


def test_diverged_remote_is_never_force_pushed(repo, hosting):
    review(repo, hosting)
    publish(repo, "run", "--authorize", "push")
    original = git(repo, "rev-parse", "HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    remote_head = git(repo, "commit-tree", tree, "-p", original, "-m", "someone else")
    git(repo, "push", "origin", f"{remote_head}:feature")
    result = publish(repo, "run", status=1)
    assert result["failed"] == "push"
    assert git(hosting[0], "rev-parse", "feature") == remote_head


@pytest.mark.parametrize(
    "state,head", [("closed", None), ("merged", None), ("open", "0" * 40)]
)
def test_existing_conflicting_request_stops_without_duplicate(
    repo, hosting, state, head
):
    review(repo, hosting)
    publish(repo, "run", "--authorize", "push")
    adapter = repo / STATE / "host.py"
    reply = {
        "url": "https://hosting.invalid/pull/1",
        "head": head or git(repo, "rev-parse", "HEAD"),
        "state": state,
    }
    adapter.write_text(f"print({json.dumps(reply)!r})\n")
    result = publish(repo, "run", "--authorize", "pr", status=1)
    assert result["failed"] == "pr lookup"
    assert "different content or is closed/merged" in result["error"]
    assert not (repo / STATE / "created.json").exists()
