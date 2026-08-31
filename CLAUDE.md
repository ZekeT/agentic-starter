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
and strict typing are all enforced by `make check` — don't hand-audit what it
covers. Use the `python-standards` skill for what a linter can't catch (reference:
`docs/harness/coding-standards.md`).

---

## Project Structure

| Path | What lives here |
|---|---|
| `.claude/` | Agents, commands, hooks, skills, `settings.json` |
| `stories/` | Lifecycle folders: `draft → ready → in-progress → review → done` |
| `docs/` | Project truth — PRD, architecture |
| `docs/harness/` | Template-owned docs: setup, coding standards |
| `config/models.json` | Model assignments per tier |
| `scripts/` | `configure.py` (shipped); manifest + migration tools (starter-only) |
| `src/` | Your code. Each feature dir carries its own `CLAUDE.md` |

Feature `CLAUDE.md` files hold stable facts only — purpose, entry points,
invariants, gotchas; ~30 lines max. Never implementation status (`stories/` is that
record), and never `@import` them here: imports load eagerly, defeating lazy loading.

---

## Story Lifecycle

`draft → ready → in-progress → review → done`

- `/sprint-planning` writes to `stories/draft/`; a human moves stories to
  `stories/ready/` — that is the gate.
- `/dev-story [id]` claims the lowest unclaimed story in `ready/` via
  `git worktree add ../wt-story-{slug} -b feat/story-{slug}`. **Branch existence is
  the mutex** — the add fails if another session claimed that slug. Inside the
  worktree it `git mv`s the story to `in-progress/` as the branch's first commit,
  then dispatches Superpowers `subagent-driven-development`.
- On completion `/dev-story` runs `/commit-push-pr`, then `git mv`s the story to
  `review/`. After merge, the `stop_story_lifecycle.py` Stop hook moves it to
  `done/` and removes the worktree and branch; `/dev-story` sweeps merged
  worktrees on its next run as a fallback.

---

## Git Strategy

- Branches: `feat/story-{id}-{slug}`, `fix/{slug}`, `chore/{slug}`
- Commits: `type(scope): description` (conventional commits)
- One worktree per story. Nothing touches `main` until a human merges.

---

## Environment Variables

**Never read `.env`** — the `pre_tool_env_guard.py` hook blocks it across Read,
Glob, LS, Grep, and Bash. Read `.env.template` instead, and reference variables by
name via `os.environ` or pydantic `BaseSettings`.

---

## PR Checklist

Beyond what hooks and `make check` already enforce:

- [ ] Acceptance criteria from the story file are met
- [ ] Tests added for new behaviour
- [ ] No bare `except:` clauses
- [ ] External data validated via pydantic/marshmallow

---

## Claude Code specifics

- Hooks are wired in `.claude/settings.json` (env guard, dangerous-bash, secrets,
  lint, story lifecycle). Never bypass them.
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
