# /dev-story

Develop a story end-to-end using the Superpowers `subagent-driven-development`
skill. Handles the `ready/ → in-progress/ → review/` lifecycle automatically
so you never have to `mv` story files by hand.

Usage:
- `/dev-story 001` — work on a specific story id
- `/dev-story story-001-slug` — or pass the full slug
- `/dev-story` — pick the lowest-numbered story in `stories/ready/`

---

```bash
set -e

ARG="$ARGUMENTS"
READY=stories/ready
INPROG=stories/in-progress

mkdir -p "$INPROG"

# Resolve which story to work on
if [ -z "$ARG" ]; then
  STORY_FILE=$(ls -1 "$READY"/*.md 2>/dev/null | sort | head -n 1 || true)
  if [ -z "$STORY_FILE" ]; then
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
fi

BASENAME=$(basename "$STORY_FILE" .md)
SLUG=${BASENAME#story-}
BRANCH="feat/story-${SLUG}"

# Move the file before any work starts so two sessions can't pick the same one
git mv "$STORY_FILE" "$INPROG/" 2>/dev/null || mv "$STORY_FILE" "$INPROG/"
NEW_PATH="$INPROG/$(basename "$STORY_FILE")"

# Land on the right branch
CURRENT=$(git branch --show-current)
if [ "$CURRENT" != "$BRANCH" ]; then
  git checkout -B "$BRANCH"
fi

echo "=== Story selected ==="
echo "$NEW_PATH"
echo "=== Branch ==="
git branch --show-current
echo "=== Story content ==="
cat "$NEW_PATH"
```

After the preamble runs:

1. Read the story file at the path printed above. It is the full context —
   do not ask the user for clarifications that the file already answers.
2. If the story's "Files to touch" names a primary feature directory under
   `src/`, note it — work is scoped there. Claude Code loads that
   directory's `CLAUDE.md` lazily on first file touch; when launching a
   fresh session for a single-feature story, prefer starting Claude Code
   from that subdirectory.
3. Invoke the Superpowers **`subagent-driven-development`** skill to drive
   implementation: brainstorm → plan 2–5 min subtasks → tests-first →
   implement → `code-reviewer` after each task → `verification-before-completion`.
4. Escalate to the `advisor_20260301` tool only on architectural ambiguity,
   contradictions between PRD and architecture, a bug attempted twice
   without success, or a non-obvious security tradeoff (max 3 uses).
5. Before declaring done: run `make check` and confirm every acceptance
   criterion in the story is satisfied.
6. When the implementation is complete and verified, run `/commit-push-pr`
   to open the PR, then move the story file from `stories/in-progress/` to
   `stories/review/` (use `git mv`).
7. Print the PR URL and the new story path.
