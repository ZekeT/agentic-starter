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
| planning | `claude-opus-4-6` |
| review | `claude-opus-4-6` |
| implement | `claude-sonnet-4-6` |
| fast | `claude-haiku-4-5-20251001` |

Advisor strategy: **enabled** — `claude-opus-4-6` advises executor agents (max 3 uses per request).
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
.claude/
  agents/       # specialized subagents (analyst, pm, architect, dev, reviewer, etc.)
  commands/     # slash commands for inner-loop workflows
  hooks/        # pre/post tool hooks (lint, secrets, block dangerous)
  skills/       # BMAD, Superpowers, optional skills (graphify, caveman)
stories/
  draft/        # not ready — being written
  ready/        # human-confirmed, agent can pick up
  in-progress/  # agent currently working
  review/       # PR open, awaiting human
  done/         # merged
docs/
  prd.md        # product requirements (generated by /prd)
  architecture.md  # system design (generated by /architecture)
graphify-out/   # knowledge graph output (run: graphify claude install)
  GRAPH_REPORT.md  # read this before answering architecture questions
  graph.json
```

---

## Workflow (Agentic Engineering Pipeline)

```
Requirements → Architecture → Stories → Implement → Review → Security → CI/CD → Deploy
    🖐            🖐             🖐                                                  🖐
```

`🖐` = human gate (blocking). Everything else = automated agent.

**Planning phase** (BMAD — human gates after each step):
1. `/plan` — Analyst: stakeholder brief
2. `/prd` — PM: structured PRD with acceptance criteria → `docs/prd.md`
3. `/architecture` — Architect: system design → `docs/architecture.md`
4. `/gate-check` — Validator: PRD ↔ architecture consistency
5. `/sprint-planning` — Scrum Master: break into story files → `stories/draft/`

**Implementation phase** (Superpowers TDD — no human gate):
- Stories move: `draft/` → `ready/` (human confirms) → `in-progress/` (agent) → `review/` → `done/`
- TDD order enforced: brainstorm → plan subtasks → write failing tests → implement → verify
- Code written before tests is deleted. This is enforced, not suggested.

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

| Agent | Phase | Notes |
|-------|-------|-------|
| Analyst | Planning | Stakeholder interviews, product brief |
| PM | Planning | PRD with acceptance criteria |
| Architect | Planning | System design, API contracts |
| Scrum Master | Sprint | Break PRD into story files |
| Developer | Implementation | TDD via Superpowers |
| Code Reviewer | Review | Read-only, checks conventions + bugs |
| Security Reviewer | Security | OWASP, secrets, CVEs |
| QA Engineer | Validation | Runs acceptance criteria |

Route planning/review tasks → Opus. Implementation subtasks → Sonnet (cost efficiency).

---

## Knowledge Graph (Graphify)

When `graphify-out/GRAPH_REPORT.md` exists, **read it before answering architecture questions**.
It provides a token-compressed map of the codebase (71x fewer tokens than grepping raw files).

To build/update: `graphify . --update`
To query: `graphify query "what connects X to Y?"`

---

## Rules (add here when Claude makes a mistake)

<!-- Add rules here as you encounter them. Example format:
- Never use `os.system()` — use `subprocess.run()` with explicit args
- Always use `pathlib.Path` not string concatenation for paths
-->
