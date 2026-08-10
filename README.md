# Agentic Base

Fork-ready template for structured AI-driven software delivery.
Superpowers + Claude Code Primitives, with Python tooling and deterministic guardrails.

> The bottleneck isn't model intelligence. It's the absence of engineering discipline.

For one-time bootstrap, project structure, hooks, and optional skills, see [`docs/SETUP.md`](docs/SETUP.md).

---

## Pipeline

```
Requirements → Architecture → Stories → Implement → Review → Security → CI/CD → Deploy
    🖐              🖐             🖐                                                🖐
```

`🖐` = human gate. Everything else is an automated agent.

| Phase | Command | Output |
|-------|---------|--------|
| Plan | Superpowers `brainstorming` conversation | `docs/prd.md` |
| Architecture | Superpowers `writing-plans` conversation | `docs/architecture.md` |
| Stories | `/sprint-planning` | `stories/draft/` |
| Implement | `/implement story-NNN` | code on a worktree branch |
| Review | `/review` | code-reviewer pass |
| Ship | `/commit-push-pr` | PR opened |

---

## Story lifecycle

```
stories/draft/ → stories/ready/ → stories/in-progress/ → stories/review/ → stories/done/
(/sprint-planning)  🖐 human        (agent + worktree)        (PR open)        (merged)
```

After `/sprint-planning` adds new stories: `graphify . --update` to refresh the codebase graph.

---

## Daily commands

```bash
make check   # fmt + lint + test — run before every commit
make fmt     # black + isort + autoflake
make lint    # black --check, isort --check, interrogate, mypy
make test    # pytest
```

Model assignments live in `config/models.json`. After editing, run `make configure`.

Coding standards: [`docs/coding-standards.md`](docs/coding-standards.md).
Project rules and active model config: [`CLAUDE.md`](CLAUDE.md).
