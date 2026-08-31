# /dev-story

Develop a story end-to-end using the Superpowers `subagent-driven-development`
skill, in an isolated git worktree per story. Handles the
`ready/ → in-progress/ → review/` lifecycle automatically so you never have
to `mv` story files by hand.

Usage:
- `/dev-story 001` — work on a specific story id
- `/dev-story story-001-slug` — or pass the full slug
- `/dev-story` — pick the lowest-numbered unclaimed story in `stories/ready/`

The mutex that stops two sessions from picking the same story is branch
existence, not file location: claiming a story means successfully creating
its `feat/story-{slug}` worktree/branch. The `ready/ → in-progress/` file
move happens *inside* that worktree as its first commit, so it only becomes
visible in the shared checkout once the PR merges.

---

```bash
set -e

ARG="$ARGUMENTS"
READY=stories/ready

# Sweep worktrees for already-merged stories before claiming a new one, so
# they don't pile up on disk. Best-effort — never blocks story selection.
if command -v git >/dev/null 2>&1 && command -v gh >/dev/null 2>&1; then
  git worktree list --porcelain 2>/dev/null | awk '
    /^worktree /  { path=$2 }
    /^branch refs\/heads\/feat\/story-/ { branch=$2; sub("refs/heads/", "", branch); print path"\t"branch }
  ' | while IFS=$'\t' read -r WT_PATH WT_BRANCH; do
    # Merged is a PR-state fact, not "no commits diverged from main yet" —
    # a freshly claimed, untouched branch is trivially an ancestor of main
    # and must not be swept.
    PR_STATE=$(gh pr view "$WT_BRANCH" --json state -q .state 2>/dev/null || true)
    if [ "$PR_STATE" = "MERGED" ]; then
      if git worktree remove "$WT_PATH" 2>/dev/null; then
        git branch -d "$WT_BRANCH" 2>/dev/null || true
        echo "swept merged worktree: $WT_PATH ($WT_BRANCH)"
      fi
    fi
  done
fi

# Resolve candidate story file(s) to work on
if [ -z "$ARG" ]; then
  CANDIDATES=$(ls -1 "$READY"/*.md 2>/dev/null | sort || true)
  if [ -z "$CANDIDATES" ]; then
    echo "ERROR: no stories in $READY/. Move one from draft/ first." >&2
    exit 1
  fi
else
  STORY_FILE=""
  for candidate in \
    "$READY/$ARG.md" \
    "$READY/$ARG" \
    "$READY/story-$ARG.md"; do
    if [ -f "$candidate" ]; then STORY_FILE="$candidate"; break; fi
  done
  if [ -z "$STORY_FILE" ]; then
    STORY_FILE=$(find "$READY" -maxdepth 1 -name "*${ARG}*.md" | sort | head -n 1 || true)
  fi
  if [ -z "$STORY_FILE" ] || [ ! -f "$STORY_FILE" ]; then
    echo "ERROR: no story matching '$ARG' in $READY/" >&2
    ls -1 "$READY" >&2 || true
    exit 1
  fi
  CANDIDATES="$STORY_FILE"
fi

# Claim a story by winning the race to create its worktree/branch. First
# successful `git worktree add` wins; a failure means another session
# already claimed that slug.
CLAIMED_PATH=""
CLAIMED_SLUG=""
CLAIMED_BRANCH=""
CLAIMED_WT=""
for STORY_FILE in $CANDIDATES; do
  BASENAME=$(basename "$STORY_FILE" .md)
  SLUG=${BASENAME#story-}
  BRANCH="feat/story-${SLUG}"
  WT_PATH="../wt-story-${SLUG}"

  if git worktree add "$WT_PATH" -b "$BRANCH" >/dev/null 2>&1; then
    CLAIMED_PATH="$STORY_FILE"
    CLAIMED_SLUG="$SLUG"
    CLAIMED_BRANCH="$BRANCH"
    CLAIMED_WT="$WT_PATH"
    break
  elif [ -n "$ARG" ]; then
    echo "ERROR: '$BRANCH' already exists — story is already claimed." >&2
    exit 1
  fi
done

if [ -z "$CLAIMED_PATH" ]; then
  echo "ERROR: every story in $READY/ is already claimed by an existing feat/story-* branch." >&2
  exit 1
fi

echo "=== Story claimed ==="
echo "$CLAIMED_PATH"
echo "=== Branch ==="
echo "$CLAIMED_BRANCH"
echo "=== Worktree ==="
echo "$CLAIMED_WT"
echo "=== Story content ==="
cat "$CLAIMED_PATH"
```

After the preamble runs:

1. Call `EnterWorktree` with `path` set to the worktree path printed above
   (`$CLAIMED_WT`) to durably switch the session into it — this also
   refreshes cwd-dependent state (system prompt, feature `CLAUDE.md`, plans
   dir) that a bare `cd` would not.
2. Inside the worktree, `git mv` the claimed story file from
   `stories/ready/` to `stories/in-progress/` and commit
   (`chore(story): mark {slug} in-progress`). This is the first commit on
   the branch and is what makes the claim visible once the PR merges.
3. Read the story file. It is the full context — do not ask the user for
   clarifications that the file already answers.
4. If the story's "Files to touch" names a primary feature directory under
   `src/`, note it — work is scoped there. Claude Code loads that
   directory's `CLAUDE.md` lazily on first file touch.
5. Invoke the Superpowers **`subagent-driven-development`** skill to drive
   implementation: brainstorm → plan 2–5 min subtasks → tests-first →
   implement → `code-reviewer` after each task → `verification-before-completion`.
6. If the story leaves a real ambiguity unresolved — architectural direction,
   contradictory requirements, a bug attempted twice without success, a
   non-obvious security tradeoff — **stop and ask the user**. Do not guess
   and do not widen scope to work around it.
7. Before declaring done: run `make check` and confirm every acceptance
   criterion in the story is satisfied.
8. When the implementation is complete and verified, run `/commit-push-pr`
   to open the PR, then move the story file from `stories/in-progress/` to
   `stories/review/` (use `git mv`) and commit.
9. Call `ExitWorktree` with `action: "keep"` — the PR is only open at this
   point, not merged, so the worktree must stay. It's cleaned up later by
   the next `/dev-story` invocation's sweep, or by `stop_story_lifecycle.py`
   once the PR merges.
10. Print the PR URL and the new story path.
