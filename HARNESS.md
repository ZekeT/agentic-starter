# Agentic Base

Fork-ready template for structured AI-driven software delivery.
Superpowers + Claude Code Primitives, with Python tooling and deterministic guardrails.

> The bottleneck isn't model intelligence. It's the absence of engineering discipline.

For one-time bootstrap, project structure, hooks, and optional skills, see [`docs/harness/setup.md`](docs/harness/setup.md).

---

## Pipeline

```
Requirements → Architecture → Stories → Implement → Review → Security → CI/CD → Deploy
    🖐              🖐             🖐                                                🖐
```

`🖐` = human gate. Everything else is an automated agent.

| Phase | Command | Output |
|-------|---------|--------|
| Plan | `/plan` Superpowers `brainstorming` conversation | `docs/prd.md` |
| Architecture | `/plan` Superpowers `writing-plans` conversation | `docs/architecture.md` |
| Stories | `/sprint-planning` | `stories/draft/` |
| Implement | `/dev-story NNN` | code on a worktree branch |
| Review | `/review` | code-reviewer pass |
| Ship | `/commit-push-pr` | PR opened |

---

## Story lifecycle

```
stories/draft/ → stories/ready/ → stories/in-progress/ → stories/review/ → stories/done/
(/sprint-planning)  🖐 human        (agent + worktree)        (PR open)        (merged)
```

Optional: after `/sprint-planning` adds new stories, `graphify . --update` refreshes
the codebase knowledge graph — worth it for broad architecture questions spanning
many files, not required otherwise (see the `graphify` skill).

E.g Walkthrough:
```
/plan → review docs → /sprint-planning → review stories, git mv approved ones to ready/ → /dev-story → review PR → merge.
```
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
