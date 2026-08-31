# CLAUDE.md

Project brain — loaded into every session, so keep it short. Add a rule under
**Rules** whenever an agent gets something wrong.

---

## Build & Dev Commands

```bash
make install    # install all deps (uv sync)
make fmt        # format: black + isort + autoflake
make lint       # check: black, isort, interrogate, mypy
make test       # pytest
make check      # fmt + lint + test — run before every commit
make clean      # remove __pycache__, .pytest_cache, dist

make configure                 # apply config/models.json to all agents
make configure PROFILE=<name>  # switch profile (list: make configure-list)
make configure-show            # print current model assignments

make manifest   # regenerate template-manifest.json after editing any
                # template-owned file, before bumping TEMPLATE_VERSION
```

Healthy `make check` ends `All done! ✨ 🍰 ✨` / `Success: no issues found` /
`N passed`. Anything else is a failure to fix, not to work around — never bypass
it. After editing `config/models.json`, run `make configure`.

---

## Tech Stack

Python via `uv` + `pyproject.toml`. Formatting, import order, docstring coverage,
and strict typing are enforced by `make check` — don't hand-audit what it covers.
Use the `python-standards` skill for what a linter can't (full reference:
`docs/harness/coding-standards.md`).

---

## Project Structure

| Path | What lives here |
|---|---|
| `.claude/` | Agents, commands, hooks, skills, `settings.json` |
| `openspec/specs/` | **Canonical**: what the system does today. Changes only at archive |
| `openspec/changes/` | Work in flight, one folder per change |
| `docs/` | `product.md`, `architecture.md` (shape only), `decisions/` (ADRs) |
| `docs/harness/` | Template-owned docs: setup, coding standards |
| `config/models.json` | Model assignments per tier |
| `scripts/` | `configure.py` (shipped); manifest + migration tools (starter-only) |
| `src/` | Your code. Each feature dir carries its own `CLAUDE.md` |

Feature `CLAUDE.md` files hold stable facts only — purpose, entry points,
invariants, gotchas; ~30 lines max. Never implementation status (a change's
`tasks.md` is that record), and never `@import` them here: imports load eagerly,
defeating lazy loading.

---

## Change Lifecycle

`/crystallize` → `/dev-change <slug> <group>` → PR → `/archive-change <slug>`.
Four human gates: intent, spec+tasks, PR merge, archived spec diff.

- One `## N` task group in `tasks.md` = one branch = one worktree = one PR.
  `/dev-change` claims a group by winning the race to create
  `feat/<slug>-g<N>`; **branch existence is the mutex**.
- `tasks.md` is the durable plan of record, not scaffolding. If implementation
  departs from it, update it in the same commit — PR review checks the diff
  against it.
- After every group merges, `/archive-change <slug>` merges the delta specs into
  `openspec/specs/` and archives the change folder.

---

## Git Strategy

- Branches: `feat/{change-slug}-g{N}`, `fix/{slug}`, `chore/{slug}`
- Commits: `type(scope): description`. Nothing touches `main` until a human merges.

---

## Environment Variables

**Never read `.env`** — the `pre_tool_env_guard.py` hook blocks it across Read,
Glob, LS, Grep, and Bash. Read `.env.template` instead; reference variables by name
via `os.environ` or pydantic `BaseSettings`.

---

## PR Checklist

Beyond what hooks and `make check` already enforce:

- [ ] Every task in the group is ticked in the change's `tasks.md`
- [ ] Tests added for new behaviour
- [ ] No bare `except:` clauses
- [ ] External data validated via pydantic/marshmallow

---

## Claude Code specifics

- Hooks are wired in `.claude/settings.json` (env guard, dangerous-bash, secrets,
  lint, feature-CLAUDE.md reminder). Never bypass them.
- Superpowers v6+ is installed globally and triggers automatically.
- `graphify` is opt-in: it offers itself for broad architecture questions, but is
  never a mandatory first step.

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

---

## Rules

- When a story leaves a real ambiguity unresolved — architectural direction,
  contradictory requirements, a non-obvious security tradeoff — stop and ask the
  user. Do not guess, and do not widen scope to route around it.
