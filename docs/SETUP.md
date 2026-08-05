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

> BMAD's runtime scripts require **Python ≥ 3.11** (`tomllib`). The project
> venv (via `uv`) satisfies this; the macOS system python3 (3.9) does not.
> Always run BMAD scripts through `uv run python`.

Then install Superpowers **once per machine** inside a Claude Code session
(this template assumes Superpowers **v6+**):

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

Already installed on this machine? Update instead:

```
/plugin update superpowers@superpowers-marketplace
```

This installs implementation skills (TDD, subagent dispatch, code review) globally
to `~/.claude/`. Required for `/dev-story` to use the full agentic TDD workflow.
Superpowers v6 replaced the two-stage review with a unified single-pass task
reviewer and keeps SDD scratch files in `.superpowers/` (gitignored here).

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
│   ├── agents/                          # Project-specific agents only
│   │   └── security-reviewer.md         # OWASP/CVE scan, read-only (Opus)
│   │                                    # developer + code-reviewer live in Superpowers
│   │                                    # (~/.claude/) — not committed here
│   ├── commands/                        # Slash commands
│   │   ├── plan.md                      # /plan → bmad-agent-analyst
│   │   ├── prd.md                       # /prd → bmad-agent-pm + bmad-prd
│   │   ├── architecture.md              # /architecture → bmad-agent-architect + bmad-architecture
│   │   ├── gate-check.md               # /gate-check → bmad-check-implementation-readiness
│   │   ├── sprint-planning.md           # /sprint-planning → bmad-create-epics-and-stories
│   │   ├── dev-story.md                 # /dev-story [id] — full story lifecycle (canonical)
│   │   ├── implement.md                 # /implement story-NNN — thin alias for dev-story
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
│       ├── bmad-prd/                    # │ (replaces deprecated bmad-create-prd)
│       ├── bmad-architecture/           # │ (replaces deprecated bmad-create-architecture)
│       ├── bmad-create-epics-and-stories/ # │
│       ├── bmad-check-implementation-readiness/ # ┘
│       ├── graphify/SKILL.md            # Optional: knowledge graph
│       ├── caveman/SKILL.md             # Optional: token-efficient comms
│       ├── setup-base/                  # Scan project setup health
│       ├── setup-migrate/               # Migrate existing projects to this framework
│       ├── setup-update/                # Update a copied project to the latest template
│       └── rescan-docs/                 # Reverse-engineer PRD + architecture + stories from code
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

---

## Migrating an existing project

To adopt this framework on an existing codebase (instead of starting fresh),
run the migration script from wherever you cloned this repo:

```bash
python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/your/project --dry
python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/your/project
```

This copies hooks, commands (including the BMAD planning triggers), the
security agent, config, scripts, docs, and our skills (`rescan-docs`,
`setup-base`, `setup-migrate`, `setup-update`, `graphify`, `caveman`) into
your project without overwriting anything that already exists. It does not
touch BMAD (`npx bmad-method install`) — run that separately, see Step 2 below.

Then open Claude Code in your project and generate planning docs from the existing code:

```
/rescan-docs    # Analyses codebase → generates PRD + architecture + story stubs in _bmad-output/
/gate-check     # Validates PRD ↔ architecture consistency
```

Move stories from `stories/draft/` to `stories/ready/` when you're ready to implement.

---

## Staying updatable

Upstream framework updates do not touch your customisations:

- **BMAD** (`npx bmad-method install`) — installs into `.claude/skills/`. Update with
  the same command, then re-run `make bmad-trim-apply` to restore the lean 7.
  BMAD 6.10 consolidated `bmad-create-prd`/`bmad-create-architecture` into
  `bmad-prd`/`bmad-architecture` — this template already uses the new names.
- **Superpowers** (`/plugin update superpowers@superpowers-marketplace`) — separate from your agent definitions.
- **The rest of the template** (hooks, commands, docs, scripts, our skills) —
  use the **`setup-update`** skill (or `python
  /path/to/agentic-starter/.claude/skills/setup-update/scripts/setup_update.py
  /path/to/your-project --dry`). It hashes every template-owned file against
  `template-manifest.json`: files you never touched are auto-updated, files
  you customised are flagged for a guided merge instead of being overwritten.
- **Your customisations** live in `.claude/agents/`, `.claude/commands/`, `.claude/hooks/`, and `CLAUDE.md` — protected by the same mechanism.
- **Graphify** (`pip install graphifyy --upgrade`) — your `.graphifyignore` and CLAUDE.md hook survive upgrades.

Every project created from this template records the template version it
started from in `.claude/template-version.json` (or `.claude/migration-report.json`
for older projects) — that's what `setup-update` diffs against.
