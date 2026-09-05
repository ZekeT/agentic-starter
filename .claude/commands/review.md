# /review

Verify an implementation against the change it claims to implement. This is
the **human's gate**: `/dev-change` stops without committing and hands the
branch over, and this is what you run before deciding to `/commit-push-pr`.

No agent calls this command. Running it is the decision to look.

Usage:
- `/review` — review the checked-out branch, uncommitted work included
- `/review <branch>` — review that branch (e.g. `feat/add-auth-g2`)
- `/review <slug>` — review the checked-out branch against that change slug

---

```bash
ARG=$(echo "$ARGUMENTS" | awk '{print $1}')
HERE=$(git rev-parse --abbrev-ref HEAD)
BRANCH="$HERE"
SLUG=""

# The argument is a branch if one exists by that name, otherwise a change slug.
if [ -n "$ARG" ]; then
  if git show-ref --verify --quiet "refs/heads/$ARG"; then
    BRANCH="$ARG"
  else
    SLUG="$ARG"
  fi
fi

# feat/<slug>-g<N>  →  slug, group
[ -n "$SLUG" ] || SLUG=$(echo "$BRANCH" | sed -nE 's|^feat/(.*)-g[0-9]+$|\1|p')
GROUP=$(echo "$BRANCH" | sed -nE 's|^feat/.*-g([0-9]+)$|\1|p')

if [ "$BRANCH" = "main" ]; then
  echo "ERROR: nothing to review — '$BRANCH' is the trunk." >&2
  echo "Name a branch:  /review <branch>" >&2
  git branch --list 'feat/*' 'fix/*' 'chore/*' >&2
  exit 1
fi

# Three-dot: what THIS branch added since it diverged, never main's own commits
# played back inverted. Anchor on the merge base so a moved main adds no noise.
BASE=$(git merge-base main "$BRANCH")

echo "=== Branch ===" && echo "$BRANCH (change: ${SLUG:-unknown}, group: ${GROUP:-n/a}, base: $(git rev-parse --short "$BASE"))"
if [ "$BRANCH" = "$HERE" ]; then
  # Checked out: diff base against the working tree, so uncommitted work is reviewed too.
  echo "=== Changed files ===" && git diff "$BASE" --name-only
  echo "=== Diff ===" && git diff "$BASE"
else
  echo "=== Changed files ===" && git diff "$BASE" "$BRANCH" --name-only
  echo "=== Diff ===" && git diff "$BASE" "$BRANCH"
fi

CHANGE_DIR="openspec/changes/$SLUG"
if [ -n "$SLUG" ] && [ -d "$CHANGE_DIR" ]; then
  echo "=== Proposal ===" && cat "$CHANGE_DIR/proposal.md" 2>/dev/null
  echo "=== Delta specs (the behaviour contract this diff must satisfy) ==="
  find "$CHANGE_DIR/specs" -name '*.md' -exec echo '--- {} ---' \; -exec cat {} \; 2>/dev/null
  if [ -n "$GROUP" ]; then
    echo "=== Task group $GROUP (the plan this diff must match) ==="
    awk -v g="$GROUP" '
      /^##[[:space:]]+[0-9]+\./ {
        match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
        inblock = (n == g)
      }
      inblock
    ' "$CHANGE_DIR/tasks.md" 2>/dev/null
  fi
else
  echo "(no change folder resolved — reviewing the diff on its own)"
fi

# No `make check` here. /dev-change ran it post-implementation and handed the
# result over; /commit-push-pr runs it again before the push, which is the run
# that catches anything edited during this review. A third run would tell you
# what you already know.
```

Run the passes defined in `REVIEW.md`. The compliance pass is the one this
harness exists to enable: check the diff against the delta specs and the task
group above, not just against general good taste.

`make check` is not run here — `REVIEW.md`'s **Skip entirely** section says not
to relitigate what the gate decides. If you have no hand-off result for this
branch, run `make check` yourself before trusting the diff.

Produce: Summary / Must Fix / Should Fix / Notes / Verdict.

For security-sensitive changes, also dispatch the `security-reviewer` agent.

End by telling the user what the verdict means for the next command: nothing
is committed yet, so **REQUEST CHANGES** means fix the branch and re-run this,
and **APPROVE** means they can run `/commit-push-pr`.
