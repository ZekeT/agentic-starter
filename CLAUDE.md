# CLAUDE.md — Project Brain

> This file is committed to git and shared by all agents and sessions.
> Keep it short and high-signal. Add a rule every time Claude does something wrong.
> Source: Boris Cherny's workflow + Agentic Engineering guide (BMAD + Superpowers + Claude Code Primitives)

---

## Build & Dev Commands

```bash
make install          # install all deps (uv sync)
make fmt              # format: black + isort + autoflake
make lint             # check: black --check, isort --check, interrogate, mypy
make test             # pytest
make check            # fmt + lint + test (run before every commit)
make clean            # remove __pycache__, .pytest_cache, dist

make configure                       # apply config/models.json to all agents
make configure PROFILE=ollama-qwen   # switch to a named profile
make configure-show                  # print current model assignments
make configure-list                  # list available profiles
```

> Always run `make check` before committing. Never bypass it.
> After editing `config/models.json`, run `make configure`.

---

## Active Model Config

<!-- This section is auto-updated by scripts/configure.py — do not edit manually. -->
<!-- Run `make configure-show` to see current assignments. -->

Provider: `anthropic`

| Tier | Model |
|------|-------|
| planning | `claude-opus-4-8` |
| review | `claude-opus-4-8` |
| implement | `claude-sonnet-5` |
| fast | `claude-haiku-4-5-20251001` |

Advisor strategy: **enabled** — `claude-opus-4-8` advises executor agents (max 3 uses per request).
Source: https://claude.com/blog/the-advisor-strategy

---

## Advisor Strategy

Sonnet/Haiku **drives the full task** and escalates to Opus only when stuck.
This is the inverse of the usual orchestrator pattern — no decomposition,
no worker pool. Frontier reasoning applies only when the executor needs it.

When to invoke the advisor (executor agents should follow this):
- Architectural ambiguity that the story file doesn't resolve
- Conflicting requirements between PRD and architecture
- A blocking bug that's been attempted twice without success
- A security decision with non-obvious tradeoffs

Do **not** invoke for routine decisions. `max_uses: 3` enforces this.

The `advisor_20260301` tool is **Anthropic-only** — it won't be present in
agent definitions when using local models (`make configure PROFILE=ollama-*`).

---

## Tech Stack

- **Python**: managed via `uv` + `pyproject.toml`
- **Formatter**: `black` (line length 88)
- **Import sorter**: `isort` (black-compatible profile)
- **Unused import cleaner**: `autoflake`
- **Docstring coverage**: `interrogate` (min 80%)
- **Type checker**: `mypy` (strict mode)
- **Test runner**: `pytest`

Full coding standards → `docs/coding-standards.md`

---

## Coding Standards

> Full detail in `docs/coding-standards.md`. This is the agent-facing summary.
> Source: Google Style Guide + PEP 8 + project conventions.

### Python (primary language)

**Functions & size**
- Functions do one thing. If you can't name it without "and", split it.
- Heuristic: aim for < 20 lines. If a function is hard to name, it's doing too much.
- Prefer early returns over deep nesting — return/raise at the top, happy path at the bottom.

**DRY & simplicity (KISS)**
- Abstract shared logic into functions or modules. If you write it twice, extract it.
- Avoid "God classes". Use classes only for managing state. Use functions for logic.
- Prefer flat over nested: simple `if`/`for` over complex class hierarchies.

**Naming**
- Variables and functions: `snake_case`, descriptive, no single-letter names except loop counters.
- Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE`.
- Booleans: `is_`, `has_`, `can_` prefix (e.g. `is_valid`, `has_token`).
- Functions named as verbs: `fetch_user()`, `validate_payload()`, not `user()` or `validation()`.

**Type hints (enforced by mypy)**
- All public function signatures require type hints on parameters and return values.
- Use `from __future__ import annotations` for forward references.
- Prefer specific types over `Any`. `Any` requires a comment explaining why.
- Use `X | None` over `Optional[X]` (Python 3.10+).

**Docstrings (Google style, enforced by interrogate)**
```python
def fetch_user(user_id: int) -> User:
    """Fetch a user record by ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The User object matching the given ID.

    Raises:
        UserNotFoundError: If no user exists with that ID.
    """
```
- One-line docstrings for trivial functions: `"""Return the user's full name."""`
- `__init__`, `__dunder__`, private methods (`_name`) exempt from interrogate.

**Imports**
- Order: stdlib → third-party → local (isort enforces this automatically).
- Never use `from module import *` — pollutes namespace, breaks static analysis.
- Use standard aliases: `import numpy as np`, `import pandas as pd`.
- Conditional imports only for type-checking: inside `if TYPE_CHECKING:` block.

**Exception handling**
- Never use bare `except:` — catches `SystemExit` and `KeyboardInterrupt`.
- Use `except Exception:` as the widest catch if you must catch everything.
- Catch the most specific exception type possible.
- Always log or re-raise — don't silently swallow exceptions.
```python
# Bad
try:
    result = fetch(url)
except:
    pass

# Good
try:
    result = fetch(url)
except httpx.TimeoutException as e:
    logger.warning("Request timed out: %s", e)
    raise
```

**Data validation**
- Use `pydantic` (preferred) or `marshmallow` for external data (API payloads, config).
- Never trust unvalidated external input.

**Immutability preference**
- Prefer `tuple` over `list` for data that shouldn't change.
- Prefer `frozenset` over `set` for fixed sets.
- Makes intent clear and reduces accidental mutation bugs.

**Resources**
- Always use context managers: `with open(...) as f:` not manual `.close()`.
- Same for database connections, locks, temp files.

**Separation of concerns**
- API layer: only request/response handling, validation, routing.
- Service layer: business logic, orchestration.
- Data layer: database access, external APIs.
- Never put database queries in API handlers. Never put business logic in models.

**Strings**
- Use f-strings over `.format()` or `%` formatting.
- Use triple-quoted `"""` for all docstrings (never `'''`).

**Other**
- No `os.system()` — use `subprocess.run()` with explicit args and `check=True`.
- Always use `pathlib.Path` not string concatenation for file paths.
- Prefer `key in dict` over `dict.has_key(key)` (Python 2 pattern — never use).
- Use default iterators: `for key in dict:` not `for key in dict.keys():`.
- Prefer generators over list comprehensions when you don't need the full list.

---

### HTML (when needed)

> Placeholder — follow Google HTML/CSS Style Guide.
> Key rules: 2-space indent, lowercase element names, double quotes for attributes,
> omit `type` attribute on `<script>` and `<style>` tags, semantic elements over divs.

---

### JavaScript (when needed)

> Placeholder — follow Google JavaScript Style Guide via `eslint-config-google`.
> Key rules: `const`/`let` over `var`, arrow functions, template literals,
> `===` not `==`, no `eval()`, JSDoc for public APIs, 2-space indent.
> Setup: `npm install --save-dev eslint eslint-config-google`

---

### TypeScript (when needed)

> Placeholder — follow Google TypeScript Style Guide via `gts`.
> Key rules: explicit types on all public APIs, no `any` without comment,
> `interface` over `type` for object shapes, `import type` for type-only imports,
> no `namespace`, `camelCase` for vars/functions, `PascalCase` for types/classes.
> Setup: `npx gts init`

---

## Project Structure

```
_bmad/                   # BMAD runtime — DO NOT EDIT. npx owns this.
  core/                  # Agent logic (Analyst, PM, Architect, Scrum Master)
  bmm/                   # BMAD Method workflows (prd, architecture, epics-and-stories, etc.)
_bmad-output/            # BMAD writes planning docs here (prd.md, architecture.md)

.claude/
  agents/                # Our agents only — Superpowers + BMAD provide the rest
                         # security-reviewer.md — OWASP/CVE scan (read-only)
  commands/              # Our slash commands (implement, review, commit-push-pr)
  hooks/                 # Deterministic guardrails (lint, secrets, env guard, dangerous bash)
  skills/
    bmad-agent-analyst/  # ┐
    bmad-agent-pm/       # │ 7 lean BMAD skill stubs (trimmed by make bmad-trim-apply)
    bmad-agent-architect/# │ Each stubs into _bmad/ runtime
    bmad-prd/            # │ (replaces deprecated bmad-create-prd)
    bmad-architecture/   # │ (replaces deprecated bmad-create-architecture)
    bmad-create-epics-and-stories/ # │
    bmad-check-implementation-readiness/ # ┘
    graphify/            # Knowledge graph (71x token reduction)
    caveman/             # Token-efficient inter-agent comms (optional)
    setup-base/          # Project structure scanner
      scripts/
        setup_base.py          # Fresh project setup + BMAD output migration
    setup-migrate/  # Migration skill for existing projects
      scripts/
        setup_migrate.py       # Full audit + scaffold for existing projects
    rescan-docs/             # Reverse-engineer PRD + architecture + stories from existing code
  settings.json          # Hook wiring

stories/
  draft/                 # BMAD sprint-planning writes here
  ready/                 # Human moves stories here to unblock agents
  in-progress/           # Agent working
  review/                # PR open
  done/                  # Merged

config/
  models.json            # Model assignments + advisor config
scripts/
  configure.py           # Patches agents with model assignments
  trim_bmad_skills.py    # Trims BMAD stubs to lean 7
docs/
  prd.md                 # Template (BMAD overwrites with real content)
  architecture.md        # Template (BMAD overwrites with real content)
  coding-standards.md    # Full coding standards reference
  local-models.md        # Local model setup guide
```

---

## Workflow (Agentic Engineering Pipeline)

```
Requirements → Architecture → Stories → Implement → Review → Security → CI/CD → Deploy
    🖐              🖐             🖐                                                🖐
```

`🖐` = human gate (blocking). Everything else = automated agent.

### Layer 1: Planning — BMAD (installed by setup.sh)

BMAD owns the planning phase. Its commands and agents come from `npx bmad-method install`
and live in `_bmad/` (runtime) + `.claude/skills/bmad-*/` (stubs). Do not edit `_bmad/`.

| Command | BMAD Skill Stub | What it does |
|---------|----------------|--------------|
| `/plan` | `bmad-agent-analyst` | Stakeholder interviews → product brief |
| `/prd` | `bmad-agent-pm` + `bmad-prd` | PRD (create/update/validate) → `_bmad-output/prd.md` |
| `/architecture` | `bmad-agent-architect` + `bmad-architecture` | System design → `_bmad-output/architecture.md` |
| `/gate-check` | `bmad-check-implementation-readiness` | PRD ↔ architecture consistency |
| `/sprint-planning` | `bmad-create-epics-and-stories` | Break PRD into story files → `stories/` |

After `setup.sh`, only these 7 BMAD skill stubs remain (all others trimmed by `make bmad-trim-apply`).

### Layer 2: Implementation — Superpowers (installed globally via plugin)

Superpowers owns the implementation workflow. It installs to `~/.claude/` — not
per-project. Skills trigger automatically when Claude detects relevant context.

| Skill | Triggers when... |
|-------|-----------------|
| `brainstorming` | You describe something to build |
| `using-git-worktrees` | Design is approved — creates isolated branch |
| `writing-plans` | Ready to implement — breaks into 2–5 min tasks |
| `subagent-driven-development` | Plan exists — dispatches subagents per task |
| `requesting-code-review` | A task completes — unified single-pass task reviewer (v6) |
| `verification-before-completion` | Before any commit or PR |

Install once globally (this project assumes Superpowers **v6+**):
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```
Already installed? Update with `/plugin update superpowers@superpowers-marketplace`.
v6 keeps SDD scratch files in `.superpowers/` (gitignored).

### Layer 3: Security — Our agent (`.claude/agents/`)

`/security-scan` → `security-reviewer` agent — OWASP Top 10, secrets, CVEs.
Use on PRs touching auth, data access, or external integrations.
Our command `/review` triggers this explicitly when needed.

### Story file lifecycle

```
_bmad-output/ → stories/draft/ → stories/ready/ → stories/in-progress/ → stories/review/ → stories/done/
                  (BMAD writes)   🖐 human moves    (/dev-story)            (Stop hook)       (merged)
```

Use `/dev-story [id]` to pick up a story. With no id it grabs the
lowest-numbered file in `stories/ready/`. The command moves the file to
`in-progress/`, checks out `feat/story-{slug}`, and dispatches the
Superpowers `subagent-driven-development` skill. The `stop_story_lifecycle.py`
Stop hook moves the file to `review/` once a PR is open for the branch — no
manual `mv` required.

After `/sprint-planning` creates new stories, rebuild the knowledge graph:
```bash
graphify . --update    # fast — only re-processes changed files
```

This keeps Superpowers subagents from grepping raw files when they need project context.

---

---

## Git Strategy

- Branch naming: `feat/story-{id}-{slug}`, `fix/{slug}`, `chore/{slug}`
- Commit format: `type(scope): description` (conventional commits)
- One worktree per agent/story (git worktrees for isolation)
- Nothing touches `main` until human merges

---

## Security Rules

- Never commit secrets or API keys — `post_tool_secrets.py` hook blocks this
- Follow OWASP Top 10 patterns
- Auth: [define your pattern here]

### Environment variable conventions

| File | Committed? | Purpose |
|------|-----------|---------|
| `.env.template` | ✅ yes | Documents all variables — no real values |
| `.env` | ❌ never | Real values for local dev — gitignored |
| `.env.claude` | ❌ never | Generated by `make configure` — gitignored |

**Claude must never read `.env`** — the `pre_tool_env_guard.py` hook enforces this
across Read, Glob, LS, Grep, and Bash tool calls.

When you need to understand what environment variables exist: read `.env.template`.
When writing code that uses env vars: reference them by name via `os.environ` or
`pydantic BaseSettings`. Never read `.env` directly.

Setup for a new environment:
```bash
cp .env.template .env   # then fill in real values
```

---

## Review Checklist (every PR)

- [ ] `make check` passes (fmt + lint + test + mypy)
- [ ] Docstring coverage ≥ 80% (interrogate)
- [ ] No mypy errors (type hints on all public signatures)
- [ ] No secrets in diff
- [ ] Acceptance criteria from story file met
- [ ] Tests added for new behaviour
- [ ] No bare `except:` clauses
- [ ] External data validated via pydantic/marshmallow
- [ ] No `os.system()` — uses `subprocess.run()`
- [ ] File paths use `pathlib.Path`

---

## Agent Team

**BMAD agents** (from `npx bmad-method install` → `_bmad/` runtime, do not edit):

| Agent | Command | Phase |
|-------|---------|-------|
| Analyst | `/plan` | Product brief |
| PM | `/prd` | PRD generation |
| Architect | `/architecture` | System design |
| Scrum Master | `/sprint-planning` | Story breakdown → `stories/draft/` |

**Superpowers agents** (installed globally to `~/.claude/` via `/plugin install`, do not edit):

| Agent / Skill | Triggers | What it does |
|--------------|----------|--------------|
| `subagent-driven-development` | Automatically when implementing | TDD workflow — brainstorm → plan → test-first → implement → review |
| `requesting-code-review` | After each implementation task | Unified single-pass review: spec compliance + code quality (v6) |
| `brainstorming` | Before writing code | Refines requirements, explores alternatives |
| `writing-plans` | After design approved | Breaks work into 2–5 min tasks with exact file paths |
| `verification-before-completion` | Before any PR/commit | Runs tests, confirms output before claiming done |

Skills trigger **automatically** based on context — you do not invoke them manually.

**Our agent** (`.claude/agents/` — customise freely):

| Agent | Phase | Why we own it |
|-------|-------|--------------|
| `security-reviewer` | Security scan — read-only | Superpowers has no security-specific agent |

---

---

## Knowledge Graph (Graphify)

When `graphify-out/GRAPH_REPORT.md` exists, **check it before any broad codebase search**.
It provides a token-compressed map of the codebase (71x fewer tokens than grepping raw files).
Prefer `graphify query "<question>"` over multi-file Grep for context gathering.
Only fall back to grepping raw files if the graph doesn't answer your question.

To build/update: `graphify . --update`
To query: `graphify query "what connects X to Y?"`

---

## Token-Efficient Comms (Caveman)

Subagents use **caveman-style output** for all internal messages — status updates,
handoff notes, task completions passed to the orchestrator. Full prose is for
human-facing output only (PR descriptions, CLAUDE.md updates, reviews).

What caveman strips: articles, filler phrases, hedging. Code blocks are never touched.
Example: "The component re-renders because a new object ref is created on every render cycle"
→ "New obj ref each render. Inline object = new ref = re-render. Wrap in useMemo."

**Use caveman for:** inter-agent messages, status updates, reasoning steps not read by humans.
**Never use caveman for:** PR descriptions, commit messages, user-facing reviews, CLAUDE.md.

---

## Rules (add here when Claude makes a mistake)

<!-- Add rules here as you encounter them. Example format:
- Never use `os.system()` — use `subprocess.run()` with explicit args
- Always use `pathlib.Path` not string concatenation for paths
-->

- BMAD runtime scripts (`_bmad/scripts/*.py`) need Python ≥ 3.11 (`tomllib`).
  Run them via `uv run python`, never bare `python3` — the macOS system
  python3 is 3.9 and fails with `ModuleNotFoundError: tomllib`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
