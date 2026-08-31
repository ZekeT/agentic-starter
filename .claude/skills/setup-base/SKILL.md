---
name: setup-base
description: >
  Scans a project to check if it is correctly set up for the Superpowers
  agentic engineering workflow. Use this skill whenever the user says "scan my
  project", "check my setup", "is my project clean", "did setup work", or wants
  to verify the agentic project structure is correct before starting a sprint.
  Also trigger when the user mentions they've just run setup_base.py or installed
  Superpowers.
---

# Foundation

Checks that a project is correctly structured for the Superpowers workflow.
Produces a clear pass/fail report with actionable fixes.

## When to use

- After running `setup_base.py`
- After running the `setup-migrate` skill (or its `setup_migrate.py` audit script)
- Before starting a new sprint (quick sanity check)
- When something feels wrong with the pipeline

## What to scan

Run all checks below. Group results into PASS / WARN / FAIL.

---

## Checks

### 1. Kanban folders

Required folders must all exist:

```
openspec/specs/
openspec/changes/
openspec/changes/archive/
docs/decisions/
```

FAIL if any are missing.
PASS if all present (empty is fine).

---

### 2. CLAUDE.md

- FAIL if `CLAUDE.md` does not exist at project root
- WARN if it exists but still contains the placeholder text
  `Edit it to reflect your actual conventions`
- PASS if it exists and looks customised

---

### 3. docs/ artefacts

Check for `docs/product.md`, `docs/architecture.md`, and `openspec/config.yaml`.

- FAIL if neither exists (planning hasn't run yet)
- WARN if only one exists
- PASS if both exist

---

### 4. Stale agents in `.claude/agents/`

**Only `security-reviewer.md` should exist here.**

WARN if any of these are found — they belong to other tools:
- `developer.md`, `dev-agent.md` → Superpowers owns implementation
  (installed globally to `~/.claude/` via `/plugin install`)
- `code-reviewer.md`, `reviewer.md` → Superpowers owns code review
- `analyst.md`, `pm.md`, `architect.md`, `scrum-master.md`
  → planning is conversational (Superpowers brainstorming / writing-plans);
  change breakdown is `/crystallize` — no agents needed

---

### 5. Python hooks

Check `.claude/hooks/` for our 4 hooks:

```
pre_tool_dangerous.py
pre_tool_env_guard.py
post_tool_secrets.py
post_tool_lint.py
```

FAIL if any are missing — run the `setup-migrate` skill's scaffold
(`python .claude/skills/setup-migrate/scripts/setup_migrate.py .`) to create them.

---

### 6. Change quality spot-check

Pick up to 3 active changes from `openspec/changes/` and check each for:

- [ ] `proposal.md` names its capabilities under New/Modified
- [ ] Delta specs use `#### Scenario:` blocks with WHEN/THEN, not prose
- [ ] `tasks.md` groups are independently shippable (each `## N` = one PR)
- [ ] `openspec validate <slug>` passes

WARN (not FAIL) on gaps — a vague change produces bad Superpowers output.
PASS if `openspec validate --all` is clean.
SKIP if no changes exist yet (fine at setup time).

---

### 7. Superpowers installed

Check whether the Superpowers plugin is installed globally. Plugins live in
the plugin cache, not `~/.claude/skills/`:

```bash
ls ~/.claude/plugins/cache/superpowers-marketplace/superpowers/ 2>/dev/null
```

- WARN if not found — run inside Claude Code:
  `/plugin marketplace add obra/superpowers-marketplace`
  `/plugin install superpowers@superpowers-marketplace`
- WARN if only versions < 6 are present — this template assumes the v6
  unified reviewer; run `/plugin update superpowers@superpowers-marketplace`
- PASS if a version 6.x (or newer) directory exists

Note: Superpowers cannot be installed from a shell script — it requires
an interactive Claude Code session.

---

### 8. Git initialised

Check that `.git/` exists at project root.

- WARN if absent — worktree isolation (used by Superpowers) requires git
- PASS if present

---

### 9. .env.template

- WARN if `.env.template` doesn't exist — new team members won't know what env vars are needed
- PASS if it exists

---

## Output format

Print a summary table, then a section for each non-passing item with a one-line fix.

```
Agentic project scan
====================
Root: /path/to/project

  PASS  Kanban folders
  PASS  CLAUDE.md
  WARN  CLAUDE.md not customised — edit before starting implementation
  FAIL  docs/product.md missing — write it before crystallizing the first change
  WARN  .claude/agents/developer.md found — remove (Superpowers owns implementation)
  PASS  Python hooks present
  PASS  Git initialised

3 issues found (2 FAIL, 1 WARN)
Fix the FAILs before starting. WARNs are safe to defer.
```

Always end with a one-line verdict:
- "Ready to plan — start a planning conversation (Superpowers brainstorming)."  (all PASS, no docs yet)
- "Ready to implement — run /dev-change <slug> <group>."  (a change has tasks)
- "Fix the FAILs above before proceeding."  (any FAIL present)

---

## How to run the scan

Use bash tool to inspect the filesystem. Key commands:

```bash
# Kanban
ls openspec/changes/ 2>/dev/null

# CLAUDE.md
head -5 CLAUDE.md 2>/dev/null

# Docs
ls docs/ 2>/dev/null

# Agents (should only be security-reviewer.md)
ls .claude/agents/ 2>/dev/null

# Hooks
ls .claude/hooks/ 2>/dev/null

# Git
ls .git/ 2>/dev/null | head -1

# .env.template
ls .env.template 2>/dev/null
```

Run from project root. Ask user for path if not clear from context.
