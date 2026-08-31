# /dev-change

Implement one task group from an OpenSpec change, in an isolated git worktree,
using the Superpowers `subagent-driven-development` skill. One task group = one
branch = one worktree = one PR.

Usage:
- `/dev-change <slug> <group>` — work on task group `<group>` of that change
- `/dev-change <slug>` — claim the lowest-numbered group with unchecked tasks

The mutex that stops two sessions implementing the same group is **branch
existence**: claiming a group means winning the race to create its
`feat/<slug>-g<N>` worktree/branch. Nothing about the claim is recorded in a
file, so there is no state to reconcile if a session dies — the branch either
exists or it does not.

Task groups come from `openspec/changes/<slug>/tasks.md`, whose `## N.` headings
are written to be independently shippable (enforced by the `tasks` rule in
`openspec/config.yaml`). If a group cannot ship on its own, that is a bug in the
change's planning, not something to work around here.

---

```bash
set -e

SLUG=$(echo "$ARGUMENTS" | awk '{print $1}')
GROUP=$(echo "$ARGUMENTS" | awk '{print $2}')

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
if command -v gh >/dev/null 2>&1; then
  git worktree list --porcelain 2>/dev/null | awk '
    /^worktree /                { path=$2 }
    /^branch refs\/heads\/feat\// { branch=$2; sub("refs/heads/", "", branch); print path"\t"branch }
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

# Claim by winning the race to create the worktree/branch.
BRANCH="feat/${SLUG}-g${GROUP}"
WT_PATH="../wt-${SLUG}-g${GROUP}"

if ! git worktree add "$WT_PATH" -b "$BRANCH" >/dev/null 2>&1; then
  echo "ERROR: '$BRANCH' already exists — group $GROUP is already claimed." >&2
  exit 1
fi

echo ""
echo "=== Claimed ==="
echo "change:   $SLUG"
echo "group:    $GROUP"
echo "branch:   $BRANCH"
echo "worktree: $WT_PATH"

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

1. Call `EnterWorktree` with `path` set to the worktree path printed above to
   durably switch the session into it — this also refreshes cwd-dependent state
   (system prompt, feature `CLAUDE.md`, plans dir) that a bare `cd` would not.
2. Work **only** the tasks in the claimed group. The other groups belong to
   other branches; touching them here creates the merge conflicts this
   one-group-per-PR split exists to prevent.
3. The proposal, delta specs, and design printed above are the full context. Do
   not bulk-read `openspec/specs/` — if you need current behaviour for a
   capability, read that capability's spec file by name.
4. Invoke the Superpowers **`subagent-driven-development`** skill to drive
   implementation: brainstorm → plan 2–5 min subtasks → tests-first → implement
   → `code-reviewer` after each task → `verification-before-completion`.
5. As each task completes, tick its checkbox in `openspec/changes/<slug>/tasks.md`
   (`- [ ]` → `- [x]`). This file is the durable plan of record: **if
   implementation departs from it, update it in the same commit**, because PR
   review checks the diff against it.
6. If implementation shows a delta spec is wrong, never silently fix the code
   around it. Amend the change's delta if the correction is small; open a new
   change if it is large. Never edit `openspec/specs/` directly — that only ever
   changes at archive time.
7. If a real ambiguity remains unresolved — architectural direction,
   contradictory requirements, a bug attempted twice without success, a
   non-obvious security tradeoff — **stop and ask the user**. Do not guess, and
   do not widen scope to route around it.
8. Before declaring done: run `make check`, and confirm every task in the group
   is ticked and every scenario in the delta specs it covers actually holds.
9. Dispatch the **`verifier`** subagent. It runs in a fresh context window, so
   its verdict is not coloured by the assumptions that produced the code — this
   session has already convinced itself. Give it the change slug and group
   number; it runs the change and reports mismatches without fixing anything.
   Paste its report into the PR's "How this was tested" section. If it reports
   a mismatch, resolve it before opening the PR — either the code is wrong, or
   the delta spec is (rule 6 above), and a FAIL verdict is not something to
   explain away in the PR body.
10. Run `/commit-push-pr` to open the PR.
11. Call `ExitWorktree` with `action: "keep"` — the PR is open, not merged, so
    the worktree must stay. The next `/dev-change` sweeps it once the PR merges.
12. Print the PR URL, and the remaining unchecked groups so the user knows
    what's left before `/archive-change`.
