---
name: setup-migrate
description: >
  Migrate an existing Claude Code / BMAD project to the full Agentic Engineering
  framework (BMAD + Superpowers + Claude Code Primitives). Use this skill whenever
  a user wants to adopt, retrofit, or align their project with the structured
  agentic engineering pipeline — including CLAUDE.md completion, story file
  canonicalisation, hook configuration, agent/command reconciliation, and
  CI/CD wiring. Trigger on phrases like "migrate to agentic engineering",
  "set up agentic framework", "adopt BMAD structure", "add Claude Code primitives",
  or "improve my Claude Code setup".
---

# Agentic Engineering Migration Skill

This skill guides Claude Code through migrating an existing project to the
Agentic Engineering framework. The mechanical parts (directory creation, file
scaffolding) are handled by `setup_migrate.py`. This skill handles the **judgment
calls** that a script cannot: merging existing content, reconciling conflicts,
and making project-specific decisions.

---

## Step 0 — Run the audit script first

Before doing anything else, run the migration script in dry-run mode to get
a complete picture of the project's current state:

```bash
python setup_migrate.py . --dry
```

Read the output carefully. You now know:
- Which directories are missing
- Which files are missing
- Which CLAUDE.md sections are absent
- Which hooks/commands/agents exist vs. are missing
- Whether orphaned story files need moving
- Whether a hook/Superpowers conflict exists

---

## Step 1 — Run the scaffold

Once you and the user have reviewed the audit, run the scaffold:

```bash
python setup_migrate.py .
```

This creates all missing structure **without overwriting anything existing**.
A report is saved to `.claude/migration-report.json`.

---

## Step 2 — Reconcile CLAUDE.md (judgment required)

The script creates a CLAUDE.md only if none exists. If one already exists,
you must merge intelligently.

**Actions:**
1. Read the existing CLAUDE.md fully
2. Check which sections from the framework are missing:
   - Coding Standards
   - Security Policies
   - Git Strategy
   - Review Checklist
   - Notes on Hooks (Superpowers/run-tests conflict warning)
   - Doc Links
3. For each missing section, add it below the existing content — **never
   replace existing content**, only append or insert clearly-marked sections
4. If the user has custom sections, preserve them exactly
5. Add the Superpowers/run-tests conflict note if both are present

**Key content to add if missing:**

```markdown
## Notes on Hooks

- `post-write-tests.sh` and Superpowers TDD are redundant.
  Disable the hook in Superpowers sessions to avoid double test runs.
- `check-secrets` hook + Security Reviewer: keep both (defence-in-depth).
```

---

## Step 3 — Reconcile existing slash commands (judgment required)

The user may have existing slash commands with different names or content.

**Actions:**
1. List all files in `.claude/commands/`
2. For each framework command that's missing, check if the user has a
   functionally equivalent command with a different name
3. If equivalent exists: create a thin wrapper that calls theirs, or suggest
   renaming — **ask the user before renaming**
4. If no equivalent: the scaffold already created a stub — inform the user
   they need to fill in the agent instructions

**Common equivalences to check:**
- `/dev`, `/code`, `/build` → likely maps to `/implement`
- `/plan`, `/brief`, `/idea` → likely maps to `/plan` (Analyst)
- `/pr-review`, `/check` → likely maps to `/review`

---

## Step 4 — Reconcile existing agents (judgment required)

Same pattern as commands. Check `.claude/agents/` for:
- Existing agents with different names but same role
- Existing agents with useful project-specific instructions that should be
  preserved and merged into the framework agent stubs

**If the user has a detailed existing developer agent:**
Merge their instructions into `.claude/agents/developer.md` — their
project-specific context is more valuable than the stub.

---

## Step 5 — Migrate story files (judgment required)

If orphaned story files were found in the audit:

1. Review each file to determine its kanban stage:
   - No implementation started → `stories/draft/`
   - Confirmed, ready to implement → `stories/ready/`
   - Partially done → `stories/in-progress/`
   - PR open → `stories/review/`
   - Merged/done → `stories/done/`

2. Check if stories have the required fields. A valid story file needs:
   - Feature description + user story
   - Exact file paths to touch
   - Acceptance criteria (testable)
   - Test strategy
   - Architectural constraints

3. If stories are missing fields, flag them for the user — they'll need
   enrichment before auto-implementation will work reliably.

**Story file naming convention:** `story-NNN-<slug>.md`
If existing names differ, rename them — but tell the user what you renamed.

---

## Step 6 — Configure hooks for the project's stack

The scaffold creates hook stubs. Now fill in the actual commands:

1. Ask the user (or detect from project files) what stack they're using:
   - Check for `pyproject.toml`, `setup.py` → Python (ruff, pytest)
   - Check for `package.json` → JS/TS (eslint, jest/vitest)
   - Check for `go.mod` → Go (gofmt, go test)
   - Check for `Cargo.toml` → Rust (cargo fmt, cargo test)

2. Edit `post-write-lint.sh` to use the correct linter
3. Edit `post-write-tests.sh` to use the correct test runner
4. Make all hooks executable: `chmod +x .claude/hooks/*.sh`

**Important:** If Superpowers TDD is in use (check CLAUDE.md or ask user),
add a comment in `post-write-tests.sh` and the CLAUDE.md notes section
reminding them to disable the hook in Superpowers sessions.

---

## Step 7 — Wire CI/CD (optional, if user wants it)

If the project uses GitHub Actions and the user wants automated PR review:

Create `.github/workflows/claude-review.yml`:

```yaml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          prompt: |
            Review this PR for:
            - Logic bugs and edge cases
            - Security issues (OWASP Top 10)
            - CLAUDE.md convention compliance
            - Test coverage gaps
            Provide structured feedback with severity levels.
```

**Review trigger strategy (pick one):**
- GitHub Actions: primary automated reviewer on every PR
- `/review`: manual, on-demand, interactive
- `/loop`: status summaries only — don't re-review what GH Actions covers

---

## Step 8 — Final validation

Run the audit one more time to confirm everything is in place:

```bash
python setup_migrate.py . --dry
```

The output should show mostly ✓ (green). Remaining ✗ items are ones that
need human attention (CLAUDE.md TODO sections, story enrichment, etc.).

Tell the user:
1. Which items are complete
2. Which items need their input (CLAUDE.md TODOs, story quality)
3. Recommended next command to run: `/gate-check` to validate
   PRD ↔ architecture consistency

---

## Decision reference: BMAD vs Superpowers overlap

Both BMAD and Superpowers have dev agents. The division is clean:
- **BMAD** → planning phases (Analyst, PM, Architect, Scrum Master)
- **Superpowers** → implementation discipline (TDD enforcement, subtask dispatch)

Don't merge or collapse these — they serve different phases.

---

## Guardrails to follow throughout

- **Never overwrite existing files** — always append or merge
- **Ask before renaming** existing commands or agents
- **Preserve project-specific content** — it's more valuable than generic stubs
- **Flag conflicts** (e.g. hook + Superpowers) rather than silently resolving
- **Story quality is the bottleneck** — flag thin stories before the user
  tries auto-implementation
