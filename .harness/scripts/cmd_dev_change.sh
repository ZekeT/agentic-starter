#!/usr/bin/env bash
# Preamble for /dev-change. Claims a task group and prints the change-scoped
# context the session needs. Usage: cmd_dev_change.sh <slug> [group] [--worktree]
set -e
. "$(cd "$(dirname "$0")" && pwd)/lib/change.sh"

# Flags first, so --worktree never lands in a positional slot.
WORKTREE=0
POSITIONAL=""
for arg in "$@"; do
  case "$arg" in
    --worktree) WORKTREE=1 ;;
    *)          POSITIONAL="$POSITIONAL $arg" ;;
  esac
done
SLUG=$(echo "$POSITIONAL" | awk '{print $1}')
GROUP=$(echo "$POSITIONAL" | awk '{print $2}')

if [ -n "$GROUP" ]; then
  case "$GROUP" in
    *[!0-9]*|0) die "group must be a positive integer, got '$GROUP'" \
                    "Omit it entirely to claim the lowest group with unchecked tasks." ;;
  esac
fi

if [ -z "$SLUG" ]; then
  echo "ERROR: usage is /dev-change <slug> [group] [--worktree]" >&2
  echo "" >&2
  echo "Active changes:" >&2
  list_active_changes >&2
  exit 1
fi

CHANGE_DIR="openspec/changes/$SLUG"
TASKS="$CHANGE_DIR/tasks.md"

if [ ! -d "$CHANGE_DIR" ]; then
  echo "ERROR: no change at $CHANGE_DIR" >&2
  echo "Crystallize one first:  /crystallize \"<your idea>\"" >&2
  echo "" >&2
  echo "Active changes:" >&2
  list_active_changes >&2
  exit 1
fi

[ -f "$TASKS" ] || die "$TASKS does not exist — the change has no task breakdown yet." \
                       "STANDARD: /crystallize $SLUG; DEEP: accept architecture, then /shape-change $SLUG"

# Legacy STANDARD changes need no tier marker or program-design artifact.
if grep -qE '^Workflow:[[:space:]]*DEEP([[:space:]]|$)' "$CHANGE_DIR/intent.md" 2>/dev/null; then
  [ -s "$CHANGE_DIR/program-design.md" ] || die "DEEP change needs accepted program design." \
    "Run /shape-change $SLUG after the architecture gate."
fi

# The change must be internally consistent before any code is written against it.
if ! openspec validate "$SLUG" 2>&1; then
  die "change '$SLUG' does not validate — fix it before implementing."
fi

# Sweep worktrees whose PR has already merged, so they don't pile up on disk.
# Best-effort: never blocks claiming. Merged is a PR-state fact, not "no commits
# diverged from main" — a freshly claimed, untouched branch is trivially an
# ancestor of main and must not be swept. The primary worktree is always the
# first entry and is never sweepable; in branch mode this session usually sits
# on a feat/ branch itself.
if command -v gh >/dev/null 2>&1; then
  git worktree list --porcelain 2>/dev/null | awk '
    /^worktree /                { path=$2; primary = (++seen == 1) }
    /^branch refs\/heads\/feat\// {
      if (primary) next
      branch=$2; sub("refs/heads/", "", branch); print path"\t"branch
    }
  ' | while IFS="$(printf '\t')" read -r WT WT_BRANCH; do
    if [ "$(gh pr view "$WT_BRANCH" --json state -q .state 2>/dev/null || true)" = "MERGED" ]; then
      if git worktree remove "$WT" 2>/dev/null; then
        git branch -d "$WT_BRANCH" 2>/dev/null || true
        echo "swept merged worktree: $WT ($WT_BRANCH)"
      fi
    fi
  done
fi

echo "=== Task groups in $SLUG ==="
task_group_summary "$TASKS"

if [ -z "$GROUP" ]; then
  GROUP=$(first_unfinished_group "$TASKS")
  [ -n "$GROUP" ] || die "All task groups in '$SLUG' are complete. Next: /archive-change $SLUG"
fi

GROUP_BODY=$(task_group_body "$TASKS" "$GROUP")
[ -n "$GROUP_BODY" ] || die "no task group '$GROUP' in $TASKS"

if ! echo "$GROUP_BODY" | grep -qE '^[[:space:]]*-[[:space:]]*\[[[:space:]]\]'; then
  die "every task in group $GROUP is already checked off." \
      "Pick another group, or run /archive-change $SLUG if all groups are done."
fi

# Claim by winning the race to create the branch. `git switch -c` and
# `git worktree add` both fail on an existing branch, so the mutex holds either way.
BRANCH="feat/${SLUG}-g${GROUP}"
WT_PATH=""
CLAIM_FAILED="'$BRANCH' already exists — group $GROUP is already claimed."

if [ "$WORKTREE" = "1" ]; then
  WT_PATH=".worktrees/${SLUG}-g${GROUP}"
  git worktree add "$WT_PATH" -b "$BRANCH" >/dev/null 2>&1 || die "$CLAIM_FAILED"
else
  git switch -c "$BRANCH" >/dev/null 2>&1 || die "$CLAIM_FAILED"
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
echo "=== Context paths (read only sections relevant to the claimed group) ==="
for artifact in intent.md proposal.md design.md program-design.md; do
  [ ! -f "$CHANGE_DIR/$artifact" ] || printf '%s\n' "$CHANGE_DIR/$artifact"
done
if [ -d "$CHANGE_DIR/specs" ]; then
  find "$CHANGE_DIR/specs" -name '*.md' -print
fi
printf '%s\n' "Follow this group's Context references; legacy groups use targeted heading searches."
printf '%s\n' "Load docs/architecture.md only if this group's architectural work needs it."
