# /sprint-planning

Break the approved PRD and architecture into implementable story files in
`stories/draft/`. Planning conversations happen **before** this command via the
Superpowers **`brainstorming`** / **`writing-plans`** skills — this command only
converts approved docs into stories. It never moves stories to `ready/`; that
is the human gate.

Usage:
- `/sprint-planning` — plan from `docs/prd.md` + `docs/architecture.md`
- `/sprint-planning <focus>` — restrict to one epic or focus area

---

```bash
set -e

if [ ! -f docs/prd.md ] || [ ! -f docs/architecture.md ]; then
  echo "ERROR: docs/prd.md and docs/architecture.md are required."
  echo "Plan first (Superpowers brainstorming / writing-plans), write both docs,"
  echo "get them approved, then re-run /sprint-planning."
  exit 1
fi

mkdir -p stories/draft

echo "=== Existing stories (for numbering) ==="
HIGHEST=$(ls stories/draft stories/ready stories/in-progress stories/review stories/done 2>/dev/null \
  | grep "^story-" | sed 's/story-//' | cut -d- -f1 | sort -n | tail -1)
echo "Highest story number so far: ${HIGHEST:-none}"

echo "=== PRD ==="
cat docs/prd.md

echo "=== Architecture ==="
cat docs/architecture.md

echo "=== Story template ==="
cat stories/STORY_TEMPLATE.md
```

After the preamble runs:

1. Identify the unimplemented work the PRD describes, checked against the
   current codebase. If `$ARGUMENTS` names a focus area, restrict to it. If
   scope is ambiguous, ask the user once (a single message) before writing
   anything.
2. Slice the work into stories: each one independently implementable, sized
   for one PR / one `/dev-story` session. Note dependencies between stories
   and order the numbering so dependencies come first.
3. Write each story following `stories/STORY_TEMPLATE.md` exactly (Status /
   What to build / Files to touch / Acceptance criteria / Test strategy /
   Architectural constraints / Out of scope / Dependencies / Notes for agent).
   Acceptance criteria must be independently testable; Files-to-touch must
   name real paths.
4. Save each story as `stories/draft/story-{NNN}-{slug}.md`, continuing `NNN`
   from the highest number printed above across ALL five `stories/` dirs
   (start at `001` if none). Status stays `draft`.
5. Print a summary table (number, slug, dependencies) and remind the user to
   review each story, then `git mv` approved ones to `stories/ready/`.
