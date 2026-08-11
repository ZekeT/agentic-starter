# AGENTS.md — Project Brain

> Cross-tool source of truth: build commands, conventions, and project facts that
> apply no matter which agent harness is driving. Claude Code loads this via the
> `@AGENTS.md` import at the top of `CLAUDE.md`; other tools read it directly.
> Keep this short and high-signal. Add a rule under **Rules** every time an agent
> does something wrong.

---

## Build & Dev Commands

```bash
make install          # install all deps (uv sync)
make fmt              # format: black + isort + autoflake
make lint              # check: black --check, isort --check, interrogate, mypy
make test              # pytest
make check             # fmt + lint + test (run before every commit)
make clean             # remove __pycache__, .pytest_cache, dist

make configure                       # apply config/models.json to all agents
make configure PROFILE=ollama-qwen   # switch to a named profile
make configure-show                  # print current model assignments
make configure-list                  # list available profiles

make manifest                        # regenerate template-manifest.json (after
                                      # editing any template-owned file, before
                                      # bumping TEMPLATE_VERSION — powers setup-update)
```

> Always run `make check` before committing. Never bypass it.
> After editing `config/models.json`, run `make configure`.

---

## Tech Stack

- **Python**: managed via `uv` + `pyproject.toml`
- **Formatter**: `black` (line length 88)
- **Import sorter**: `isort` (black-compatible profile)
- **Unused import cleaner**: `autoflake`
- **Docstring coverage**: `interrogate` (min 80%)
- **Type checker**: `mypy` (strict mode)
- **Test runner**: `pytest`

Writing or reviewing Python? Use the `python-standards` skill for the conventions
a linter doesn't already enforce. Full reasoning/reference → `docs/coding-standards.md`.

---

## Project Structure

```
.claude/
  agents/                # security-reviewer.md — OWASP/CVE scan (read-only)
  commands/               # commit-push-pr, dev-story, implement, review, sprint-planning
  hooks/                  # Deterministic guardrails (lint, secrets, env guard, dangerous bash,
                          # story lifecycle, feature CLAUDE.md reminder)
  skills/
    graphify/             # Knowledge graph — opt-in, not enforced (see skill for triggers)
    python-standards/      # Python conventions not already caught by linters
    rescan-docs/           # Reverse-engineer PRD + architecture + stories from existing code
    setup-base/            # Project structure scanner
    setup-migrate/          # Migration skill for existing projects
    setup-update/           # Update a copied project to the latest template
  settings.json           # Hook wiring

stories/
  STORY_TEMPLATE.md      # Copy to draft/ when writing a new story
  draft/                  # /sprint-planning writes here
  ready/                  # Human moves stories here to unblock agents
  in-progress/            # Agent working
  review/                 # PR open
  done/                   # Merged

config/
  models.json             # Model assignments + advisor config
scripts/
  configure.py             # Patches CLAUDE.md's "## Active Model Config" section
docs/
  prd.md                   # Written during planning
  architecture.md          # Written during planning
  coding-standards.md      # Full Python/HTML/JS/TS reference
  local-models.md          # Local model setup guide
  SETUP.md                 # End-to-end setup walkthrough
```

Each feature directory under `src/` carries its own `CLAUDE.md` describing
stable facts only: purpose, key entry points, invariants, gotchas — max
~30 lines. Never implementation status (`stories/` is the record of what's
in flight/done). The root file links features with one-line pointers; never
`@import` feature files from the root (imports load eagerly and defeat lazy
loading).

---

## Story Lifecycle

```
draft → ready → in-progress → review → done
```

- `/sprint-planning` writes new stories to `stories/draft/`.
- A human moves a story to `stories/ready/` to unblock agents.
- `/dev-story [id]` (no id: lowest-numbered unclaimed file in `stories/ready/`)
  claims a story by creating its worktree: `git worktree add
  ../wt-story-{slug} -b feat/story-{slug}`. Branch existence is the mutex —
  the `git worktree add` fails if another session already claimed that slug,
  so this is what makes two sessions unable to pick the same story. The
  session then enters the worktree and, inside it, `git mv`s the story to
  `stories/in-progress/` as the branch's first commit, before dispatching
  Superpowers `subagent-driven-development`.
- On completion, `/dev-story` runs `/commit-push-pr` to open the PR, then
  `git mv`s the story file to `stories/review/` — still inside the worktree.
- After merge, the `stop_story_lifecycle.py` Stop hook moves the file to
  `stories/done/` and removes the worktree and its branch (releasing the
  mutex) — no manual `mv` or cleanup required at that point. `/dev-story`
  also sweeps merged worktrees/branches on its next invocation as a
  fallback, since a merge can happen with no session open to catch the Stop
  event.

---

## Git Strategy

- Branch naming: `feat/story-{id}-{slug}`, `fix/{slug}`, `chore/{slug}`
- Commit format: `type(scope): description` (conventional commits)
- One worktree per agent/story (git worktrees for isolation)
- Nothing touches `main` until human merges

---

## Environment Variable Conventions

| File | Committed? | Purpose |
|------|-----------|---------|
| `.env.template` | ✅ yes | Documents all variables — no real values |
| `.env` | ❌ never | Real values for local dev — gitignored |
| `.env.claude` | ❌ never | Generated by `make configure` — gitignored |

**Agents must never read `.env`** — the `pre_tool_env_guard.py` hook enforces this
across Read, Glob, LS, Grep, and Bash tool calls.

When you need to know what environment variables exist: read `.env.template`.
When writing code that uses env vars: reference them by name via `os.environ` or
`pydantic BaseSettings`. Never read `.env` directly.

Setup for a new environment:
```bash
cp .env.template .env   # then fill in real values
```

---

## PR Checklist

Items not already caught by a hook or `make check` (which covers formatting,
linting, docstring coverage, mypy, tests, and secrets-in-diff):

- [ ] Acceptance criteria from the story file are met
- [ ] Tests added for new behaviour
- [ ] No bare `except:` clauses
- [ ] External data validated via pydantic/marshmallow

---

## Rules (add here when an agent makes a mistake)

For codebase knowledge-graph navigation, see the `graphify` skill (opt-in — offers
itself for broad architecture questions, not a mandatory first step).
