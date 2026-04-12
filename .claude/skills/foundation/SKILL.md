---
name: agentic-project-scanner
description: Scans a project to check if it is correctly set up for the BMAD + Superpowers agentic engineering workflow. Use this skill whenever the user says "scan my project", "check my setup", "is my project clean", "did setup work", "migrate from BMAD", or wants to verify the agentic project structure is correct before starting a sprint. Also trigger when the user mentions they've just run setup_agentic_project.py or installed BMAD/Superpowers.
---

# Agentic project scanner

Checks that a project is correctly structured for the BMAD + Superpowers workflow.
Produces a clear pass/fail report with actionable fixes.

## When to use

- After running `setup_agentic_project.py`
- After migrating from a BMAD-only project
- Before starting a new sprint (quick sanity check)
- When something feels wrong with the pipeline

## What to scan

Run all checks below. Group results into PASS / WARN / FAIL.

---

## Checks

### 1. Kanban folders

Required folders must all exist:

```
stories/draft/
stories/ready/
stories/in-progress/
stories/review/
stories/done/
```

FAIL if any are missing.
PASS if all present (empty is fine).

---

### 2. CLAUDE.md

- FAIL if `CLAUDE.md` does not exist at project root
- WARN if it exists but still contains the placeholder text `Edit it to reflect your actual conventions`
- PASS if it exists and looks customised

---

### 3. docs/ artefacts

Check for `docs/prd.md` and `docs/architecture.md`.

- FAIL if neither exists (planning hasn't run yet)
- WARN if only one exists
- PASS if both exist

Do NOT check `_bmad/output/` for these — only `docs/` counts as the approved copy.

---

### 4. BMAD output leftover check

Look for `_bmad/output/` (or `_bmad/`) containing `.md` files.

- WARN if files exist there that have NOT been copied to `docs/` or `stories/draft/`
  — this means the migration is incomplete
- PASS if `_bmad/` doesn't exist, or all its artefacts are already reflected in `docs/` and `stories/`

To check: list filenames in `_bmad/` and compare against filenames in `docs/` and `stories/draft/`.

---

### 5. BMAD developer/reviewer agents

Check `.claude/agents/` for any agent file whose name or content suggests it is the BMAD developer or BMAD reviewer agent (e.g. names like `developer.md`, `dev-agent.md`, `reviewer.md`, `bmad-dev.md`).

- WARN if found — these should be removed because Superpowers owns implementation and `/review` owns code review. Keeping them risks accidental use.
- PASS if absent

Hint: open each `.md` file in `.claude/agents/` and look for phrases like "implement the story", "write the code", "review the PR" in the BMAD agent style (not the Superpowers style).

---

### 6. Story file quality spot-check

Pick up to 3 story files from `stories/draft/` or `stories/ready/` and check each for:

- [ ] Acceptance criteria section present
- [ ] File paths mentioned (not just vague feature description)
- [ ] Test strategy mentioned

WARN (not FAIL) if stories are missing these — vague stories produce bad Superpowers output.
PASS if stories look self-contained.
SKIP if no stories exist yet (that's fine at setup time).

---

### 7. Git initialised

Check that `.git/` exists at project root.

- WARN if absent — worktree isolation (used by auto-loop) requires git
- PASS if present

---

## Output format

Print a summary table, then a section for each non-passing item with a one-line fix.

Example:

```
Agentic project scan
====================
Root: /path/to/project

  PASS  Kanban folders
  PASS  CLAUDE.md
  WARN  CLAUDE.md not customised — edit it before starting implementation
  FAIL  docs/prd.md missing — run /prd in BMAD to generate it
  WARN  _bmad/output/story-001.md not migrated — run setup_agentic_project.py
  WARN  .claude/agents/developer.md found — remove it (Superpowers handles implementation)
  PASS  Git initialised

3 issues found (1 FAIL, 2 WARN)
Fix the FAIL before starting. WARNs are safe to defer.
```

Always end with a one-line verdict:
- "Ready to plan — run /plan in BMAD to start."  (all PASS)
- "Ready to implement — move stories to stories/ready/ and run /implement."  (docs exist, stories in draft)
- "Fix the FAILs above before proceeding."  (any FAIL present)

---

## How to run the scan

Use `bash_tool` to inspect the filesystem. Key commands:

```bash
# Check kanban folders
ls stories/ 2>/dev/null || echo "stories/ missing"

# Check CLAUDE.md
cat CLAUDE.md 2>/dev/null | head -5

# Check docs
ls docs/ 2>/dev/null

# Find leftover BMAD artefacts
find _bmad -name "*.md" 2>/dev/null

# List agent files
ls .claude/agents/ 2>/dev/null

# Check git
ls .git/ 2>/dev/null | head -1
```

Run these from the project root. Ask the user for the project path if not obvious from context.
