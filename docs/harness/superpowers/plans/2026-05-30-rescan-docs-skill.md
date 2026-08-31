# rescan-docs Skill + Doc Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `rescan-docs` skill that reverse-engineers PRD + architecture docs + story stubs from an existing codebase, and fix inconsistencies in SETUP.md and setup-migrate.

**Architecture:** A new SKILL.md-based skill guides Claude Code through: (1) running graphify to build a knowledge graph, (2) interviewing the user to distinguish current vs desired state, (3) generating BMAD-format PRD/architecture docs, (4) generating draft story stubs. Doc fixes are surgical edits to SETUP.md and the setup-migrate skill.

**Tech Stack:** Markdown skill files, BMAD doc format, graphify CLI output.

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `.claude/skills/rescan-docs/SKILL.md` | **Create** | New skill: codebase → BMAD docs |
| `docs/SETUP.md` | **Modify** | Remove stale agent entries; add Superpowers install step; clarify /dev-story vs /implement |
| `.claude/skills/setup-migrate/SKILL.md` | **Modify** | Add Step 9 that invokes `rescan-docs` after structural scaffold |
| `CLAUDE.md` | **Modify** | Add `rescan-docs` entry to Agent Team table and Project Structure |

---

## Task 1: Create the `rescan-docs` skill

**Files:**
- Create: `.claude/skills/rescan-docs/SKILL.md`

- [ ] **Step 1: Write the skill file**

Content for `.claude/skills/rescan-docs/SKILL.md`:

```markdown
---
name: rescan-docs
description: >
  Reverse-engineer BMAD planning documents (PRD, architecture, story stubs) from
  an existing codebase. Use when migrating a project to the Agentic Engineering
  framework, when docs are missing or stale, or after inheriting a codebase with
  no planning artefacts. Trigger on: "rescan docs", "generate PRD from code",
  "reverse-engineer architecture", "create docs from codebase", "rescan to generate stories".
---

# Rescan-Docs Skill

Analyse an existing codebase and produce BMAD-format planning documents so the
full agentic pipeline can resume from a documented baseline.

**Announce at start:** "I'm using the rescan-docs skill to generate BMAD documents from the existing codebase."

**Output directory:** `_bmad-output/` — same location BMAD uses. Human reviews before copying to `docs/`.

---

## When to use this skill

- Migrating an existing project that has no PRD or architecture doc
- Docs are stale and no longer reflect the codebase
- Inheriting a codebase from another team
- After running `setup-migrate` — that skill sets up structure; this skill fills in content

---

## Step 0 — Check graphify output

```bash
ls graphify-out/ 2>/dev/null || echo "no graphify output"
cat graphify-out/GRAPH_REPORT.md 2>/dev/null | head -5 || echo "no GRAPH_REPORT.md"
```

- If `graphify-out/GRAPH_REPORT.md` exists and is recent (check file mod time vs `git log -1`):
  skip to Step 1.
- Otherwise run graphify:

```bash
graphify . 2>/dev/null || echo "graphify not installed — run: pip install graphify-cli"
```

If graphify is not installed, proceed without it — fall back to reading key files
directly (entry points, config files, top-level modules, README).

---

## Step 1 — Orient from the knowledge graph

Read `graphify-out/GRAPH_REPORT.md` (or fallback files below) and answer these
questions for yourself. Do NOT ask the user yet — derive what you can from the code.

**From the graph/files, identify:**

1. **Entry points** — what are the top-level executables, API handlers, or CLI commands?
2. **Core modules** — what are the 3–5 most-connected modules?
3. **External dependencies** — what third-party libraries does this project use?
4. **Data stores** — databases, caches, file storage, queues?
5. **User-facing surfaces** — web UI, REST API, CLI, background jobs?
6. **Tech stack** — language, framework, test runner, build system?

Fallback if no graph: scan these files:
```bash
# Identify entry points and stack
find . -name "main.py" -o -name "index.ts" -o -name "main.go" -o -name "app.py" \
  -o -name "server.py" -o -name "cli.py" | head -10
cat README.md 2>/dev/null | head -60
cat pyproject.toml 2>/dev/null | head -40
cat package.json 2>/dev/null | head -30
```

---

## Step 2 — Interview the user (5 questions max)

Ask the following questions in a single message. Do not ask them one at a time.

> "I've analysed the codebase. Before I generate the docs, I need five answers:
>
> 1. **What does this system do?** (One sentence for non-technical users)
> 2. **Who are the primary users?** (e.g. internal team, paying customers, API consumers)
> 3. **What's missing or incomplete?** (Features you know aren't implemented yet)
> 4. **What's tech debt or known problems?** (Things that work but shouldn't stay this way)
> 5. **What's the next sprint goal?** (What should the team be working on next?)"

Wait for answers before proceeding. Their answers fill in the "why" — the code only shows the "what".

---

## Step 3 — Generate the PRD

Write `_bmad-output/prd.md` using this structure. Fill every section from your
analysis and the user's answers. Do not leave any section as a placeholder.

```markdown
# Product Requirements Document
> Reverse-engineered from codebase on {date}. Review and edit before treating as authoritative.

## Problem Statement
{what problem this system solves — from user interview}

## Target Users
{who uses it and how — from user interview + UX surfaces identified in Step 1}

## Current Functionality (implemented)
{bullet list of features that exist in the code — be specific, name endpoints/commands/modules}

## Planned Functionality (not yet implemented)
{bullet list from user interview answer 3 + any TODOs/FIXMEs found in code}

### Scan for incomplete features:
```bash
grep -r "TODO\|FIXME\|HACK\|XXX\|PLACEHOLDER\|NotImplemented" \
  --include="*.py" --include="*.ts" --include="*.go" \
  -l 2>/dev/null | head -20
```

## Success Metrics
{how success is measured — ask if not obvious from code}

## Constraints
{tech constraints from code: language runtime, deployment target, external APIs required}

## Out of Scope
{what this system explicitly does NOT do — infer from missing obvious features}
```

---

## Step 4 — Generate the architecture doc

Write `_bmad-output/architecture.md` using this structure.

```markdown
# Architecture Document
> Reverse-engineered from codebase on {date}. Review and edit before treating as authoritative.

## System Overview
{2-3 sentence summary of what this system is}

## Tech Stack
| Layer | Technology |
|-------|------------|
| Language | {e.g. Python 3.11} |
| Framework | {e.g. FastAPI, Django, Flask, none} |
| Database | {e.g. PostgreSQL via SQLAlchemy, none} |
| Test runner | {e.g. pytest, jest, go test} |
| Build/package | {e.g. uv + pyproject.toml, npm, cargo} |
| Deployment | {e.g. Docker, bare metal, inferred from Dockerfile/fly.toml} |

## Component Map
{List top-level modules/packages with one-line description each}
{Derive from graphify community clusters or directory listing}

## Data Flow
{Describe how data enters the system, is processed, and exits}
{Identify: inputs → processing → outputs → storage}

## External Integrations
{List every third-party API, SDK, or service the code calls}

```bash
grep -r "import\|require\|from" --include="*.py" --include="*.ts" \
  . 2>/dev/null | grep -v "^Binary\|node_modules\|__pycache__" \
  | sed 's/.*import //' | sort -u | head -40
```

## Security Boundaries
{Where does untrusted input enter? Where is auth enforced?}
{Infer from middleware, decorators, env var usage}

## Known Technical Debt
{From user interview answer 4 + grep for TODO/FIXME/HACK}

## Open Architecture Questions
{Decisions that aren't clear from the code — flag these for the human to answer}
```

---

## Step 5 — Generate story stubs for gaps

Create one story file per identified gap in `stories/draft/`. Use the template:

```bash
cat stories/STORY_TEMPLATE.md 2>/dev/null || echo "no template"
```

**Sources for stories:**

1. **Planned features** from PRD section "Planned Functionality"
2. **TODO/FIXME items** from the grep in Step 3
3. **Tech debt** from user interview answer 4
4. **Test coverage gaps:**
```bash
# Find source files with no corresponding test file
find . -name "*.py" -not -path "*/test*" -not -path "*__pycache__*" \
  -not -name "setup.py" -not -name "conftest.py" 2>/dev/null | while read f; do
  base=$(basename "$f" .py)
  if ! find . -name "test_${base}.py" -o -name "${base}_test.py" 2>/dev/null | grep -q .; then
    echo "No test for: $f"
  fi
done | head -10
```

**Story file format** (one file per story, `stories/draft/story-NNN-<slug>.md`):

```markdown
# Story NNN: <title>

**Type:** feature | bug | tech-debt | test-coverage

## User Story
As a {user type}, I want {capability} so that {benefit}.

## Background
{Why this exists — link to PRD section or tech debt source}

## Acceptance Criteria
- [ ] {Testable criterion 1}
- [ ] {Testable criterion 2}

## Files to Touch
- `src/path/to/file.py` — {what changes}
- `tests/path/to/test_file.py` — {new tests}

## Test Strategy
{Unit / integration / e2e — what to test and how}

## Architectural Constraints
{Any constraints from architecture.md that apply here}
```

Number stories starting from 001. If stories already exist in `stories/draft/`,
find the highest existing number and continue from there.

---

## Step 6 — Final report

Print a summary:

```
Rescan complete
===============
PRD:           _bmad-output/prd.md          ({N} features documented)
Architecture:  _bmad-output/architecture.md  ({N} components mapped)
Stories:       stories/draft/story-{NNN}-*.md  ({N} stories created)

Review _bmad-output/ before running /gate-check.
Move stories from stories/draft/ to stories/ready/ when ready to implement.

Next: /gate-check — validates PRD ↔ architecture consistency
```

---

## Guardrails

- **Do not overwrite** existing files in `_bmad-output/` or `docs/` — create with
  a timestamp suffix (`prd-rescan-2026-05-30.md`) and tell the user to diff them
- **Flag uncertainty** — if a section can't be inferred from code, say so explicitly
  in the doc rather than guessing (use `<!-- UNKNOWN: explain what's missing -->`)
- **Do not generate stories for things that are clearly done** — only gaps and debt
- **Quality over quantity** for stories — 5 well-specified stories beat 20 vague ones
```

- [ ] **Step 2: Verify the file was written correctly**

```bash
head -10 .claude/skills/rescan-docs/SKILL.md
wc -l .claude/skills/rescan-docs/SKILL.md
```

Expected: frontmatter present, file is 150+ lines.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/rescan-docs/SKILL.md
git commit -m "feat(skills): add rescan-docs skill for reverse-engineering BMAD docs from code"
```

---

## Task 2: Fix SETUP.md inconsistencies

**Files:**
- Modify: `docs/SETUP.md`

**Problems to fix:**
1. `.claude/agents/` shows `developer.md` and `code-reviewer.md` — these don't exist and CLAUDE.md says they shouldn't (Superpowers owns them)
2. No mention of Superpowers install as a required step
3. `/implement` is listed as the implementation command but `/dev-story` is the canonical one

- [ ] **Step 1: Read the current SETUP.md fully**

```bash
cat docs/SETUP.md
```

- [ ] **Step 2: Fix the agents section in SETUP.md**

In the project structure tree, find this block:
```
│   ├── agents/                          # Our implementation agents
│   │   ├── developer.md                 # TDD (Sonnet + Opus advisor)
│   │   ├── code-reviewer.md             # PR review, read-only (Opus)
│   │   └── security-reviewer.md         # OWASP/CVE scan, read-only (Opus)
```

Replace with:
```
│   ├── agents/                          # Project-specific agents only
│   │   └── security-reviewer.md         # OWASP/CVE scan, read-only (Opus)
│   │                                    # Note: developer + code-reviewer live in
│   │                                    # Superpowers (~/.claude/) — not here
```

- [ ] **Step 3: Add Superpowers install step**

After the `bash setup.sh` step, add:

```markdown
Then install Superpowers **once per machine** inside Claude Code:

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

This installs implementation skills (TDD, subagent dispatch, code review) globally
to `~/.claude/`. Required for `/dev-story` and `/implement` to work correctly.
```

- [ ] **Step 4: Fix /implement reference in the pipeline table**

In the pipeline table, change:
```
| Implement | `/implement story-NNN` | code on a worktree branch |
```

To:
```
| Implement | `/dev-story [id]` | code on a worktree branch (full lifecycle) |
```

Add a note below the table:
```markdown
> `/implement story-NNN` also works as a lighter alias, but `/dev-story` handles
> the kanban file moves (ready → in-progress → review) automatically.
```

- [ ] **Step 5: Add rescan-docs to the "Optional add-ons" section (or create one if absent)**

Add a section near the bottom of SETUP.md:

```markdown
## Migrating an existing project

If you're adopting this framework on an existing codebase (rather than starting fresh):

```bash
python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/your/project
```

Then open Claude Code in that project and run:

```
/rescan-docs    # Analyses your codebase → generates PRD + architecture + story stubs
/gate-check     # Validates consistency before implementing
```
```

- [ ] **Step 6: Commit**

```bash
git add docs/SETUP.md
git commit -m "fix(docs): remove stale agent entries, add Superpowers install step, clarify /dev-story vs /implement"
```

---

## Task 3: Update setup-migrate skill — add Step 9 (rescan-docs)

**Files:**
- Modify: `.claude/skills/setup-migrate/SKILL.md`

- [ ] **Step 1: Read the end of the setup-migrate skill**

```bash
tail -60 .claude/skills/setup-migrate/SKILL.md
```

- [ ] **Step 2: Add Step 9 before the "Decision reference" section**

Find the `## Step 8 — Final validation` section ending and add after it:

```markdown
---

## Step 9 — Generate planning docs from existing code (optional)

If the target project has no PRD or architecture doc, or if docs are stale,
invoke the `rescan-docs` skill to reverse-engineer them:

**Invoke the Skill tool:**
```
skill: "rescan-docs"
```

The skill will:
1. Build a graphify knowledge graph of the codebase
2. Interview the user (5 questions) to understand intent vs. current state
3. Write `_bmad-output/prd.md` — reverse-engineered PRD
4. Write `_bmad-output/architecture.md` — component map and tech stack
5. Create story stubs in `stories/draft/` for identified gaps

**When to skip this step:**
- The project already has up-to-date `docs/prd.md` and `docs/architecture.md`
- The user explicitly says they will write docs themselves

After Step 9 completes, tell the user:
> "Migration complete. Run `/gate-check` to validate PRD ↔ architecture consistency,
> then move stories from `stories/draft/` to `stories/ready/` when ready."
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/setup-migrate/SKILL.md
git commit -m "feat(skills): add Step 9 to setup-migrate — invoke rescan-docs for doc generation"
```

---

## Task 4: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add rescan-docs to Project Structure section**

In the skills listing inside `## Project Structure`, after the `setup-migrate/` entry:

```
    setup-migrate/  # Migration skill for existing projects
      scripts/
        setup_migrate.py       # Full audit + scaffold for existing projects
    rescan-docs/             # Reverse-engineer PRD + arch + stories from code
```

- [ ] **Step 2: Update the skill trigger table in the "Workflow" section if present**

In `## Workflow (Agentic Engineering Pipeline)`, if there's a migration subsection, add:

```
`/rescan-docs` → `rescan-docs` skill — codebase analysis → `_bmad-output/prd.md`, `architecture.md`, `stories/draft/`
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): register rescan-docs skill in project structure and workflow"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|-------------|------|
| Create rescan-docs skill | Task 1 |
| Skill analyses code → PRD | Task 1, Steps 1-3/4 |
| Skill analyses code → architecture doc | Task 1, Step 4 |
| Skill generates story stubs for gaps | Task 1, Step 5 |
| Fix SETUP.md agent inconsistency | Task 2, Step 2 |
| Add Superpowers install to SETUP.md | Task 2, Step 3 |
| Clarify /dev-story vs /implement | Task 2, Step 4 |
| Wire rescan-docs into setup-migrate | Task 3 |
| Update CLAUDE.md registry | Task 4 |

**No placeholders found** — all steps contain actual content.

**Type consistency** — skill steps use consistent file paths throughout.
