"""Advance the active story file when its branch's PR changes state.

Runs on Claude Code Stop events. No-op unless the current git branch matches
`feat/story-*` (the only prefix `_branch_slug` currently parses, despite what
older revisions of this docstring claimed about fix/*  and chore/*).

  - PR state OPEN: move stories/in-progress/{slug}.md -> stories/review/,
    in this checkout (normally a feature-branch worktree).
  - PR state MERGED: the feature branch is already fully landed in main, so
    a rename made *in the worktree* would never reach main — there's no
    future merge to carry it. Instead this moves
    stories/review/{slug}.md -> stories/done/ in the *main* checkout (found
    via git-common-dir), then best-effort removes the now-merged worktree
    and its branch (branch existence is the claim mutex, so this also
    releases it). The reliable cleanup path is still the sweep in
    .claude/commands/dev-story.md — this is just a faster path when a
    session happens to still be open post-merge.

Idempotent: if the story has already moved or no PR exists, exits 0 silently.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INPROG = REPO / "stories" / "in-progress"
REVIEW = REPO / "stories" / "review"


def _run(cmd: list[str], cwd: Path) -> str | None:
    """Return stdout of `cmd` run in `cwd`, or None on non-zero exit."""
    try:
        out = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True, timeout=10
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
    return _run(["git", "branch", "--show-current"], cwd=REPO)


def _branch_slug(branch: str) -> str | None:
    """Extract the story slug portion of a feat/story-* branch name."""
    prefix = "feat/story-"
    if not branch.startswith(prefix):
        return None
    return branch[len(prefix) :]


def _pr_state() -> str | None:
    """Return the current branch's PR state (e.g. "OPEN", "MERGED"), or None."""
    out = _run(["gh", "pr", "view", "--json", "state"], cwd=REPO)
    if not out:
        return None
    try:
        state = json.loads(out).get("state")
    except json.JSONDecodeError:
        return None
    return state if isinstance(state, str) else None


def _find_story(directory: Path, slug: str) -> Path | None:
    """Find a story file in `directory` matching `slug`."""
    if not directory.is_dir():
        return None
    for path in directory.glob("*.md"):
        if slug in path.stem:
            return path
    return None


def _move(story: Path, target_dir: Path, label: str) -> None:
    """Move `story` into `target_dir`, no-op if already there."""
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / story.name
    if target.exists():
        return
    story.rename(target)
    print(f"[stop_story_lifecycle] moved {story.name} -> {label}/", file=sys.stderr)


def _main_repo_root() -> Path | None:
    """Return the main checkout's root if REPO is itself a worktree, else None."""
    git_dir = _run(["git", "rev-parse", "--git-dir"], cwd=REPO)
    common_dir = _run(["git", "rev-parse", "--git-common-dir"], cwd=REPO)
    if not git_dir or not common_dir:
        return None
    git_dir_path = (
        Path(git_dir) if Path(git_dir).is_absolute() else (REPO / git_dir).resolve()
    )
    common_dir_path = (
        Path(common_dir)
        if Path(common_dir).is_absolute()
        else (REPO / common_dir).resolve()
    )
    if git_dir_path == common_dir_path:
        return None  # not a worktree
    if common_dir_path.name != ".git":
        return None
    main_root = common_dir_path.parent
    return main_root if main_root.is_dir() else None


def _remove_worktree(main_root: Path, branch: str) -> None:
    """Best-effort: remove REPO's worktree and its branch from `main_root`."""
    if _run(["git", "worktree", "remove", "--force", str(REPO)], cwd=main_root) is None:
        return
    _run(["git", "branch", "-d", branch], cwd=main_root)


def main() -> int:
    """Advance the in-progress/review story based on its branch's PR state."""
    branch = _current_branch()
    if not branch:
        return 0
    slug = _branch_slug(branch)
    if not slug:
        return 0
    state = _pr_state()
    if state == "OPEN":
        story = _find_story(INPROG, slug)
        if story is not None:
            _move(story, REVIEW, "stories/review")
    elif state == "MERGED":
        main_root = _main_repo_root()
        stories_root = main_root if main_root is not None else REPO
        review_dir = stories_root / "stories" / "review"
        done_dir = stories_root / "stories" / "done"
        story = _find_story(review_dir, slug)
        if story is not None:
            _move(story, done_dir, "stories/done")
        if main_root is not None:
            _remove_worktree(main_root, branch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
