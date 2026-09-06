#!/usr/bin/env bash
# Preamble for /commit-push-pr. Pre-computes git context and runs the gate.
set -e
. "$(cd "$(dirname "$0")" && pwd)/lib/change.sh"

BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE=$(merge_base_of HEAD)
SLUG=$(slug_from_branch "$BRANCH")
GROUP=$(group_from_branch "$BRANCH")

echo "=== Branch ===" && echo "$BRANCH"
echo "=== Status ===" && git status --short
echo "=== Diff stat since $(git rev-parse --short "$BASE") ===" && git diff "$BASE" --stat

if [ -n "$SLUG" ] && [ -d "openspec/changes/$SLUG" ]; then
  echo "=== Change: $SLUG (task group ${GROUP:-?}) ==="
  # Scenario headings only, not the spec bodies. This command runs in the
  # session that just implemented against those specs — they are already in
  # context. The headings are enough to fill the PR's Spec compliance boxes
  # honestly; open the file if one is unclear.
  echo "--- scenarios this diff must satisfy (openspec/changes/$SLUG/specs/) ---"
  grep -rn '^#### Scenario:' "openspec/changes/$SLUG/specs" 2>/dev/null || echo "(no delta specs)"
  echo "--- task group $GROUP ---"
  task_group_body "openspec/changes/$SLUG/tasks.md" "$GROUP" 2>/dev/null

  UNCHECKED=$(unchecked_in_group "openspec/changes/$SLUG/tasks.md" "$GROUP" 2>/dev/null)
  if [ -n "$UNCHECKED" ]; then
    echo "!!! Tasks in group $GROUP still unchecked:"
    echo "$UNCHECKED"
    echo "!!! Tick them if done, or finish them. tasks.md is the plan of record."
  fi
else
  echo "=== No change folder resolved from branch name ==="
  echo "(fine for a hotfix or chore — say so in the PR's Change line)"
fi

echo "=== Tests touched by this diff ==="
git diff "$BASE" --name-only | grep -E '^tests/' || echo "(none — is that right for this change?)"

echo "=== make check ===" && make check 2>&1 | tail -15
