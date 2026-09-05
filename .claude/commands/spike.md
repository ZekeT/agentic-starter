# /spike

Settle a **how** before it becomes a change. Use this when the *what* is roughly
clear but the approach is not — the shape of the state model, whether an
integration works the way the docs claim, which of three designs survives
contact with real data.

Usage:
- `/spike <slug> <question>` — start a spike, e.g.
  `/spike event-ordering can we keep ordering guarantees without a broker?`
- `/spike <slug>` — resume one already in progress

The spike's only durable outputs are **an ADR in `docs/decisions/`** and, when
it helps, a `CONTEXT.md` term. Prototype code stays on the `spike/<slug>` branch
and is never merged. Nothing here writes `openspec/specs/`, `tasks.md`, or a
delta spec — a spike answers *how*, and the change loop still owns *what*.

Exit through `/crystallize`, with the how settled and an ADR to point at.

---

```bash
set -e

SLUG=$(echo "$ARGUMENTS" | awk '{print $1}')
# cut -f2- echoes the whole field when there is no delimiter, so a bare slug
# would come back as its own question.
QUESTION=""
case "$ARGUMENTS" in
  *\ *) QUESTION=$(echo "$ARGUMENTS" | cut -d' ' -f2-) ;;
esac

if [ -z "$SLUG" ]; then
  echo "ERROR: usage is /spike <slug> <question>" >&2
  echo "" >&2
  echo "Spikes in progress:" >&2
  git branch --list 'spike/*' >&2 || true
  exit 1
fi

case "$SLUG" in
  *[!a-z0-9-]*)
    echo "ERROR: slug must be kebab-case (a-z, 0-9, -), got '$SLUG'" >&2
    exit 1
    ;;
esac

BRANCH="spike/$SLUG"

if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git switch "$BRANCH" >/dev/null 2>&1
  echo "=== Resuming $BRANCH ==="
  echo "Commits so far:"
  git log --oneline "$(git merge-base main "$BRANCH")..$BRANCH" 2>/dev/null || echo "  (none yet)"
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
echo "=== Available if the question needs them (read by name, do not bulk-read) ==="
for f in docs/architecture.md docs/product.md CONTEXT-MAP.md; do
  [ -f "$f" ] && echo "  $f"
done
echo "  openspec list --specs     — the capability index"
echo "  git branch --list 'spike/*'  — other spikes"
```

After the preamble runs:

1. **Interview before you build.** Invoke the **`grilling`** skill and work the
   design tree in rounds. Most of what looks like a coding question is an
   undecided requirement, and an interview settles those far faster than a
   prototype does. Facts are yours to find; decisions are the user's.
2. Invoke **`domain-modeling`** alongside it. When a term settles, write it to
   `CONTEXT.md` there and then. When the user's word conflicts with the
   glossary, say so immediately — that conflict is usually the real question.
3. **Prototype only what the interview cannot settle.** For each question that
   genuinely needs running code, invoke the **`prototype`** skill. Throwaway
   from day one, no persistence, no tests, no abstractions; surface the state
   after every action so the user can see what changed. Commit prototypes to
   this branch — that is what the branch is for.
4. **Time-box it and say so.** State up front how long you expect to spend and
   what would make you stop. A spike that cannot answer its question is a
   result: record what you ruled out.
5. **Capture the answer as an ADR** in `docs/decisions/`, following that
   directory's `index.md` convention, and add its index row in the same commit.
   Record what lost and why — the rejected option is what stops the question
   being reopened in six months. Reference this branch by name so the prototype
   remains findable.
6. **Stop at the gate.** Show the user the ADR and wait. An unaccepted ADR is
   not a decision, and the change loop must not consume one.
7. Once accepted, hand over:

   ```
   /crystallize <the idea, now with its how settled — cite the ADR>
   ```

   The ADR is the input to the change's `design.md`. Do not write the proposal,
   the delta specs, or `tasks.md` here.

**Leave the branch unmerged.** `spike/<slug>` is a primary source, not work in
flight: the validated decision reaches `main` as an ADR through `/crystallize`
and a normal PR, and the throwaway code stays where it can be read but never
runs in production. Delete the branch only when the ADR that cites it is
superseded.
