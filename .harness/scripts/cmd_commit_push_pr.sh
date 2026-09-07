#!/usr/bin/env bash
# Preamble for /commit-push-pr. Pre-computes git context and runs the gate.
# Usage: cmd_commit_push_pr.sh [--base <branch>]
set -e
. "$(cd "$(dirname "$0")" && pwd)/lib/change.sh"

# --base names the branch the PR targets, for this invocation only. Everything
# downstream — the diff base and `gh pr create --base` — follows it, so a team
# that merges to develop is not fighting a hardcoded main.
while [ $# -gt 0 ]; do
  case "$1" in
    --base)
      [ -n "${2:-}" ] || die "--base needs a branch name." "Usage: /commit-push-pr --base <branch> [\"message\"]"
      HARNESS_BASE_BRANCH="$2"; shift 2 ;;
    --base=*)
      HARNESS_BASE_BRANCH="${1#--base=}"; shift ;;
    *) shift ;;
  esac
done
export HARNESS_BASE_BRANCH

BRANCH=$(git rev-parse --abbrev-ref HEAD)
resolve_base_branch
BASE_REF=$(base_ref)

# Validate the base before anything tries to diff against it — git's own
# "Not a valid object name" says nothing about where the branch name came from.
if [ "$BASE_BRANCH" = "$BRANCH" ]; then
  die "The PR base and the current branch are both '$BRANCH'." \
      "Check out the feature branch, or pass: /commit-push-pr --base <branch>"
fi
if ! git rev-parse --verify --quiet "$BASE_REF" >/dev/null; then
  die "PR base '$BASE_BRANCH' is not a branch here or on origin (source: $BASE_BRANCH_SOURCE)." \
      "Pass one:  /commit-push-pr --base <branch>" \
      "Or set the default once:  git config harness.baseBranch <branch>"
fi

BASE=$(merge_base_of HEAD)
SLUG=$(slug_from_branch "$BRANCH")
GROUP=$(group_from_branch "$BRANCH")

echo "=== Branch ===" && echo "$BRANCH"
echo "=== PR base ===" && echo "$BASE_BRANCH  (source: $BASE_BRANCH_SOURCE)"
if [ "$BASE_BRANCH_SOURCE" != "--base" ]; then
  echo "  override for this PR:  /commit-push-pr --base <branch>"
  echo "  set the default once:  git config harness.baseBranch <branch>"
fi
echo "=== Status ===" && git status --short
echo "=== Diff stat since $(git rev-parse --short "$BASE") on $BASE_BRANCH ===" && git diff "$BASE" --stat

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
