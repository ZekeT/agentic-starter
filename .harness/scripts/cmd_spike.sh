#!/usr/bin/env bash
# Preamble for /spike. Claims or resumes a spike branch and prints the
# artifacts a spike extends. Usage: cmd_spike.sh <slug> [question...]
set -e
. "$(cd "$(dirname "$0")" && pwd)/lib/change.sh"

SLUG="$1"
[ $# -gt 0 ] && shift
QUESTION="$*"

if [ -z "$SLUG" ]; then
  echo "ERROR: usage is /spike <slug> <question>" >&2
  echo "" >&2
  echo "Spikes in progress:" >&2
  git branch --list 'spike/*' >&2 || true
  exit 1
fi

case "$SLUG" in
  *[!a-z0-9-]*) die "slug must be kebab-case (a-z, 0-9, -), got '$SLUG'" ;;
esac

BRANCH="spike/$SLUG"

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git switch "$BRANCH" >/dev/null 2>&1
  echo "=== Resuming $BRANCH ==="
  echo "Commits so far:"
  git log --oneline "$(merge_base_of "$BRANCH")..$BRANCH" 2>/dev/null || echo "  (none yet)"
else
  git switch -c "$BRANCH" >/dev/null 2>&1
  echo "=== Started $BRANCH ==="
fi

[ -n "$QUESTION" ] && { echo ""; echo "Question: $QUESTION"; }

echo ""
echo "=== Decisions already recorded ==="
cat docs/decisions/index.md 2>/dev/null || echo "(no index)"

if [ -f CONTEXT.md ]; then
  echo ""
  echo "=== CONTEXT.md (the glossary this spike may extend) ==="
  cat CONTEXT.md
fi

# Listed, not printed: a spike reads what its question actually needs, and most
# spikes need none of these in full.
echo ""
echo "=== Available if the question needs them (read by name) ==="
for f in docs/architecture.md docs/product.md CONTEXT-MAP.md; do
  [ -f "$f" ] && echo "  $f"
done
echo "  openspec list --specs        — the capability index"
echo "  git branch --list 'spike/*'  — other spikes"
