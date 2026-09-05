# /dev-change

Implement one task group from an OpenSpec change, on its own branch. One task
group = one branch = one PR.

Usage:
- `/dev-change <slug> <group>` — work on task group `<group>` of that change
- `/dev-change <slug>` — claim the lowest-numbered group with unchecked tasks
- `--worktree` — claim into `.worktrees/<slug>-g<N>` instead of switching this
  checkout. Worth it **only** when running several sessions at once, which is
  what the isolation is for. A single session pays for it in editor visibility
  and a system-prompt refresh on `EnterWorktree`, and gains nothing.

The mutex that stops two sessions implementing the same group is **branch
existence**: claiming a group means winning the race to create
`feat/<slug>-g<N>`. `git switch -c` and `git worktree add` both fail on an
existing branch, so the mutex holds either way. Nothing about the claim is
recorded in a file, so there is no state to reconcile if a session dies — the
branch either exists or it does not.

Task groups come from `openspec/changes/<slug>/tasks.md`, whose `## N.` headings
are written to be independently shippable (enforced by the `tasks` rule in
`openspec/config.yaml`). If a group cannot ship on its own, that is a bug in the
change's planning, not something to work around here.

---

```bash
set -e

# Flags first, so `--worktree` never lands in the positional slots.
WORKTREE=0
POSITIONAL=""
for arg in $ARGUMENTS; do
  case "$arg" in
    --worktree) WORKTREE=1 ;;
    *)          POSITIONAL="$POSITIONAL $arg" ;;
  esac
done

SLUG=$(echo "$POSITIONAL" | awk '{print $1}')
GROUP=$(echo "$POSITIONAL" | awk '{print $2}')

if [ -n "$GROUP" ]; then
  case "$GROUP" in
    *[!0-9]*|0)
      echo "ERROR: group must be a positive integer, got '$GROUP'" >&2
      echo "Omit it entirely to claim the lowest group with unchecked tasks." >&2
      exit 1
      ;;
  esac
fi

if [ -z "$SLUG" ]; then
  echo "ERROR: usage is /dev-change <slug> [group]" >&2
  echo "" >&2
  echo "Active changes:" >&2
  openspec list 2>/dev/null >&2 || ls -1 openspec/changes 2>/dev/null | grep -v '^archive$' >&2
  exit 1
fi

CHANGE_DIR="openspec/changes/$SLUG"
TASKS="$CHANGE_DIR/tasks.md"

if [ ! -d "$CHANGE_DIR" ]; then
  echo "ERROR: no change at $CHANGE_DIR" >&2
  echo "Crystallize one first:  /crystallize \"<your idea>\"" >&2
  echo "" >&2
  echo "Active changes:" >&2
  ls -1 openspec/changes 2>/dev/null | grep -v '^archive$' >&2
  exit 1
fi

if [ ! -f "$TASKS" ]; then
  echo "ERROR: $TASKS does not exist — the change has no task breakdown yet." >&2
  echo "Generate it, then re-run:  openspec instructions tasks --change $SLUG" >&2
  exit 1
fi

# The change must be internally consistent before any code is written against it.
if ! openspec validate "$SLUG" 2>&1; then
  echo "" >&2
  echo "ERROR: change '$SLUG' does not validate — fix it before implementing." >&2
  exit 1
fi

# Sweep worktrees whose PR has already merged, so they don't pile up on disk.
# Best-effort: never blocks claiming. Merged is a PR-state fact, not "no commits
# diverged from main" — a freshly claimed, untouched branch is trivially an
# ancestor of main and must not be swept.
# The primary worktree is always the first entry, and is never sweepable — in
# branch mode this session is usually sitting on a feat/ branch itself.
if command -v gh >/dev/null 2>&1; then
  git worktree list --porcelain 2>/dev/null | awk '
    /^worktree /                { path=$2; primary = (++seen == 1) }
    /^branch refs\/heads\/feat\// {
      if (primary) next
      branch=$2; sub("refs/heads/", "", branch); print path"\t"branch
    }
  ' | while IFS=$'\t' read -r WT_PATH WT_BRANCH; do
    PR_STATE=$(gh pr view "$WT_BRANCH" --json state -q .state 2>/dev/null || true)
    if [ "$PR_STATE" = "MERGED" ]; then
      if git worktree remove "$WT_PATH" 2>/dev/null; then
        git branch -d "$WT_BRANCH" 2>/dev/null || true
        echo "swept merged worktree: $WT_PATH ($WT_BRANCH)"
      fi
    fi
  done
fi

# Every `## N.` heading in tasks.md, with its checkbox counts.
echo "=== Task groups in $SLUG ==="
awk '
  /^##[[:space:]]+[0-9]+\./ {
    if (n != "") printf "  group %-3s %-40s %d/%d done\n", n, title, done, total
    match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
    title = $0; sub(/^##[[:space:]]+[0-9]+\.[[:space:]]*/, "", title)
    done = 0; total = 0; next
  }
  /^[[:space:]]*-[[:space:]]*\[[ xX]\]/ { total++; if ($0 ~ /\[[xX]\]/) done++ }
  END { if (n != "") printf "  group %-3s %-40s %d/%d done\n", n, title, done, total }
' "$TASKS"

# With no group argument, claim the lowest-numbered group that has unchecked work.
if [ -z "$GROUP" ]; then
  GROUP=$(awk '
    /^##[[:space:]]+[0-9]+\./ {
      if (n != "" && done < total) { print n; found = 1; exit }
      match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
      done = 0; total = 0; next
    }
    /^[[:space:]]*-[[:space:]]*\[[ xX]\]/ { total++; if ($0 ~ /\[[xX]\]/) done++ }
    END { if (!found && n != "" && done < total) print n }
  ' "$TASKS")
  if [ -z "$GROUP" ]; then
    echo "" >&2
    echo "All task groups in '$SLUG' are complete. Next: /archive-change $SLUG" >&2
    exit 1
  fi
fi

# Isolate the requested group's tasks.
GROUP_BODY=$(awk -v g="$GROUP" '
  /^##[[:space:]]+[0-9]+\./ {
    match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
    inblock = (n == g)
  }
  inblock
' "$TASKS")

if [ -z "$GROUP_BODY" ]; then
  echo "ERROR: no task group '$GROUP' in $TASKS" >&2
  exit 1
fi

if ! echo "$GROUP_BODY" | grep -qE '^[[:space:]]*-[[:space:]]*\[[[:space:]]\]'; then
  echo "ERROR: every task in group $GROUP is already checked off." >&2
  echo "Pick another group, or run /archive-change $SLUG if all groups are done." >&2
  exit 1
fi

# Claim by winning the race to create the branch.
BRANCH="feat/${SLUG}-g${GROUP}"
WT_PATH=""

if [ "$WORKTREE" = "1" ]; then
  WT_PATH=".worktrees/${SLUG}-g${GROUP}"
  if ! git worktree add "$WT_PATH" -b "$BRANCH" >/dev/null 2>&1; then
    echo "ERROR: '$BRANCH' already exists — group $GROUP is already claimed." >&2
    exit 1
  fi
elif ! git switch -c "$BRANCH" >/dev/null 2>&1; then
  echo "ERROR: '$BRANCH' already exists — group $GROUP is already claimed." >&2
  exit 1
fi

echo ""
echo "=== Claimed ==="
echo "change:   $SLUG"
echo "group:    $GROUP"
echo "branch:   $BRANCH"
echo "worktree: ${WT_PATH:-(none — switched this checkout)}"

echo ""
echo "=== Tasks for group $GROUP ==="
echo "$GROUP_BODY"

echo ""
echo "=== Proposal ==="
cat "$CHANGE_DIR/proposal.md" 2>/dev/null || echo "(none)"

echo ""
echo "=== Delta specs ==="
find "$CHANGE_DIR/specs" -name '*.md' -exec echo '--- {} ---' \; -exec cat {} \; 2>/dev/null || echo "(none)"

if [ -f "$CHANGE_DIR/design.md" ]; then
  echo ""
  echo "=== Design ==="
  cat "$CHANGE_DIR/design.md"
fi

# Architecture is loaded only when the proposal says the change affects it —
# this is the whole point of change-scoped context.
if grep -qiE 'architecture-affecting|affects architecture' "$CHANGE_DIR/proposal.md" 2>/dev/null; then
  echo ""
  echo "=== Architecture (change is marked architecture-affecting) ==="
  cat docs/architecture.md 2>/dev/null || true
fi
```

After the preamble runs:

1. If a worktree path was printed, call `EnterWorktree` with it. Otherwise this
   checkout is already on the branch — do not create a worktree.
2. Work **only** the tasks in the claimed group. The other groups belong to
   other branches; touching them here creates the merge conflicts this
   one-group-per-PR split exists to prevent.
3. The proposal, delta specs, and design printed above are the full context.
   Do not bulk-read `openspec/specs/`; if you need current behaviour for a
   capability, read that spec file by name.
4. **The task group is the plan. Do not re-plan it.** It was written by
   `/crystallize` and accepted at a human gate, and it is already on screen.
   Implement it directly in this session, driving each task with the Superpowers
   **`test-driven-development`** skill: failing test, minimal code, refactor.
   Do **not** invoke `subagent-driven-development` here — it dispatches a fresh
   implementer and a fresh reviewer per task, each re-reading this context cold,
   to re-derive a plan you already have.
5. As each task completes, tick its checkbox in `openspec/changes/<slug>/tasks.md`
   (`- [ ]` → `- [x]`), and update the task text in the same commit if
   implementation departed from it (see CLAUDE.md **Rules**).
6. If this group adds a feature directory under `src/`, or changes what an
   existing one is for, write or update that directory's own `CLAUDE.md` in the
   same commit — purpose, entry points, invariants, gotchas; ~30 lines. This is
   what stops the next session re-deriving the feature from its source. Stable
   facts only: never implementation status, which is `tasks.md`'s job.
7. CLAUDE.md's **Rules** govern here and are already loaded — in particular,
   what to do when a delta spec turns out to be wrong, and when to stop and ask
   rather than guess. A bug attempted twice without success is one of those
   stopping points.
8. Run `make check`. It must pass before you hand anything to a human, and its
   result is what you hand over — nothing downstream runs it again until
   `/commit-push-pr`.
9. Dispatch the **`verifier`** subagent. Fresh context, so its verdict is not
   coloured by the assumptions that produced the code — this session has
   already convinced itself. Give it the change slug and group number; it runs
   the change and reports mismatches without fixing anything. A FAIL is yours
   to resolve now: either the code is wrong or the delta spec is (step 7).
10. Worktree mode only: call `ExitWorktree` with `action: "keep"`.
11. **Stop here. Do not commit, and do not open a PR.** Print, for the user:
    the branch name, the `make check` result, the verifier's report verbatim,
    the tasks now ticked, the remaining unchecked groups, and the two commands
    that come next —

    ```
    /review           # verify the implementation against the spec
    /commit-push-pr   # commit and open the PR, once satisfied
    ```

    The human gate sits *before* the commit. Nothing this session wrote reaches
    git history or GitHub until a person has read `/review`'s verdict and chosen
    to run `/commit-push-pr` themselves.
