#!/usr/bin/env bash
# Preamble for /review. Prints a branch's diff plus the contract it must satisfy.
# Usage: cmd_review.sh [<branch>|<slug>]
set -e
. "$(cd "$(dirname "$0")" && pwd)/lib/change.sh"

ARG="$1"
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

[ -n "$SLUG" ] || SLUG=$(slug_from_branch "$BRANCH")
GROUP=$(group_from_branch "$BRANCH")

if [ "$BRANCH" = "main" ]; then
  echo "ERROR: nothing to review — '$BRANCH' is the trunk." >&2
  echo "Name a branch:  /review <branch>" >&2
  git branch --list 'feat/*' 'fix/*' 'chore/*' >&2
  exit 1
fi

BASE=$(merge_base_of "$BRANCH")

echo "=== Branch ==="
echo "$BRANCH (change: ${SLUG:-unknown}, group: ${GROUP:-n/a}, base: $(git rev-parse --short "$BASE"))"

if [ "$BRANCH" = "$HERE" ]; then
  # Checked out: diff the base against the working tree, so uncommitted work
  # is reviewed too.
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
    task_group_body "$CHANGE_DIR/tasks.md" "$GROUP" 2>/dev/null
  fi
else
  echo "(no change folder resolved — reviewing the diff on its own)"
fi

# No `make check` here. /dev-change ran it post-implementation and handed the
# result over; /commit-push-pr runs it again before the push, which is the run
# that catches anything edited during this review.
