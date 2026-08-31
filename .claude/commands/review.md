# /review

Review the current branch's diff against the change it implements.

Usage: `/review` — infers the change slug and task group from the branch name
(`feat/<slug>-g<N>`), or `/review <slug>` to name one explicitly.

---

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
SLUG="$ARGUMENTS"

# feat/<slug>-g<N>  →  slug, group
if [ -z "$SLUG" ]; then
  SLUG=$(echo "$BRANCH" | sed -nE 's|^feat/(.*)-g[0-9]+$|\1|p')
fi
GROUP=$(echo "$BRANCH" | sed -nE 's|^feat/.*-g([0-9]+)$|\1|p')

echo "=== Branch ===" && echo "$BRANCH (change: ${SLUG:-unknown}, group: ${GROUP:-n/a})"
echo "=== Changed files ===" && git diff main --name-only
echo "=== Diff ===" && git diff main

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

echo "=== make check ===" && make check 2>&1 | tail -30
```

Run the passes defined in `REVIEW.md`. The compliance pass is the one this
harness exists to enable: check the diff against the delta specs and the task
group above, not just against general good taste.

Produce: Summary / Must Fix / Should Fix / Notes / Verdict.

For security-sensitive changes, also dispatch the `security-reviewer` agent.
