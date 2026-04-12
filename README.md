# Agentic Base

A fork-ready project template for structured AI-driven software delivery.

Built on the [Agentic Engineering guide](https://github.com/your-link) —
BMAD + Superpowers + Claude Code Primitives — with Python tooling,
deterministic guardrails, and optional knowledge graph support.

---

## Philosophy

> The bottleneck isn't model intelligence. It's the absence of engineering discipline.
> — Agentic Engineering guide

This template solves the four core problems with naive AI-assisted development:

| Problem | Solution |
|---------|----------|
| No structure (AI jumps straight to code) | BMAD planning pipeline with human gates |
| Context loss (each session starts fresh) | CLAUDE.md + story files + graphify graph |
| Inconsistent output (same prompt, different results) | Deterministic hooks + Superpowers TDD |
| Review bottleneck (AI writes faster than humans review) | Automated hooks + agent reviewers |

---

## Quick start

```bash
# 1. Clone and bootstrap
git clone <this-repo> my-project && cd my-project
bash setup.sh

# 2. Open Claude Code and start the planning pipeline
# In Claude Code terminal:
/plan         # Analyst: stakeholder brief
/prd          # PM: product requirements → docs/prd.md
/architecture # Architect: system design → docs/architecture.md
              # ← HUMAN GATE: review and approve architecture
/sprint-planning  # Scrum Master: break into story files → stories/draft/
              # ← HUMAN GATE: review and move stories to stories/ready/

# 3. Implement
/implement story-001   # Developer agent (TDD, worktree-isolated)

# 4. Review and ship
/review                # Code reviewer agent
/commit-push-pr        # Stage, commit, push, open PR
              # ← HUMAN GATE: approve merge
```

---

## Structure

After `bash setup.sh` completes, the project looks like this:

```
.
├── _bmad/                               # BMAD runtime — DO NOT EDIT (npx owns this)
│   ├── core/                            # Agent logic: Analyst, PM, Architect, SM
│   └── bmm/                             # Workflows: create-prd, create-architecture, etc.
├── _bmad-output/                        # BMAD writes planning docs here
│
├── CLAUDE.md                            # Project brain — read every session
├── Makefile                             # Single entry point for all commands
├── pyproject.toml                       # Python deps + tool config
├── setup.sh                             # One-command bootstrap
├── .env.template                        # Committed — documents all env vars, no real values
├── .gitignore / .graphifyignore
│
├── .claude/
│   ├── settings.json                    # Hook wiring
│   ├── agents/                          # Our implementation agents
│   │   ├── developer.md                 # TDD (Sonnet + Opus advisor)
│   │   ├── code-reviewer.md             # PR review, read-only (Opus)
│   │   └── security-reviewer.md         # OWASP/CVE scan, read-only (Opus)
│   ├── commands/                        # Our implementation commands
│   │   ├── implement.md                 # /implement story-NNN
│   │   ├── review.md                    # /review
│   │   └── commit-push-pr.md            # /commit-push-pr
│   ├── hooks/
│   │   ├── pre_tool_dangerous.py        # Block rm -rf, force push
│   │   ├── pre_tool_env_guard.py        # Block Claude reading .env
│   │   ├── post_tool_secrets.py         # Block committed credentials
│   │   └── post_tool_lint.py            # Auto-lint after file writes
│   └── skills/
│       ├── bmad-agent-analyst/          # ┐
│       ├── bmad-agent-pm/               # │ 7 lean BMAD stubs
│       ├── bmad-agent-architect/        # │ (after make bmad-trim-apply)
│       ├── bmad-create-prd/             # │
│       ├── bmad-create-architecture/    # │
│       ├── bmad-create-epics-and-stories/ # │
│       ├── bmad-check-implementation-readiness/ # ┘
│       ├── graphify/SKILL.md            # Optional: knowledge graph
│       └── caveman/SKILL.md             # Optional: token-efficient comms
│
├── stories/
│   ├── STORY_TEMPLATE.md
│   ├── draft/        ← BMAD /sprint-planning writes here
│   ├── ready/        ← human moves stories here to unblock agents
│   ├── in-progress/  ← agent working (git worktree)
│   ├── review/       ← PR open
│   └── done/         ← merged
│
├── config/
│   └── models.json                      # Model assignments + advisor config
├── scripts/
│   ├── configure.py                     # Patches agents with model assignments
│   └── trim_bmad_skills.py              # Trims BMAD stubs to lean 7
└── docs/
    ├── prd.md / architecture.md         # Templates (BMAD overwrites these)
    ├── coding-standards.md
    └── local-models.md
```

---

## Pipeline (from the Agentic Engineering guide)

```
Requirements → Architecture → Stories → Implement → Review → Security → CI/CD → Deploy
    🖐              🖐             🖐                                                🖐
```

`🖐` = human gate (blocking). Everything else = automated agent.

---

## Python tooling

All configured in `pyproject.toml`, run via `make`:

| Tool | Purpose | Config |
|------|---------|--------|
| `black` | Formatter | line-length = 88 |
| `isort` | Import sorter | profile = "black" |
| `autoflake` | Remove unused imports | via Makefile |
| `interrogate` | Docstring coverage | fail-under = 80% |
| `pytest` | Test runner | coverage ≥ 80% |
| `uv` | Package manager | pyproject.toml |

```bash
make fmt    # fix: black + isort + autoflake (mutating)
make lint   # check: black + isort + interrogate (non-mutating)
make test   # pytest with coverage
make check  # fmt + lint + test — run before every commit
```

---

## Hooks (deterministic guardrails)

Run on every tool call. No LLM judgment — pure code.

| Hook | Trigger | Action |
|------|---------|--------|
| `post_tool_lint.py` | Write/Edit | Auto-lint after file changes |
| `post_tool_secrets.py` | Write/Edit | Block committed credentials |
| `pre_tool_dangerous.py` | Bash | Block rm -rf, force push, etc. |

---

## Optional skills

**Graphify** (recommended for large codebases):
```bash
pip install graphifyy && graphify claude install
graphify .   # builds knowledge graph
```
Gives agents a 71x token-compressed map of the codebase to query
instead of grepping raw files. Hooks tell Claude to consult it automatically.

**Caveman** (for token-efficient inter-agent comms):
```bash
claude install-skill JuliusBrussee/caveman
```
Cuts ~75% of output tokens on internal agent messages. Use for
agent-to-agent handoffs, not human-facing output.

---

## Staying updatable

This template is designed so upstream framework updates don't break your customisations:

- **BMAD** (`npx bmad-method install`) — installs into `.claude/skills/`. Update with the same command.
- **Superpowers** (`/plugin install superpowers@superpowers-marketplace`) — separate from your agent definitions.
- **Your customisations** live in `.claude/agents/`, `.claude/commands/`, `.claude/hooks/`, and `CLAUDE.md` — none of these are touched by upstream updates.
- **Graphify** (`pip install graphifyy --upgrade`) — your `.graphifyignore` and CLAUDE.md hook survive upgrades.
