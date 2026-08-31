# /archive-change

Close the loop on a completed change: merge its delta specs into
`openspec/specs/` and archive the change folder.

This is the step that makes `openspec/specs/` a living statement of what the
system does rather than a snapshot that rots. It is **human-gated on purpose** —
a command, never a hook. `openspec/specs/` is the project's durable truth, and
nothing should mutate it as a side effect of a session ending.

Usage: `/archive-change <slug>`

---

```bash
set -e

SLUG="$ARGUMENTS"

if [ -z "$SLUG" ]; then
  echo "ERROR: usage is /archive-change <slug>" >&2
  echo "" >&2
  echo "Active changes:" >&2
  openspec list 2>/dev/null >&2 || ls -1 openspec/changes 2>/dev/null | grep -v '^archive$' >&2
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
  ls -1 openspec/changes 2>/dev/null | grep -v '^archive$' >&2
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
  echo "" >&2
  echo "ERROR: '$SLUG' does not validate — fix it before archiving." >&2
  exit 1
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
```

After the preamble runs:

1. **Show the user the spec diff and stop for confirmation.** Summarise what
   `openspec/specs/` will gain, lose, or change, and whether that matches the
   proposal's stated impact. A mismatch means either the proposal was wrong or
   the implementation drifted — say which, and do not archive until it's
   resolved.
2. On confirmation, archive via the OpenSpec CLI — never hand-merge the deltas:

   ```bash
   openspec archive <slug> --yes
   ```

   This merges the delta specs into `openspec/specs/` and moves the change to
   `openspec/changes/archive/YYYY-MM-DD-<slug>/`. For a change with no deltas,
   add `--skip-specs`.
3. Print the resulting diff so it lands in the transcript:

   ```bash
   git diff --stat openspec/specs/
   git diff openspec/specs/
   ```
4. **Product-truth check — ask once, not continuously.** In a single message:
   - Does this change alter `docs/product.md` (what the product is or isn't)?
   - Does it alter `docs/architecture.md` (containers, boundaries, constraints)?
   - Did implementation settle a durable decision that needs an ADR in
     `docs/decisions/`?

   Apply whatever the user confirms. If they say no to all three, move on — the
   spec diff is already the record.
5. Commit:

   ```bash
   git add openspec/ docs/
   git commit -m "chore(<slug>): archive change, merge deltas into specs"
   ```
6. Report: capabilities added/modified, the archive path, and any remaining
   active changes (`openspec list`).

## Constraints

- **Never edit `openspec/specs/` by hand**, here or anywhere. The CLI's merge is
  what keeps the archived change and the resulting spec consistent.
- Idempotent: re-running on an already-archived change exits 0 having done
  nothing.
- Refuses while any task is unchecked, and refuses if the change fails
  validation.
