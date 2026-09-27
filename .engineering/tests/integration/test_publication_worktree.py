"""Publish from a linked Git worktree, where hooks receive an absolute GIT_DIR."""

import shutil

import pytest

from .test_publication import STATE, publish, review
from .test_publication import hosting as hosting
from .test_verification import git
from .test_verification import repo as repo

pytestmark = pytest.mark.integration


def test_linked_worktree_publishes_without_moving_refs(repo, hosting, tmp_path):
    git(repo, "add", "app.txt")
    git(repo, "commit", "-m", "implementation")
    accepted = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "main")
    worktree = tmp_path / "linked"
    git(repo, "worktree", "add", str(worktree), "feature")
    shutil.copytree(repo / STATE, worktree / STATE)
    review(worktree, hosting)
    main = git(repo, "rev-parse", "refs/heads/main")

    result = publish(worktree, "run", "--authorize", "push")

    assert result["completed"] == ["preflight", "commit", "push"]
    assert git(worktree, "rev-parse", "refs/heads/feature") == accepted
    assert git(worktree, "rev-parse", "HEAD") == accepted
    assert git(repo, "rev-parse", "refs/heads/main") == main
    assert git(hosting[0], "rev-parse", "refs/heads/feature") == accepted
    assert git(worktree, "status", "--porcelain") == ""
