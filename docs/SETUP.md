# Setup

One-time bootstrap and optional add-ons for this template. After your project
is up and running, you can ignore this file.

---

## Quick start

```bash
git clone <this-repo> my-project && cd my-project
bash setup.sh
```

`setup.sh` installs Python deps via `uv`, fetches the BMAD runtime via
`npx bmad-method install`, trims the BMAD skill set down to the lean 7,
and applies model assignments from `config/models.json`.

Then open Claude Code and run the planning pipeline:

```
/plan             # Analyst: stakeholder brief
/prd              # PM: PRD → _bmad-output/prd.md
/architecture     # Architect: system design → _bmad-output/architecture.md
                  # ← HUMAN GATE: review architecture
/gate-check       # Verify PRD ↔ architecture consistency
/sprint-planning  # Scrum Master: stories → stories/draft/
                  # ← HUMAN GATE: move stories to stories/ready/
/dev-story [id]   # Implement a story end-to-end (omit id to pick lowest-numbered)
```

---

## Project structure (post-setup)

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
│   ├── commands/                        # Slash commands
│   │   ├── plan.md                      # /plan → bmad-agent-analyst
│   │   ├── prd.md                       # /prd → bmad-agent-pm + bmad-create-prd
│   │   ├── architecture.md              # /architecture → bmad-agent-architect + bmad-create-architecture
│   │   ├── gate-check.md               # /gate-check → bmad-check-implementation-readiness
│   │   ├── sprint-planning.md           # /sprint-planning → bmad-create-epics-and-stories
│   │   ├── dev-story.md                 # /dev-story [id] — full story lifecycle
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

## Hooks (deterministic guardrails)

Run on every tool call. No LLM judgment — pure code.

| Hook | Trigger | Action |
|------|---------|--------|
| `post_tool_lint.py` | Write/Edit | Auto-lint after file changes |
| `post_tool_secrets.py` | Write/Edit | Block committed credentials |
| `pre_tool_dangerous.py` | Bash | Block rm -rf, force push, etc. |
| `pre_tool_env_guard.py` | Read/Glob/LS/Grep/Bash | Block Claude reading `.env` |

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

**Superpowers** (global plugin — installs to `~/.claude/`, not per-project):
```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

---

## Staying updatable

Upstream framework updates do not touch your customisations:

- **BMAD** (`npx bmad-method install`) — installs into `.claude/skills/`. Update with the same command.
- **Superpowers** (`/plugin install superpowers@superpowers-marketplace`) — separate from your agent definitions.
- **Your customisations** live in `.claude/agents/`, `.claude/commands/`, `.claude/hooks/`, and `CLAUDE.md` — none are touched by upstream updates.
- **Graphify** (`pip install graphifyy --upgrade`) — your `.graphifyignore` and CLAUDE.md hook survive upgrades.
