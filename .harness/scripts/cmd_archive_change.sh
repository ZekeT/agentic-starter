#!/usr/bin/env bash
# Preamble for /archive-change. Preflights a change and shows the spec diff
# surface before anything is merged into openspec/specs/.
# Usage: cmd_archive_change.sh <slug>
set -e
. "$(cd "$(dirname "$0")" && pwd)/lib/change.sh"

SLUG="$1"

if [ -z "$SLUG" ]; then
  echo "ERROR: usage is /archive-change <slug>" >&2
  echo "" >&2
  echo "Active changes:" >&2
  list_active_changes >&2
  exit 1
fi

CHANGE_DIR="openspec/changes/$SLUG"

# Idempotency. `openspec archive` errors with "not found" on an already-archived
# change, which is indistinguishable from a typo'd slug — so check the archive
# ourselves and exit 0 on a genuine re-run.
if [ ! -d "$CHANGE_DIR" ]; then
  EXISTING=$(ls -1d openspec/changes/archive/*-"$SLUG" 2>/dev/null | head -1 || true)
  if [ -n "$EXISTING" ]; then
    echo "Already archived: $EXISTING"
    echo "Nothing to do."
    exit 0
  fi
  echo "ERROR: no change at $CHANGE_DIR, and nothing matching in the archive." >&2
  echo "" >&2
  echo "Active changes:" >&2
  list_active_changes >&2
  exit 1
fi

# Preflight: every task must be ticked. Archiving with work outstanding would
# publish specs describing behaviour that does not exist yet.
TASKS="$CHANGE_DIR/tasks.md"
if [ -f "$TASKS" ]; then
  OPEN=$(grep -nE '^[[:space:]]*-[[:space:]]*\[[[:space:]]\]' "$TASKS" || true)
  if [ -n "$OPEN" ]; then
    echo "ERROR: '$SLUG' still has unchecked tasks:" >&2
    echo "$OPEN" | sed 's/^/  /' >&2
    echo "" >&2
    echo "Finish them with /dev-change $SLUG <group>, or tick them if they were" >&2
    echo "completed another way. Archiving now would publish specs for behaviour" >&2
    echo "that does not exist." >&2
    exit 1
  fi
  echo "All tasks complete."
else
  echo "No tasks.md — nothing to check off."
fi

# Unmerged branches for this change mean code is still in review.
STRAY=$(git branch --list "feat/${SLUG}-g*" --format='%(refname:short)' 2>/dev/null || true)
if [ -n "$STRAY" ]; then
  echo ""
  echo "WARNING: branches for this change still exist locally:"
  echo "$STRAY" | sed 's/^/  /'
  echo "If any PR is still open, stop and merge it first."
fi

if ! openspec validate "$SLUG" 2>&1; then
  die "'$SLUG' does not validate — fix it before archiving."
fi

# THE REVIEW SURFACE. Show exactly what would change in openspec/specs/ before
# touching it. Reviewing a spec diff instead of thousands of generated lines is
# the entire point of the loop.
echo ""
echo "=== Delta specs to be merged ==="
find "$CHANGE_DIR/specs" -name '*.md' -exec echo '--- {} ---' \; -exec cat {} \; 2>/dev/null \
  || echo "(no deltas — spec-less change)"

echo ""
echo "=== Current openspec/specs/ (before) ==="
openspec list --specs 2>/dev/null || echo "(none yet)"

echo ""
echo "=== Proposal's stated impact (the diff below should match this) ==="
sed -n '/^## Impact/,$p' "$CHANGE_DIR/proposal.md" 2>/dev/null || echo "(none)"
