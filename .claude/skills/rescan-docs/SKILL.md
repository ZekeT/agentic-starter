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
graphify . 2>/dev/null || echo "graphify not installed — run: uv pip install graphifyy"
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

Fallback if no graph — scan these files:

```bash
# Identify entry points and stack
find . -name "main.py" -o -name "index.ts" -o -name "main.go" -o -name "app.py" \
  -o -name "server.py" -o -name "cli.py" | grep -v node_modules | head -10
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

If `_bmad-output/prd.md` already exists, create `_bmad-output/prd-rescan-{date}.md`
instead and tell the user to diff them.

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

## Success Metrics
{how success is measured — ask if not obvious from code}

## Constraints
{tech constraints from code: language runtime, deployment target, external APIs required}

## Out of Scope
{what this system explicitly does NOT do — infer from missing obvious features}
```

Find incomplete features with:

```bash
grep -r "TODO\|FIXME\|HACK\|XXX\|PLACEHOLDER\|NotImplemented" \
  --include="*.py" --include="*.ts" --include="*.go" --include="*.js" \
  -n 2>/dev/null | grep -v node_modules | grep -v ".git" | head -30
```

---

## Step 4 — Generate the architecture doc

Write `_bmad-output/architecture.md` using this structure.

If `_bmad-output/architecture.md` already exists, create
`_bmad-output/architecture-rescan-{date}.md` instead.

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
| Deployment | {inferred from Dockerfile / fly.toml / render.yaml / Procfile} |

## Component Map
{List top-level modules/packages with one-line description each.
Derive from graphify community clusters or directory listing.}

## Data Flow
{Describe how data enters the system, is processed, and exits.
Identify: inputs → processing → outputs → storage.}

## External Integrations
{List every third-party API, SDK, or service the code calls.}

## Security Boundaries
{Where does untrusted input enter? Where is auth enforced?
Infer from middleware, decorators, env var usage.}

## Known Technical Debt
{From user interview answer 4 + grep for TODO/FIXME/HACK.}

## Open Architecture Questions
{Decisions that aren't clear from the code — flag these for the human to answer.}
```

Identify external integrations with:

```bash
# Python
grep -r "^import\|^from" --include="*.py" . 2>/dev/null \
  | grep -v "^\./\." | sed 's/.*from //' | sed 's/ import.*//' \
  | sort -u | grep -v "^\." | head -30

# JS/TS
cat package.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(k) for k in {**d.get('dependencies',{}),**d.get('devDependencies',{})}.keys()]" 2>/dev/null | head -30
```

---

## Step 5 — Generate story stubs for gaps

Create one story file per identified gap in `stories/draft/`. Find the next
available story number:

```bash
ls stories/draft/ stories/ready/ stories/in-progress/ stories/review/ stories/done/ \
  2>/dev/null | grep "^story-" | sed 's/story-//' | cut -d- -f1 | sort -n | tail -1
```

Start numbering from that value + 1 (or 001 if no stories exist).

**Sources for stories (in priority order):**

1. Planned features from the PRD "Planned Functionality" section
2. TODO/FIXME items from the grep in Step 3
3. Tech debt from user interview answer 4
4. Files with no test coverage:

```bash
find . -name "*.py" -not -path "*/test*" -not -path "*__pycache__*" \
  -not -name "setup.py" -not -name "conftest.py" \
  -not -path "*/.git/*" 2>/dev/null | while read f; do
  base=$(basename "$f" .py)
  if ! find . \( -name "test_${base}.py" -o -name "${base}_test.py" \) 2>/dev/null | grep -q .; then
    echo "No test: $f"
  fi
done | head -10
```

**Story file format** — write to `stories/draft/story-{NNN}-{slug}.md`:

```markdown
# Story {NNN}: {title}

**Type:** feature | bug | tech-debt | test-coverage

## User Story
As a {user type}, I want {capability} so that {benefit}.

## Background
{Why this exists — link to PRD section, TODO line, or tech debt description.}

## Acceptance Criteria
- [ ] {Testable criterion 1}
- [ ] {Testable criterion 2}

## Files to Touch
- `src/path/to/file.ext` — {what changes}
- `tests/path/to/test_file.ext` — {new or updated tests}

## Test Strategy
{Unit / integration / e2e — what to test and how}

## Architectural Constraints
{Any constraints from architecture.md that apply here}
```

Quality over quantity: generate 3–8 well-specified stories. Flag thin story
candidates to the user rather than writing vague stubs.

---

## Step 6 — Final report

Print a summary:

```
Rescan complete
===============
PRD:           _bmad-output/prd.md              ({N} features documented)
Architecture:  _bmad-output/architecture.md      ({N} components mapped)
Stories:       stories/draft/story-{NNN}-*.md    ({N} stories created)

Review _bmad-output/ before running /gate-check.
Move stories from stories/draft/ to stories/ready/ when ready to implement.

Next: /gate-check — validates PRD ↔ architecture consistency
```

---

## Guardrails

- **Do not overwrite** existing files in `_bmad-output/` or `docs/` — timestamp the
  new file and tell the user to diff them
- **Flag uncertainty** — if a section can't be inferred from code, say so explicitly
  in the doc with `<!-- UNKNOWN: explain what's missing -->` rather than guessing
- **Do not generate stories for things that are clearly done** — only gaps and debt
- **Quality over quantity** for stories — 5 well-specified stories beat 20 vague ones
