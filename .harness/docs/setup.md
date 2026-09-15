# Setup

One-time bootstrap and optional add-ons for this template. After your project
is up and running, you can ignore this file.

---

## Quick start

```bash
git clone <this-repo> my-project && cd my-project
bash .harness/setup.sh
```

`.harness/setup.sh` installs Python deps via `uv`, bootstraps `.env`, and checks
for OpenSpec.

### OpenSpec (required for the change loop)

OpenSpec owns the document lifecycle: `openspec/specs/` is the living statement
of what the system currently does, and `openspec/changes/<slug>/` holds work in
flight. It is a **Node** CLI, a non-Python dependency in an otherwise
uv-managed harness.

```bash
node --version                              # must be >= 20.19.0
npm install -g @fission-ai/openspec@latest
openspec init --tools claude                # only in a fresh project
```

`.harness/setup.sh` **warns** rather than fails when Node or `openspec` is
missing. Formatting, linting, tests and hooks can run separately, but the full
`make check` now includes doctor and requires initialized OpenSpec structure plus
the installed Node/Graft dependency. Doctor does not execute the OpenSpec CLI;
the change loop uses it for document lifecycle operations.

`openspec init` writes three things, all owned by the CLI and none of them by
this template: `openspec/`, `.claude/commands/opsx/`, and
`.claude/skills/openspec-*/`. Keep them current with `openspec update`, never by
hand. Both `scripts/generate_template_manifest.py` and the `setup-update` skill
exclude these paths explicitly, so template updates and OpenSpec updates never
fight over the same file.

### Application navigation (Graft)

Install Node.js 22.12+ and run `make graft-install` after bootstrap or migration.
For older installations whose Makefile lacks that target, run `npm ci --prefix
.harness/graft --no-audit --no-fund`, then `.harness/bin/graft install-skill` to
preview and `.harness/bin/graft install-skill --apply` to apply. This adds the
unchanged upstream skill and missing cache ignore rules, preserving existing
hooks, instructions, statusline and customized skill content. No global agent
configuration is installed. Set the application roots and agent PATH as described
in [HARNESS.md](../../HARNESS.md#application-navigation-with-graft). Graph
preparation is not applicable until application sources are configured.

### Installation diagnosis

Adopt/update use shared explicit ownership and installed baselines. Plans are
read-only; apply requires a clean committed target and refuses all conflicts.
Existing project tooling and configuration survive. Initialize OpenSpec before
apply and prepare external Graft prerequisites explicitly; the engine never
installs dependencies or copies a graph. Missing prerequisites fail the mandatory
post-apply doctor check and produce recovery instructions. See
[safe installation](installation.md) for the complete setup and recovery sequence.

Legacy version records are validated during conversion; `.factory/state.json`
then becomes the installed authority. Conflicts never advance baselines. Starter
manifest regeneration refreshes distribution hashes and starter state together.

After initializing OpenSpec and installing Graft, run
`uv run --no-project --isolated --python 3.12 python factory doctor`. The same
offline diagnosis runs in `make check`. Correct each reported installation error
before verification. Doctor does not execute project checks or Graft; freshness
remains a separate `.harness/bin/graft check`. Pinned Graft can contact the
registry during its CLI upkeep, so doctor reports freshness not assessed.
See [the step-by-step reference](../../HARNESS.md#start-here-the-development-loop)
for the complete setup-to-review sequence and command responsibilities.

### Optional Superpowers techniques

An existing Superpowers installation may remain for selected TDD, debugging or
verification techniques. The factory does not require it for any stage and owns
planning, task decomposition, branch/worktree management, review and shipping.
Measure usage before deciding whether to remove an existing installation; see
[workflow runs](../evals/workflow-runs.md).

For the workflow, gates and tier-specific commands, read
[FACTORY.md](../../FACTORY.md). Runtime commands and check mechanics are in
[HARNESS.md](../../HARNESS.md).

---

## Project structure (post-setup)

```
.
├── CLAUDE.md                            # Project brain — read every session
├── Makefile                             # Single entry point for all commands
├── pyproject.toml                       # Python deps + tool config
├── .harness/setup.sh                     # One-command bootstrap
├── .env.template                        # Committed — documents all env vars, no real values
├── .gitignore
│
├── .claude/
│   ├── settings.json                    # Hook wiring
│   ├── agents/                          # Project-specific agents only
│   │   ├── security-reviewer.md         # OWASP/CVE scan, read-only
│   │   └── verifier.md                  # Final check in a fresh context, read-only
│   ├── commands/                        # Slash commands
│   │   ├── dev-change.md                # /dev-change <slug> <group> — implement one task group
│   │   ├── archive-change.md            # /archive-change <slug> — merge deltas into specs
│   │   ├── opsx/                        # OpenSpec's own commands — generated by `openspec update`, gitignored, not committed
│   │   ├── review.md                    # /review
│   │   └── commit-push-pr.md            # /commit-push-pr
│   ├── hooks/
│   │   ├── pre_tool_dangerous.py        # Block rm -rf, force push
│   │   ├── pre_tool_env_guard.py        # Block Claude reading .env
│   │   ├── post_tool_secrets.py         # Block committed credentials
│   │   └── post_tool_lint.py            # Auto-lint after file writes
│   └── skills/
│       ├── graphify/SKILL.md            # Optional: knowledge graph
│       ├── setup-update/                # Update a copied project to the latest template
│       ├── crystallize/                 # Accepted intent → tier-specific artifacts
│       ├── shape-change/                # DEEP architecture → program design + tasks
│       ├── rescan-docs/                 # Reverse-engineer specs + product doc from code
│       └── openspec-*/                  # OpenSpec's own skills — generated by `openspec update`, gitignored, not committed
│
├── openspec/                            # CLI-owned — use `openspec update`, never hand-edit
│   ├── config.yaml                      # Schema + project context + artifact rules
│   ├── specs/                           # CANONICAL: what the system does today
│   └── changes/                         # Work in flight, one folder per change
│       └── archive/                     # Archived changes, dated
│
└── docs/
    ├── product.md                       # Durable product intent + non-goals
    ├── architecture.md                  # System shape only (behaviour lives in specs)
    ├── decisions/                       # ADRs, append-only
    └── harness/                         # This file + coding standards
```

---

## Hooks (deterministic guardrails)

Run on every tool call. No LLM judgment — pure code.

| Hook | Trigger | Action |
|------|---------|--------|
| `post_tool_lint.py` | Write/Edit | Check edited Python file only, non-mutating, silent success |
| `post_tool_secrets.py` | Write/Edit | Block committed credentials |
| `.harness/scripts/check_feature_docs.py` | Final `make check` | Fail for missing feature `CLAUDE.md`; no per-edit reminders or session state |
| `pre_tool_dangerous.py` | Bash | Block rm -rf, force push, etc. |
| `pre_tool_env_guard.py` | Read/Glob/LS/Grep/Bash | Block Claude reading `.env` |

---

## Optional skills

**Graphify** (optional, worth it on large codebases):
```bash
uv pip install graphifyy && uv run graphify claude install
uv run graphify .   # builds the knowledge graph → graphify-out/ (gitignored)
```
Gives agents a token-compressed map of the codebase to query instead of grepping
raw files. Nothing in the harness requires it, and the harness deliberately ships
no graphify skill of its own: `graphify claude install` writes one into
`~/.claude/skills/`, and a second copy here would collide with it by name and
give skill routing two entries to choose between. It earns its keep on questions
that span many files at once; for anything scoped to one feature, Grep is
simpler and just as fast.

---

## Migrating an existing project

To adopt this framework on an existing codebase (instead of starting fresh),
run the migration script from wherever you cloned this repo:

```bash
python /path/to/agentic-starter/.harness/scripts/migrate_to_framework.py /path/to/your/project --dry
python /path/to/agentic-starter/.harness/scripts/migrate_to_framework.py /path/to/your/project --apply
```

The script delegates to `factory adopt`. Review the plan first: it adds owned
factory content and bounded integration while preserving project content. Existing
conflicting factory scopes require resolution; `--force` cannot overwrite them.

Then open Claude Code in your project and generate planning docs from the existing code:

```
/rescan-docs           # Analyses the codebase → openspec/specs/ + docs/product.md
/explore "<idea>"      # Then start the loop on your first real change
```

Review the reverse-engineered specs before trusting them — they describe what the
code *does*, which is not always what it *should* do.

---

## Staying updatable

Upstream framework updates do not touch your customisations:

- **Superpowers**, if installed, stays optional and separate from agent definitions.
- **The rest of the template** (hooks, commands, docs, scripts, our skills) —
  use the **`setup-update`** skill (or `python
  /path/to/agentic-starter/.claude/skills/setup-update/scripts/setup_update.py
  /path/to/your-project --dry`). It compares owned content against installed upstream fingerprints. Use
  `--apply` explicitly after resolving any dual-change conflicts; local-only
  customizations remain preserved.
- **Your customisations** live in `.claude/agents/`, `.claude/commands/`, `.claude/hooks/`, and `CLAUDE.md` — protected by the same mechanism.
- **Graphify** (`uv pip install graphifyy --upgrade`) — optional; nothing else in the harness depends on it.

Ownership-enabled installations record installed version and upstream baselines
in `.factory/state.json`. Legacy stamps are conversion inputs, superseded by
that state after reconciliation. See [safe installation](installation.md).

## Updating to factory checks

Update Makefile, check helpers and hook wiring together. Remove the retired
`post_tool_feature_claude_reminder.py` and its settings entry after reviewing
local customizations; `check_feature_docs.py` now enforces documentation during
`make check`. Existing feature directories may need a CLAUDE.md before their
next successful gate. Existing STANDARD tasks need no shape-change migration.

Factory tooling requires Python 3.12+. Use
`uv run --no-project --isolated --python 3.12 python factory ...` without changing
a downstream application's Python requirements, environment or lockfile.
