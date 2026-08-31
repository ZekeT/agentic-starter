---
name: rescan-docs
description: >
  Reverse-engineer behaviour specs and product intent from an existing codebase,
  so the change loop has a documented baseline to work from. Use when adopting
  this harness on a brownfield project, when openspec/specs/ is empty or stale,
  or after inheriting a codebase with no planning artefacts. Trigger on:
  "rescan docs", "generate specs from code", "reverse-engineer architecture",
  "create docs from codebase", "what does this system currently do".
---

# Rescan-Docs Skill

Analyse an existing codebase and produce the loop's durable truth: behaviour
specs in `openspec/specs/`, plus `docs/product.md` and `docs/architecture.md`.

The output is **what the code does**, which is not always what it *should* do.
Every artefact this skill writes is a draft for a human to correct, never an
authority.

**Announce at start:** "I'm using the rescan-docs skill to generate planning documents from the existing codebase."

**Output directory:** `docs/` — never overwrites existing files (collisions get
timestamped `*-rescan-{date}.md` siblings the human diffs and merges).

---

## When to use this skill

- Migrating an existing project that has no PRD or architecture doc
- Docs are stale and no longer reflect the codebase
- Inheriting a codebase from another team
- After running `scripts/migrate_to_framework.py` — that sets up structure; this skill fills in content

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
> 5. **What should the next change be?** (The first thing you'd crystallize)"

Wait for answers before proceeding. Their answers fill in the "why" — the code only shows the "what".

---

## Step 3 — Generate product intent

Write `docs/product.md`: what the product is, who it's for, why it exists, and
its non-goals. Fill every section from your analysis and the user's answers.
Do not leave placeholders.

If `docs/product.md` already exists with real (non-placeholder) content, write
`docs/product-rescan-{date}.md` instead and tell the user to diff them. Never
overwrite.

```markdown
# Product
> Reverse-engineered from the codebase on {date}. Review and edit before treating as authoritative.

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

Write `docs/architecture.md` using this structure.

If `docs/architecture.md` already exists with real (non-placeholder) content,
create `docs/architecture-rescan-{date}.md` instead.

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

## Step 5 — Generate behaviour specs

This is the important output. `openspec/specs/` is what makes "what does this
system currently do?" answerable without reading code.

**Slice into capabilities.** A capability is *something you would plausibly
rewrite or delete as a unit* — not one per file, and not one per layer. Derive
them from the code's actual seams: an auth module, a payment integration, a CLI
surface. Aim for a handful, not dozens.

For each capability write `openspec/specs/<capability-path>/spec.md`:

```markdown
# <capability> Specification

## Purpose
One or two sentences (50+ chars) on what this capability is for.

## Requirements

### Requirement: <name>
The system SHALL <observable behaviour>.

#### Scenario: <name>
- **WHEN** <condition>
- **THEN** <expected outcome>
```

Rules that keep specs useful:

- Describe **observable behaviour only** — inputs, outputs, error conditions,
  external constraints. If the implementation could change without changing
  what a caller sees, it does not belong here.
- Never name internal classes, functions, or libraries.
- Every requirement needs at least one `#### Scenario:` block, or
  `openspec validate` rejects it.
- Only write a requirement you can point at real code for. A spec that
  describes intentions rather than behaviour is worse than no spec.

Never write into `openspec/changes/` here — that is for work in flight, and
nothing is in flight during a rescan.

Verify before reporting:

```bash
openspec validate --all
openspec list --specs
```

**Gaps go in the report, not into specs.** TODO/FIXME items, untested files,
and missing features describe what the system *doesn't* do. Collect them for
Step 6 so the user can crystallize them into real changes:

```bash
grep -rn "TODO\|FIXME\|XXX\|HACK" --include="*.py" . 2>/dev/null | head -20

find . -name "*.py" -not -path "*/test*" -not -path "*__pycache__*" \
  -not -name "setup.py" -not -name "conftest.py" \
  -not -path "*/.git/*" 2>/dev/null | while read f; do
  base=$(basename "$f" .py)
  if ! find . \( -name "test_${base}.py" -o -name "${base}_test.py" \) 2>/dev/null | grep -q .; then
    echo "No test: $f"
  fi
done | head -10
```

## Step 6 — Final report

Print a summary:

```
Rescan complete
===============
Specs:         openspec/specs/<capability>/spec.md   ({N} capabilities, {M} requirements)
Product:       docs/product.md
Architecture:  docs/architecture.md                  ({N} components mapped)

Everything above is reverse-engineered from code — it describes what the system
DOES, not what it SHOULD do. Review before treating any of it as authoritative.

Gaps found (not written to specs — specs describe current behaviour only):
  - {N} TODO/FIXME markers
  - {N} source files with no test
  - {N} features the interview named as planned but unbuilt

Next: /crystallize "<one of the gaps above>" to open your first change.
```

---

## Guardrails

- **Never overwrite** an existing file in `docs/` or `openspec/specs/` — write a
  timestamped `*-rescan-{date}.md` sibling and tell the user to diff them.
- **Never write to `openspec/changes/`.** Nothing is in flight during a rescan.
  Gaps belong in the report so a human can crystallize them deliberately.
- **Specs describe behaviour that exists.** A gap is the absence of behaviour, so
  it is never a spec. Writing aspirational specs is the exact failure mode —
  a PRD wearing a spec's clothes — that this harness exists to prevent.
- **Flag uncertainty** — if something can't be inferred from code, write
  `<!-- UNKNOWN: what's missing -->` rather than guessing.
- **Quality over quantity** — a handful of accurate capabilities beats twenty
  speculative ones. Say so when the codebase is too thin to spec confidently.
