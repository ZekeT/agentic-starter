# Story {NNN}: {Title}

> Copy this file to `stories/draft/story-{NNN}-{slug}.md` and fill it in.
> A story file is the complete context a developer agent needs — no other
> files should be required to understand and implement this story.
> Principle: the story file is the complete context.

---

## Status
<!-- draft | ready | in-progress | review | done -->
draft

## What to build

<!-- User story format: "As a [role], I want [goal] so that [reason]" -->
As a ...

<!-- Feature description: what does this actually do? -->

---

## Files to touch

<!-- Be specific. Vague stories produce garbage implementations. -->
- `src/module/file.py` — [what changes and why]
- `tests/test_file.py` — [what tests to add]

---

## Feature context

- [ ] If this story creates a new feature directory, scaffold `CLAUDE.md`
      in it (purpose, entry points, invariants — max ~30 lines).
- [ ] If this story changes a feature's invariants or entry points, update
      that feature's `CLAUDE.md`.
- [ ] Add/refresh the one-line pointer in the root CLAUDE.md structure table.

---

## Acceptance criteria

<!-- Each criterion must be independently testable. -->
- [ ] ...
- [ ] ...
- [ ] `make check` passes (fmt + lint + test)
- [ ] Docstring coverage ≥ 80%

---

## Test strategy

**Unit tests** (`tests/unit/`):
- ...

**Integration tests** (`tests/integration/`):
- ...

**E2E** (if applicable):
- ...

---

## Architectural constraints

<!-- What patterns must be followed? What must be avoided? -->
- Follow existing patterns in `src/` — read `docs/architecture.md` §[section]
- Use `pathlib.Path` for all file paths
- No direct database access from API layer (go through service layer)

---

## Out of scope

<!-- Explicitly list what this story does NOT cover. -->
- ...

---

## Dependencies

<!-- Other stories that must be done first, if any. -->
- None

---

## Notes for agent

<!-- Anything that would help the agent avoid wrong turns. -->
- If `graphify-out/GRAPH_REPORT.md` exists, read it before exploring the codebase
- Read `CLAUDE.md` for build commands and conventions
