#!/usr/bin/env python3
"""
Agentic Engineering Migration Script
Audits an existing Claude Code / BMAD project and scaffolds missing
structure from the Agentic Engineering framework (BMAD + Superpowers +
Claude Code Primitives).

Usage:
    python migrate.py [project_root]        # audit + scaffold
    python migrate.py [project_root] --dry  # audit only, no changes
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ── colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✓{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def missing(msg): print(f"  {RED}✗{RESET}  {msg}")
def info(msg):  print(f"  {CYAN}→{RESET}  {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}\n{'─'*60}")


# ── expected structure ────────────────────────────────────────────────────────

# Directories that must exist
REQUIRED_DIRS = [
    ".claude/agents",
    ".claude/commands",
    ".claude/hooks",
    ".claude/skills",
    "stories/draft",
    "stories/ready",
    "stories/in-progress",
    "stories/review",
    "stories/done",
    "docs",
]

# Files checked for existence (not created — content is project-specific)
REQUIRED_FILES = [
    "CLAUDE.md",
    "docs/prd.md",
    "docs/architecture.md",
]

# CLAUDE.md sections that should be present
CLAUDE_MD_SECTIONS = [
    "Coding Standards",
    "Security",
    "Git",
    "Review",
    "docs/",          # doc links section (flexible heading)
]

# Hooks that should exist and what they do
EXPECTED_HOOKS = {
    "post-write-lint.sh":    "Auto-lint after every file write/edit",
    "post-write-tests.sh":   "Run tests after every file write/edit",
    "post-write-secrets.sh": "Block committed credentials",
    "pre-bash-guard.sh":     "Block dangerous bash (rm -rf, force push)",
}

# Slash commands expected
EXPECTED_COMMANDS = {
    "plan.md":            "/plan  — Analyst: stakeholder interviews, product brief",
    "prd.md":             "/prd   — PM: structured PRD with acceptance criteria",
    "architecture.md":    "/architecture — Architect: system design, API contracts",
    "gate-check.md":      "/gate-check — Validator: PRD ↔ architecture consistency",
    "sprint-planning.md": "/sprint-planning — Scrum Master: break into story files",
    "implement.md":       "/implement — Developer: TDD implementation (Superpowers)",
    "review.md":          "/review — Code reviewer: convention + bug check",
    "code-review.md":     "/code-review — 4 parallel agents, confidence scoring",
    "security-scan.md":   "/security-scan — OWASP Top 10, secrets, CVEs",
    "dispatch.md":        "/dispatch — Background worker for long-running tasks",
    "loop.md":            "/loop — Polling loop for auto-implementation",
}

# Agents expected
EXPECTED_AGENTS = {
    "analyst.md":           "Analyst (BMAD planning)",
    "pm.md":                "Product Manager (BMAD planning)",
    "architect.md":         "Architect (BMAD planning)",
    "scrum-master.md":      "Scrum Master (BMAD sprint planning)",
    "developer.md":         "Developer / Subagent (implementation)",
    "code-reviewer.md":     "Code Reviewer (read-only subagent)",
    "security-reviewer.md": "Security Reviewer (read-only subagent)",
    "qa-engineer.md":       "QA Engineer (validation)",
    "devops.md":            "DevOps (CI/CD)",
}


# ── audit functions ───────────────────────────────────────────────────────────

def audit_dirs(root: Path) -> dict:
    results = {}
    for d in REQUIRED_DIRS:
        p = root / d
        results[d] = p.exists() and p.is_dir()
    return results

def audit_files(root: Path) -> dict:
    results = {}
    for f in REQUIRED_FILES:
        p = root / f
        results[f] = p.exists() and p.is_file()
    return results

def audit_claude_md(root: Path) -> dict:
    """Check which key sections exist in CLAUDE.md."""
    p = root / "CLAUDE.md"
    if not p.exists():
        return {s: False for s in CLAUDE_MD_SECTIONS}
    content = p.read_text(errors="replace").lower()
    return {s: s.lower() in content for s in CLAUDE_MD_SECTIONS}

def audit_hooks(root: Path) -> dict:
    hooks_dir = root / ".claude" / "hooks"
    if not hooks_dir.exists():
        return {k: False for k in EXPECTED_HOOKS}
    existing = {f.name for f in hooks_dir.iterdir()}
    return {k: k in existing for k in EXPECTED_HOOKS}

def audit_commands(root: Path) -> dict:
    cmd_dir = root / ".claude" / "commands"
    if not cmd_dir.exists():
        return {k: False for k in EXPECTED_COMMANDS}
    existing = {f.name for f in cmd_dir.iterdir()}
    return {k: k in existing for k in EXPECTED_COMMANDS}

def audit_agents(root: Path) -> dict:
    agents_dir = root / ".claude" / "agents"
    if not agents_dir.exists():
        return {k: False for k in EXPECTED_AGENTS}
    existing = {f.name for f in agents_dir.iterdir()}
    return {k: k in existing for k in EXPECTED_AGENTS}

def audit_stories(root: Path) -> dict:
    """Find story files outside the kanban structure."""
    results = {"kanban_dirs": {}, "orphaned_stories": []}
    for stage in ["draft", "ready", "in-progress", "review", "done"]:
        d = root / "stories" / stage
        results["kanban_dirs"][stage] = d.exists()

    # look for .md files that look like stories outside stories/
    for p in root.rglob("*.md"):
        parts = p.relative_to(root).parts
        if parts[0] == "stories":
            continue  # already in kanban
        if parts[0] in (".claude", "docs", "node_modules", ".git"):
            continue
        name = p.stem.lower()
        if any(kw in name for kw in ["story", "ticket", "task", "feature", "us-", "story-"]):
            results["orphaned_stories"].append(str(p.relative_to(root)))

    return results

def check_superpowers_conflict(root: Path) -> bool:
    """Check if run-tests hook + Superpowers could conflict."""
    hooks_dir = root / ".claude" / "hooks"
    has_run_tests = (hooks_dir / "post-write-tests.sh").exists()
    # Heuristic: if superpowers skill/plugin is referenced anywhere
    claude_md = (root / "CLAUDE.md").read_text(errors="replace") if (root / "CLAUDE.md").exists() else ""
    has_superpowers = "superpowers" in claude_md.lower()
    return has_run_tests and has_superpowers


# ── scaffold functions ────────────────────────────────────────────────────────

HOOK_TEMPLATES = {
    "post-write-lint.sh": """\
#!/usr/bin/env bash
# Auto-lint after every Write/Edit tool call.
# Adjust the linter command for your stack.
# Examples: ruff check, eslint, flake8, etc.

FILE="$1"   # Claude Code passes the modified file path

# --- Python ---
if [[ "$FILE" == *.py ]]; then
  command -v ruff &>/dev/null && ruff check --fix "$FILE" && ruff format "$FILE"
  exit 0
fi

# --- JavaScript / TypeScript ---
if [[ "$FILE" == *.js || "$FILE" == *.ts || "$FILE" == *.tsx ]]; then
  command -v eslint &>/dev/null && eslint --fix "$FILE"
  exit 0
fi
""",

    "post-write-secrets.sh": """\
#!/usr/bin/env bash
# Block accidental credential commits.
# Runs after every Write/Edit. Exits non-zero to block if secrets found.

FILE="$1"
[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

PATTERNS=(
  'PRIVATE KEY'
  'BEGIN RSA'
  'AWS_SECRET'
  r'api_key\s*='
  r'password\s*=\s*[^$]'
  r'secret\s*=\s*[^$]'
)

for pat in "${PATTERNS[@]}"; do
  if grep -qiE "$pat" "$FILE" 2>/dev/null; then
    echo "⛔  Potential secret detected in $FILE (pattern: $pat)"
    echo "    Remove the credential and use environment variables instead."
    exit 1
  fi
done
""",

    "pre-bash-guard.sh": """\
#!/usr/bin/env bash
# Block dangerous bash commands before execution.
# Claude Code passes the command as $1.

CMD="$1"

DANGEROUS=(
  'rm -rf /'
  'rm -rf ~'
  'git push --force'
  'git push -f'
  'git reset --hard HEAD'
  'DROP TABLE'
  'DROP DATABASE'
  'format '
  'mkfs.'
)

for danger in "${DANGEROUS[@]}"; do
  if echo "$CMD" | grep -qF "$danger"; then
    echo "⛔  Blocked dangerous command: $danger"
    echo "    If intentional, run this manually outside Claude Code."
    exit 1
  fi
done
""",

    "post-write-tests.sh": """\
#!/usr/bin/env bash
# Run tests after every Write/Edit.
# NOTE: Disable this hook when using Superpowers TDD —
#       Superpowers already runs tests per subtask (see CLAUDE.md).

FILE="$1"

# Only run for source files, skip test files themselves to avoid loops
if [[ "$FILE" == *test* || "$FILE" == *spec* ]]; then
  exit 0
fi

# --- Python ---
if [[ "$FILE" == *.py ]]; then
  command -v pytest &>/dev/null && pytest --tb=short -q 2>&1 | tail -20
  exit 0
fi

# --- JavaScript / TypeScript ---
if [[ "$FILE" == *.js || "$FILE" == *.ts || "$FILE" == *.tsx ]]; then
  command -v npm &>/dev/null && npm test --silent 2>&1 | tail -20
  exit 0
fi
""",
}

COMMAND_TEMPLATES = {
    "plan.md": "# /plan\nActivate the **Analyst** agent.\n\nConduct stakeholder interviews and produce a product brief ready for `/prd`.\n\nLoad `.claude/agents/analyst.md` for full persona and instructions.\n",
    "prd.md": "# /prd\nActivate the **PM** agent.\n\nTransform the product brief into a structured PRD with acceptance criteria.\n\nLoad `.claude/agents/pm.md` for full persona and instructions.\n",
    "architecture.md": "# /architecture\nActivate the **Architect** agent.\n\nProduce system design, API contracts, and data models from the PRD.\n\nLoad `.claude/agents/architect.md` for full persona and instructions.\n",
    "gate-check.md": "# /gate-check\nActivate the **Validator**.\n\nCheck PRD ↔ architecture consistency. Surface gaps before sprint planning.\n**Human gate** — review output before proceeding.\n",
    "sprint-planning.md": "# /sprint-planning\nActivate the **Scrum Master** agent.\n\nBreak the architecture into self-contained story files in `stories/draft/`.\n**Human gate** — prioritise and confirm stories before moving to `ready/`.\n\nLoad `.claude/agents/scrum-master.md` for full persona and instructions.\n",
    "implement.md": "# /implement\nActivate the **Developer** subagent with Superpowers TDD.\n\nUsage: `/implement <story-file>`\n\nWorkflow:\n1. Brainstorm — clarifying questions, design spec, file paths\n2. Plan — 2-5 min subtasks with exact code context\n3. Test First — write failing tests before any code\n4. Implement — minimum code to pass tests\n5. Verify — full test suite, coverage check\n\nCode written before tests is deleted. This is enforced, not suggested.\n",
    "review.md": "# /review\nDefault code reviewer (included with subscription).\n\nChecks: convention compliance, bug detection, CLAUDE.md adherence.\nUse for all routine PRs.\n",
    "code-review.md": "# /code-review\nSelective deep review — 4 parallel review agents with confidence scoring (>=80).\n\nUse for: security-sensitive changes, core infrastructure PRs.\nCost: ~$15-25 per review.\n",
    "security-scan.md": "# /security-scan\nDedicated read-only security agent.\n\nCovers: OWASP Top 10, secrets, CVEs, CWE classification.\nAgent has no write access — read-only by design.\n",
    "dispatch.md": "# /dispatch\nBackground worker for long-running tasks.\n\nUsage: `/dispatch <task description>`\n\nMain session stays focused on orchestration.\nWorker gets full context, asks async Q&A, reports back when done.\n",
    "loop.md": "# /loop\nPolling loop for auto-implementation.\n\nUsage: `/loop <interval>  <task>`\n\nExamples:\n  `/loop 5m  Check stories/ready/ and auto-implement in worktrees`\n  `/loop 30m Check open PRs and summarise status`\n\nCap parallel worktrees at 3-5 to limit merge conflicts.\n",
}

AGENT_TEMPLATES = {
    "analyst.md":           "# Analyst\n\nYou are a senior business analyst. Your job is to interview stakeholders, clarify requirements, and produce a concise product brief.\n\n## Responsibilities\n- Ask clarifying questions to surface unknowns\n- Identify scope boundaries\n- Produce a product brief ready for the PM\n\n## Output format\nMarkdown document: problem statement, goals, non-goals, constraints, open questions.\n",
    "pm.md":                 "# Product Manager\n\nYou are a senior PM. Transform the product brief into a structured PRD.\n\n## Output format\n- Overview\n- User stories (As a… I want… So that…)\n- Acceptance criteria (testable, unambiguous)\n- Out of scope\n- Open questions\n",
    "architect.md":          "# Architect\n\nYou are a senior software architect. Design the system from the PRD.\n\n## Output format\n- System diagram (text/ASCII)\n- Component responsibilities\n- API contracts\n- Data models\n- Tech decisions + rationale\n- Risks\n",
    "scrum-master.md":       "# Scrum Master\n\nBreak the architecture into self-contained story files.\n\n## Each story file must include\n- Feature description + user story\n- Exact file paths to touch\n- Acceptance criteria (testable)\n- Test strategy (unit / integration / e2e)\n- Architectural constraints\n\nWrite story files to `stories/draft/story-NNN-<slug>.md`.\n",
    "developer.md":          "# Developer\n\nYou are a senior developer using Superpowers TDD.\n\n## Workflow (enforced)\n1. Brainstorm — clarifying questions, design spec, file paths\n2. Plan — 2-5 min subtasks with exact code context\n3. Test First — write failing tests before any implementation code\n4. Implement — minimum code to pass tests\n5. Verify — full suite passes, coverage acceptable\n\n**Any code written before tests are green is deleted.**\n",
    "code-reviewer.md":      "# Code Reviewer\n\nRead-only. Review PRs for:\n- Logic bugs\n- Convention compliance (see CLAUDE.md)\n- Test coverage gaps\n- Performance issues\n\nOutput: structured review with severity levels (blocker / major / minor / nit).\n",
    "security-reviewer.md":  "# Security Reviewer\n\nRead-only. Scan for:\n- OWASP Top 10\n- Hardcoded secrets / credentials\n- Known CVEs in dependencies\n- CWE classifications\n\nNever modify files. Output: security report with CWE IDs and remediation steps.\n",
    "qa-engineer.md":        "# QA Engineer\n\nValidate completed implementations against story acceptance criteria.\n\n- Run the full test suite\n- Verify acceptance criteria manually where automated tests don't cover\n- Move story file to `stories/done/` on pass\n- Move back to `stories/in-progress/` with failure notes on fail\n",
    "devops.md":             "# DevOps\n\nManage CI/CD pipeline.\n\n- Configure GitHub Actions workflows\n- Monitor deployment health\n- Manage secrets and environment config\n- Ensure main branch is always deployable\n",
}

CLAUDE_MD_TEMPLATE = """\
# {project_name}

> Generated by agentic-engineering migration script on {date}.
> Fill in the sections marked TODO — this file is Claude's persistent memory.

---

## Coding Standards

TODO: Add your architecture decisions, conventions, and preferred libraries.

Example:
- Language: Python 3.12
- Formatter: ruff
- Test framework: pytest
- No bare `except:` clauses
- Type hints required on all public functions

---

## Security Policies

TODO: Define your security rules.

Example:
- No credentials in source — use environment variables
- All user input must be validated/sanitised before use
- Follow OWASP Top 10 mitigations
- Auth: [your auth pattern here]

---

## Git Strategy

TODO: Define your branching and commit conventions.

Example:
- Branch naming: `feature/<story-id>-<slug>`, `fix/<slug>`
- Commit format: `<type>(<scope>): <summary>` (conventional commits)
- PRs require at least one review before merge
- Never force-push to main

---

## Review Checklist

What every reviewer (human or agent) checks on every PR:

- [ ] Tests pass and coverage hasn't dropped
- [ ] No new secrets or credentials
- [ ] Follows coding standards above
- [ ] Acceptance criteria met (cross-reference story file)
- [ ] No obvious security regressions

---

## Notes on Hooks

- `post-write-tests.sh` and Superpowers TDD are redundant.
  **Disable the hook in Superpowers sessions** to avoid double test runs.
- `check-secrets` hook + Security Reviewer are intentionally kept both
  (defence-in-depth).

---

## Doc Links

- PRD: [docs/prd.md](docs/prd.md)
- Architecture: [docs/architecture.md](docs/architecture.md)
- Stories: [stories/](stories/)
"""


# ── scaffold logic ────────────────────────────────────────────────────────────

def scaffold(root: Path, audit: dict, dry: bool):
    """Create missing structure. Never overwrites existing files."""
    created = []
    skipped = []

    def make_dir(rel: str):
        p = root / rel
        if not p.exists():
            if not dry:
                p.mkdir(parents=True, exist_ok=True)
            created.append(f"DIR  {rel}/")
        else:
            skipped.append(f"DIR  {rel}/  (exists)")

    def make_file(rel: str, content: str):
        p = root / rel
        if not p.exists():
            if not dry:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)
            created.append(f"FILE {rel}")
        else:
            skipped.append(f"FILE {rel}  (exists — not overwritten)")

    # Directories
    for d in REQUIRED_DIRS:
        make_dir(d)

    # Hooks
    for name, content in HOOK_TEMPLATES.items():
        rel = f".claude/hooks/{name}"
        make_file(rel, content)
        if not dry and (root / rel).exists():
            os.chmod(root / rel, 0o755)

    # Commands
    for name, content in COMMAND_TEMPLATES.items():
        make_file(f".claude/commands/{name}", content)

    # Agents
    for name, content in AGENT_TEMPLATES.items():
        make_file(f".claude/agents/{name}", content)

    # CLAUDE.md — only if missing
    if not (root / "CLAUDE.md").exists():
        project_name = root.resolve().name.replace("-", " ").replace("_", " ").title()
        content = CLAUDE_MD_TEMPLATE.format(
            project_name=project_name,
            date=datetime.now().strftime("%Y-%m-%d"),
        )
        make_file("CLAUDE.md", content)

    # Placeholder docs
    make_file("docs/prd.md", "# Product Requirements Document\n\nTODO: Complete with `/prd` command.\n")
    make_file("docs/architecture.md", "# Architecture\n\nTODO: Complete with `/architecture` command.\n")

    return created, skipped


# ── reporting ─────────────────────────────────────────────────────────────────

def print_audit(root: Path):
    header("1 / DIRECTORY STRUCTURE")
    dirs = audit_dirs(root)
    for d, exists in dirs.items():
        (ok if exists else missing)(d)

    header("2 / REQUIRED FILES")
    files = audit_files(root)
    for f, exists in files.items():
        (ok if exists else missing)(f)

    header("3 / CLAUDE.md SECTIONS")
    sections = audit_claude_md(root)
    if not (root / "CLAUDE.md").exists():
        warn("CLAUDE.md not found — all sections missing")
    else:
        for s, found in sections.items():
            (ok if found else warn)(s)

    header("4 / HOOKS")
    hooks = audit_hooks(root)
    for name, exists in hooks.items():
        desc = EXPECTED_HOOKS[name]
        (ok if exists else missing)(f"{name}  ({desc})")

    header("5 / SLASH COMMANDS")
    cmds = audit_commands(root)
    for name, exists in cmds.items():
        desc = EXPECTED_COMMANDS[name]
        (ok if exists else missing)(f"{name}  —  {desc}")

    header("6 / AGENTS")
    agents = audit_agents(root)
    for name, exists in agents.items():
        desc = EXPECTED_AGENTS[name]
        (ok if exists else missing)(f"{name}  —  {desc}")

    header("7 / STORY FILES")
    stories = audit_stories(root)
    for stage, exists in stories["kanban_dirs"].items():
        (ok if exists else missing)(f"stories/{stage}/")
    if stories["orphaned_stories"]:
        warn("Story files found outside kanban structure:")
        for p in stories["orphaned_stories"]:
            info(f"  Consider moving: {p}  →  stories/draft/")

    header("8 / CONFLICT CHECKS")
    if check_superpowers_conflict(root):
        warn("run-tests hook + Superpowers TDD detected — these are redundant.")
        info("Disable post-write-tests.sh in Superpowers sessions (see CLAUDE.md note).")
    else:
        ok("No hook/Superpowers conflict detected")


def print_summary(created: list, skipped: list, dry: bool):
    header("SCAFFOLD SUMMARY" + (" (DRY RUN — no files written)" if dry else ""))
    if created:
        print(f"\n  {GREEN}Created:{RESET}")
        for item in created:
            print(f"    + {item}")
    if skipped:
        print(f"\n  {CYAN}Skipped (already exist):{RESET}")
        for item in skipped:
            print(f"    · {item}")
    print()


def save_report(root: Path, created: list, skipped: list):
    report = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(root.resolve()),
        "created": created,
        "skipped": skipped,
    }
    p = root / ".claude" / "migration-report.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2))
    info(f"Report saved: {p.relative_to(root)}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Agentic Engineering migration tool")
    parser.add_argument("project_root", nargs="?", default=".", help="Path to project root (default: current dir)")
    parser.add_argument("--dry", action="store_true", help="Audit only — no files created")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"{RED}Error:{RESET} Path does not exist: {root}")
        sys.exit(1)

    print(f"\n{BOLD}Agentic Engineering Migration{RESET}")
    print(f"Project: {CYAN}{root}{RESET}")
    print(f"Mode:    {'DRY RUN (audit only)' if args.dry else 'SCAFFOLD (create missing)'}")

    print_audit(root)

    if not args.dry:
        header("SCAFFOLDING MISSING STRUCTURE")
        audit = {}  # passed for future conditional logic
        created, skipped = scaffold(root, audit, dry=False)
        print_summary(created, skipped, dry=False)
        save_report(root, created, skipped)
    else:
        header("DRY RUN — WHAT WOULD BE CREATED")
        _, created_dry = scaffold(root, {}, dry=True)  # unused return
        created, skipped = scaffold(root, {}, dry=True)
        print_summary(created, skipped, dry=True)

    print(f"{BOLD}Next steps:{RESET}")
    print("  1. Review CLAUDE.md and fill in the TODO sections")
    print("  2. Populate docs/prd.md and docs/architecture.md (or use /prd, /architecture)")
    print("  3. Run `/gate-check` to validate PRD ↔ architecture consistency")
    print("  4. Move story files into stories/draft/ and review with /sprint-planning")
    print("  5. For the CLAUDE.md judgment work, use the migration SKILL.md in Claude Code\n")


if __name__ == "__main__":
    main()
