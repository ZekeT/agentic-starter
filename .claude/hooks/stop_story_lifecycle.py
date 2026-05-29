"""Move the active story file to stories/review/ when a PR exists for the branch.

Runs on Claude Code Stop events. No-op unless:
  - the current git branch matches feat/story-*, fix/*, or chore/*
  - a story file with a matching slug lives in stories/in-progress/
  - `gh pr view` reports an open PR for the branch

Idempotent: if the story is already in review/ or no PR exists, exits 0 silently.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INPROG = REPO / "stories" / "in-progress"
REVIEW = REPO / "stories" / "review"


def _run(cmd: list[str]) -> str | None:
    """Return stdout of `cmd` or None on non-zero exit."""
    try:
        out = subprocess.run(
            cmd, cwd=REPO, check=True, capture_output=True, text=True, timeout=10
        )
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):
        return None
    return out.stdout.strip()


def _current_branch() -> str | None:
    """Return the current git branch name."""
    return _run(["git", "branch", "--show-current"])


def _branch_slug(branch: str) -> str | None:
    """Extract the story slug portion of a feat/story-* branch name."""
    prefix = "feat/story-"
    if not branch.startswith(prefix):
        return None
    return branch[len(prefix) :]


def _has_open_pr() -> bool:
    """Return True iff `gh pr view` reports an open PR for the current branch."""
    out = _run(["gh", "pr", "view", "--json", "state"])
    if not out:
        return False
    try:
        return json.loads(out).get("state") == "OPEN"
    except json.JSONDecodeError:
        return False


def _find_story(slug: str) -> Path | None:
    """Find a story file in in-progress/ matching `slug`."""
    if not INPROG.is_dir():
        return None
    for path in INPROG.glob("*.md"):
        if slug in path.stem:
            return path
    return None


def main() -> int:
    """Move the in-progress story to review/ when its PR is open."""
    branch = _current_branch()
    if not branch:
        return 0
    slug = _branch_slug(branch)
    if not slug:
        return 0
    story = _find_story(slug)
    if story is None:
        return 0
    if not _has_open_pr():
        return 0
    REVIEW.mkdir(parents=True, exist_ok=True)
    target = REVIEW / story.name
    if target.exists():
        return 0
    story.rename(target)
    print(
        f"[stop_story_lifecycle] moved {story.name} -> stories/review/", file=sys.stderr
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
