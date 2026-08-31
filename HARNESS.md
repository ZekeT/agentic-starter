# Agentic Base

Fork-ready template for structured AI-driven software delivery.
Superpowers + Claude Code Primitives, with Python tooling and deterministic guardrails.

> The bottleneck isn't model intelligence. It's the absence of engineering discipline.

For one-time bootstrap, project structure, hooks, and optional skills, see [`docs/harness/setup.md`](docs/harness/setup.md).

---

## Pipeline

```
exploration → intent → spec → tasks → implement → review → archive
                🖐       🖐              🖐 (PR merge)      🖐
```

`🖐` = human gate. Everything else is an automated agent.

| Stage | Command | Output | Gate |
|---|---|---|---|
| Explore | conversation, or `/opsx:explore` | understanding | — |
| Intent | `/crystallize "<idea>"` | `openspec/changes/<slug>/intent.md` | 🖐 accept the intent |
| Spec | `/crystallize` continues | `proposal.md` + `specs/` + `design.md` + `tasks.md` | 🖐 accept the spec |
| Implement | `/dev-change <slug> <group>` | code + tests on a worktree branch | — |
| Review | `/review` | compliance against the delta specs | — |
| Ship | `/commit-push-pr` | PR opened | 🖐 merge |
| Archive | `/archive-change <slug>` | deltas merged into `openspec/specs/` | 🖐 review the spec diff |

---

## Where truth lives

| Question | Read |
|---|---|
| What does the system do **today**? | `openspec/specs/` — start with `openspec list --specs` |
| What is changing **right now**? | `openspec/changes/<slug>/` |
| **Why** was it built this way? | `docs/decisions/` |
| What **shape** is the system? | `docs/architecture.md` |
| What is this product **for**? | `docs/product.md` |

`openspec/specs/` is the only thing that changes automatically, and only at
archive time. That is what stops it drifting from the code the way a PRD does.

---

## The unit of work

One `## N` task group in a change's `tasks.md` = one branch = one worktree = one
PR. `/dev-change <slug> <group>` claims a group by creating `feat/<slug>-g<N>`;
branch existence is the mutex, so two sessions cannot claim the same group.

Walkthrough:

```
/crystallize "add rate limiting"   → review intent → review spec + tasks
/dev-change add-rate-limiting 1    → PR → merge
/dev-change add-rate-limiting 2    → PR → merge
/archive-change add-rate-limiting  → review the spec diff
```

Optional: `graphify . --update` refreshes the codebase knowledge graph — worth it
for broad architecture questions spanning many files, not required otherwise
(see the `graphify` skill).

---

## Daily commands

```bash
make check   # fmt + lint + test — run before every commit
make fmt     # black + isort + autoflake
make lint    # black --check, isort --check, interrogate, mypy
make test    # pytest
```

Model assignments live in `config/models.json`. After editing, run `make configure`.

Project facts and conventions: [`CLAUDE.md`](CLAUDE.md).
Active model config: [`CLAUDE.md`](CLAUDE.md).
Python style guide: `python-standards` skill (full reference: [`docs/harness/coding-standards.md`](docs/harness/coding-standards.md)).
