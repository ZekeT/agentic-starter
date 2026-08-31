# Setup

One-time bootstrap and optional add-ons for this template. After your project
is up and running, you can ignore this file.

---

## Quick start

```bash
git clone <this-repo> my-project && cd my-project
bash harness_setup.sh
```

`harness_setup.sh` installs Python deps via `uv`, applies model assignments from
`config/models.json`, bootstraps `.env`, sets up graphify, and checks for
OpenSpec.

### OpenSpec (required for the change loop)

OpenSpec owns the document lifecycle: `openspec/specs/` is the living statement
of what the system currently does, and `openspec/changes/<slug>/` holds work in
flight. It is a **Node** CLI, the one non-Python dependency in an otherwise
uv-managed harness.

```bash
node --version                              # must be >= 20.19.0
npm install -g @fission-ai/openspec@latest
openspec init --tools claude                # only in a fresh project
```

`harness_setup.sh` **warns** rather than fails when Node or `openspec` is
missing — formatting, linting, tests, hooks, and every other command work
without it. Only the change loop needs it.

`openspec init` writes three things, all owned by the CLI and none of them by
this template: `openspec/`, `.claude/commands/opsx/`, and
`.claude/skills/openspec-*/`. Keep them current with `openspec update`, never by
hand. Both `scripts/generate_template_manifest.py` and the `setup-update` skill
exclude these paths explicitly, so template updates and OpenSpec updates never
fight over the same file.

Then install Superpowers **once per machine** inside a Claude Code session
(this template assumes Superpowers **v6.2+**, latest as of 2026-08-05):

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
reviewer. SDD scratch files live in `.superpowers/sdd/<plan-basename>/`
(gitignored here) — since 6.2.0 the workspace is scoped per plan, so a
follow-up plan can't read a prior plan's progress ledger.

Then open Claude Code and run the planning pipeline:

```
(plan)            # Superpowers brainstorming/writing-plans conversations
                  #   → docs/prd.md + docs/architecture.md
                  # ← HUMAN GATE: review and approve both docs
/sprint-planning  # Break the approved docs into stories → stories/draft/
                  # ← HUMAN GATE: move stories to stories/ready/
/dev-story [id]   # Implement a story end-to-end (omit id to pick lowest-numbered)
```

---

## Project structure (post-setup)

```
.
├── CLAUDE.md                            # Project brain — read every session
├── Makefile                             # Single entry point for all commands
├── pyproject.toml                       # Python deps + tool config
├── harness_setup.sh                     # One-command bootstrap
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
│   │   ├── sprint-planning.md           # /sprint-planning — break approved docs into stories
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
│       ├── graphify/SKILL.md            # Optional: knowledge graph
│       ├── setup-base/                  # Scan project setup health
│       ├── setup-migrate/               # Migrate existing projects to this framework
│       ├── setup-update/                # Update a copied project to the latest template
│       └── rescan-docs/                 # Reverse-engineer PRD + architecture + stories from code
│
├── stories/
│   ├── STORY_TEMPLATE.md
│   ├── draft/        ← /sprint-planning writes here
│   ├── ready/        ← human moves stories here to unblock agents
│   ├── in-progress/  ← agent working (git worktree)
│   ├── review/       ← PR open
│   └── done/         ← merged
│
├── config/
│   └── models.json                      # Model assignments per tier
├── scripts/
│   └── configure.py                     # Patches agents with model assignments
└── docs/
    ├── prd.md / architecture.md         # Templates (planning fills these in)
    └── coding-standards.md
```

---

## Hooks (deterministic guardrails)

Run on every tool call. No LLM judgment — pure code.

| Hook | Trigger | Action |
|------|---------|--------|
| `post_tool_lint.py` | Write/Edit | Auto-lint after file changes |
| `post_tool_secrets.py` | Write/Edit | Block committed credentials |
| `post_tool_feature_claude_reminder.py` | Write/Edit (feature `CLAUDE.md`) | Nudge to add the root CLAUDE.md pointer |
| `pre_tool_dangerous.py` | Bash | Block rm -rf, force push, etc. |
| `pre_tool_env_guard.py` | Read/Glob/LS/Grep/Bash | Block Claude reading `.env` |
| `stop_story_lifecycle.py` | Stop | Move story file `review/` → `done/` after merge |

---

## Optional skills

**Graphify** (recommended for large codebases):
```bash
pip install graphifyy && graphify claude install
graphify .   # builds knowledge graph
```
Gives agents a 71x token-compressed map of the codebase to query
instead of grepping raw files. Hooks tell Claude to consult it automatically.

---

## Migrating an existing project

To adopt this framework on an existing codebase (instead of starting fresh),
run the migration script from wherever you cloned this repo:

```bash
python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/your/project --dry
python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/your/project
```

This copies hooks, commands, the security agent, config, scripts, docs, and
our skills (`rescan-docs`, `setup-base`, `setup-migrate`, `setup-update`,
`graphify`) into your project without overwriting anything that
already exists.

Then open Claude Code in your project and generate planning docs from the existing code:

```
/rescan-docs      # Analyses codebase → PRD + architecture in docs/ + story stubs
/sprint-planning  # Breaks the reviewed docs into further stories
```

Move stories from `stories/draft/` to `stories/ready/` when you're ready to implement.

---

## Staying updatable

Upstream framework updates do not touch your customisations:

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
