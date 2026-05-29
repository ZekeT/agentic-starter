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
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg):
    print(f"  {GREEN}✓{RESET}  {msg}")


def warn(msg):
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def missing(msg):
    print(f"  {RED}✗{RESET}  {msg}")


def info(msg):
    print(f"  {CYAN}→{RESET}  {msg}")


def header(msg):
    print(f"\n{BOLD}{msg}{RESET}\n{'─'*60}")


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
    "docs/",  # doc links section (flexible heading)
]

# Hooks that should exist and what they do
# Note: agentic-base uses Python hooks (.py), not shell scripts (.sh)
EXPECTED_HOOKS = {
    "pre_tool_dangerous.py": "Block dangerous bash (rm -rf, force push, etc.)",
    "pre_tool_env_guard.py": "Block Claude reading .env files",
    "post_tool_secrets.py": "Block committed credentials",
    "post_tool_lint.py": "Auto-lint after every file write/edit",
}

# Slash commands in .claude/commands/ — our implementation layer only
# BMAD planning commands (/plan, /prd, /architecture, /gate-check, /sprint-planning)
# come from BMAD skill stubs in .claude/skills/, NOT from .claude/commands/
EXPECTED_COMMANDS = {
    "implement.md": "/implement — Superpowers TDD implementation",
    "review.md": "/review — Security reviewer: OWASP/CVE check",
    "commit-push-pr.md": "/commit-push-pr — Stage, commit, push, open PR",
}

# BMAD skill stubs that should exist in .claude/skills/ (after make bmad-trim-apply)
EXPECTED_BMAD_STUBS = {
    "bmad-agent-analyst",
    "bmad-agent-pm",
    "bmad-agent-architect",
    "bmad-create-prd",
    "bmad-create-architecture",
    "bmad-create-epics-and-stories",
    "bmad-check-implementation-readiness",
}

# Agents in .claude/agents/ — only what our template owns
# BMAD agents (Analyst, PM, Architect, SM) live in _bmad/ runtime — not here
# Superpowers agents (Developer, Code Reviewer) installed globally to ~/.claude/ — not here
EXPECTED_AGENTS = {
    "security-reviewer.md": "Security Reviewer (read-only, OWASP/CVE) — our only custom agent",
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
    """Audit our implementation commands (.claude/commands/)."""
    cmd_dir = root / ".claude" / "commands"
    if not cmd_dir.exists():
        return {k: False for k in EXPECTED_COMMANDS}
    existing = {f.name for f in cmd_dir.iterdir()}
    return {k: k in existing for k in EXPECTED_COMMANDS}


def audit_bmad_stubs(root: Path) -> dict:
    """Audit BMAD skill stubs (.claude/skills/bmad-*/).
    These come from npx bmad-method install + make bmad-trim-apply.
    They are NOT in .claude/commands/.
    """
    skills_dir = root / ".claude" / "skills"
    if not skills_dir.exists():
        return {k: False for k in EXPECTED_BMAD_STUBS}
    existing = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    return {k: k in existing for k in EXPECTED_BMAD_STUBS}


def audit_agents(root: Path) -> dict:
    """Audit .claude/agents/. Only security-reviewer.md should be here."""
    agents_dir = root / ".claude" / "agents"
    if not agents_dir.exists():
        return {k: False for k in EXPECTED_AGENTS}
    existing = {f.name for f in agents_dir.iterdir()}
    return {k: k in existing for k in EXPECTED_AGENTS}


def audit_stale_agents(root: Path) -> list[str]:
    """Find agent files that should NOT exist because other tools own them.
    - developer.md, code-reviewer.md → Superpowers owns these
    - analyst.md, pm.md, architect.md, scrum-master.md → BMAD _bmad/ runtime owns these
    """
    should_not_exist = {
        "developer.md": "Superpowers owns implementation (installed globally via /plugin install)",
        "code-reviewer.md": "Superpowers owns code review (installed globally via /plugin install)",
        "analyst.md": "BMAD owns planning — agent lives in _bmad/, not .claude/agents/",
        "pm.md": "BMAD owns planning — agent lives in _bmad/, not .claude/agents/",
        "architect.md": "BMAD owns planning — agent lives in _bmad/, not .claude/agents/",
        "scrum-master.md": "BMAD owns sprint planning — agent lives in _bmad/, not .claude/agents/",
    }
    agents_dir = root / ".claude" / "agents"
    if not agents_dir.exists():
        return []
    found = []
    for f in agents_dir.iterdir():
        if f.name in should_not_exist:
            found.append(f"{f.name}  ({should_not_exist[f.name]})")
    return found


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
        if any(
            kw in name for kw in ["story", "ticket", "task", "feature", "us-", "story-"]
        ):
            results["orphaned_stories"].append(str(p.relative_to(root)))

    return results


def check_superpowers_conflict(root: Path) -> bool:
    """Check if post_tool_lint.py hook is present alongside Superpowers.
    Superpowers already runs tests per subtask — double-running is wasteful.
    """
    hooks_dir = root / ".claude" / "hooks"
    has_lint_hook = (hooks_dir / "post_tool_lint.py").exists()
    claude_md = (
        (root / "CLAUDE.md").read_text(errors="replace")
        if (root / "CLAUDE.md").exists()
        else ""
    )
    has_superpowers = "superpowers" in claude_md.lower()
    return has_lint_hook and has_superpowers


# ── scaffold functions ────────────────────────────────────────────────────────

# Hooks scaffold our .py hooks (matching agentic-base template convention).
# Shell-based (.sh) hooks are NOT used — Python hooks give richer logic,
# better error messages, and cross-platform consistency.
HOOK_TEMPLATES = {
    "pre_tool_dangerous.py": '#!/usr/bin/env python3\n"""\nPreToolUse hook — block dangerous bash commands before execution.\n\nTriggered by: Bash tool calls.\nPurpose: Deterministic guardrail. No LLM judgment — pure pattern matching.\nSource: Agentic Engineering guide (Layer 4: Deterministic Hooks)\n\nexit 1 → block and show reason to agent so it can correct itself.\n"""\n\nimport json\nimport re\nimport sys\n\n# (pattern, human-readable reason)\nDANGEROUS_PATTERNS = [\n    (r"\\brm\\s+-rf\\s+/", "rm -rf / is not allowed"),\n    (r"\\brm\\s+--no-preserve-root", "rm --no-preserve-root is not allowed"),\n    (r"\\bgit\\s+push\\s+.*--force\\b(?!-with-lease)", "force push without --force-with-lease is not allowed"),\n    (r"\\bgit\\s+push\\s+-f\\b", "force push (-f) is not allowed — use --force-with-lease"),\n    (r"\\bchmod\\s+-R\\s+777\\b", "chmod -R 777 is not allowed"),\n    (r"\\bdd\\s+if=.*of=/dev/(sd|hd|nvme)", "writing directly to block device is not allowed"),\n    (r"\\bcurl\\s+.*\\|\\s*(ba)?sh\\b", "piping curl to shell is not allowed"),\n    (r"\\bwget\\s+.*\\|\\s*(ba)?sh\\b", "piping wget to shell is not allowed"),\n    (r":\\(\\)\\s*\\{.*\\};\\s*:", "fork bomb pattern detected"),\n    (r"\\b(DROP|TRUNCATE)\\s+(TABLE|DATABASE)\\b", "destructive SQL statement — use a migration"),\n]\n\n\ndef main() -> None:\n    """Check bash command against dangerous pattern list."""\n    payload = json.loads(sys.stdin.read())\n\n    if payload.get("tool_name") != "Bash":\n        return\n\n    command = payload.get("tool_input", {}).get("command", "")\n    if not command:\n        return\n\n    for pattern, reason in DANGEROUS_PATTERNS:\n        if re.search(pattern, command, re.IGNORECASE):\n            print(f"BLOCKED: {reason}", file=sys.stderr)\n            print(f"Command was: {command[:200]}", file=sys.stderr)\n            sys.exit(1)\n\n\nif __name__ == "__main__":\n    main()\n',
    "pre_tool_env_guard.py": '#!/usr/bin/env python3\n"""\nPreToolUse hook — block Claude from reading .env files.\n\nTriggered by: Read, Glob, Grep, LS, Bash tool calls.\nPurpose: Prevent Claude from ingesting real secrets during agentic sessions.\n         Claude should read .env.template (committed, no real values) not .env.\n\nWhy this matters:\n    During long agentic sessions Claude reads many files to build context.\n    If it reads .env it may inadvertently include secrets in its context window,\n    in summaries, in logs, or in generated code. Blocking the read eliminates\n    the risk entirely — Claude doesn\'t need the real values to do its job.\n\nWhat Claude should use instead:\n    - .env.template  — understand what variables exist and their purpose\n    - os.environ / pydantic BaseSettings — reference env vars by name in code\n    - Never hardcode values, never read .env directly\n\nSource: Anthropic free course best practices for agentic security.\n\nexit 1 → block the tool call and explain why.\nexit 0 → allow the tool call to proceed.\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport re\nimport sys\nfrom pathlib import Path\n\n# Files Claude must never read.\n# .env.template is explicitly allowed — it has no real values.\nBLOCKED_FILENAMES = {\n    ".env",\n    ".env.local",\n    ".env.production",\n    ".env.staging",\n    ".env.development",\n    ".env.test",\n    ".env.secrets",\n    ".env.claude",   # generated by configure.py, may contain API URL overrides\n}\n\n# Patterns in Bash commands that would read .env content into Claude\'s context.\n# We want to catch: cat .env, source .env, . .env, grep .env, etc.\nBASH_ENV_READ_PATTERNS = [\n    r"\\bcat\\s+[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",\n    r"\\bsource\\s+[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",\n    r"^\\.\\s+[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",          # POSIX `. .env`\n    r"\\bgrep\\s+.*[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",\n    r"\\bless\\s+[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",\n    r"\\bmore\\s+[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",\n    r"\\bhead\\s+.*[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",\n    r"\\btail\\s+.*[\'\\"]?\\.env[\'\\"]?(?:\\s|$)",\n]\n\n\ndef is_blocked_path(path_str: str) -> bool:\n    """Return True if the path resolves to a blocked .env file."""\n    p = Path(path_str)\n    # Match on filename only — .env in any subdirectory is blocked\n    return p.name in BLOCKED_FILENAMES\n\n\ndef is_blocked_bash(command: str) -> bool:\n    """Return True if the bash command would read a .env file."""\n    for pattern in BASH_ENV_READ_PATTERNS:\n        if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):\n            return True\n    return False\n\n\ndef block(reason: str) -> None:\n    """Print block reason and exit 1."""\n    print(f"BLOCKED: {reason}", file=sys.stderr)\n    print("", file=sys.stderr)\n    print("Claude should not read .env files — they may contain real secrets.", file=sys.stderr)\n    print("Use .env.template to understand available variables (no real values).", file=sys.stderr)\n    print("Reference env vars by name in code: os.environ[\'VAR\'] or pydantic BaseSettings.", file=sys.stderr)\n    sys.exit(1)\n\n\ndef main() -> None:\n    """Check tool call for .env access attempts."""\n    payload = json.loads(sys.stdin.read())\n    tool_name = payload.get("tool_name", "")\n    tool_input = payload.get("tool_input", {})\n\n    # --- File read tools ---\n    if tool_name == "Read":\n        path = tool_input.get("file_path", "") or tool_input.get("path", "")\n        if path and is_blocked_path(path):\n            block(f"Attempted to read \'{Path(path).name}\'")\n\n    # --- Glob / LS — block if pattern would match .env files ---\n    elif tool_name in ("Glob", "LS"):\n        pattern = tool_input.get("pattern", "") or tool_input.get("path", "")\n        # Be conservative: if the glob pattern could match a .env file, block it.\n        # e.g. ".env*", ".*", "**/.env" all warrant blocking.\n        if pattern and re.search(r"(^|/)\\.env", pattern):\n            block(f"Glob/LS pattern \'{pattern}\' could match .env files")\n\n    # --- Grep — block if searching in .env files ---\n    elif tool_name == "Grep":\n        include = tool_input.get("include", "")\n        path = tool_input.get("path", "")\n        if include and is_blocked_path(include):\n            block(f"Grep include pattern targets \'{include}\'")\n        if path and is_blocked_path(path):\n            block(f"Grep path targets \'{Path(path).name}\'")\n\n    # --- Bash — block commands that read .env content ---\n    elif tool_name == "Bash":\n        command = tool_input.get("command", "")\n        if command and is_blocked_bash(command):\n            block("Bash command would read .env file content")\n\n\nif __name__ == "__main__":\n    main()\n',
    "post_tool_secrets.py": '#!/usr/bin/env python3\n"""\nPostToolUse hook — block secrets from being written to any file.\n\nTriggered by: Write, Edit, MultiEdit tool calls.\nPurpose: Defense-in-depth first layer. The Security Reviewer agent\n         catches indirect exposure during formal review — keep both.\nSource: Agentic Engineering guide (Layer 4: Deterministic Hooks)\n\nexit 1 → block the tool call and show the pattern that matched.\n"""\n\nimport json\nimport re\nimport sys\nfrom pathlib import Path\n\n# Patterns that suggest a hardcoded secret.\n# Tuned to avoid false positives on test fixtures and example values.\nSECRET_PATTERNS = [\n    (r\'(?i)(api[_-]?key|apikey)\\s*=\\s*["\\\'][A-Za-z0-9_\\-]{16,}["\\\']\', "API key"),\n    (r\'(?i)(secret[_-]?key|secret)\\s*=\\s*["\\\'][A-Za-z0-9_\\-]{16,}["\\\']\', "Secret key"),\n    (r\'(?i)(password|passwd|pwd)\\s*=\\s*["\\\'][^"\\\']{6,}["\\\']\', "Password"),\n    (r\'(?i)(token)\\s*=\\s*["\\\'][A-Za-z0-9_\\-\\.]{20,}["\\\']\', "Token"),\n    (r\'(?i)(aws_access_key_id)\\s*=\\s*["\\\'][A-Z0-9]{20}["\\\']\', "AWS key"),\n    (r\'(?i)(aws_secret_access_key)\\s*=\\s*["\\\'][A-Za-z0-9/+=]{40}["\\\']\', "AWS secret"),\n    (r\'sk-[A-Za-z0-9]{32,}\', "OpenAI/Anthropic key"),\n]\n\n# Files that are allowed to contain secret-like patterns (e.g., .env.example)\nALLOWED_PATHS = {".env.example", ".env.sample", ".env.template"}\n\n\ndef main() -> None:\n    """Scan newly written file content for secret patterns."""\n    payload = json.loads(sys.stdin.read())\n    tool_name = payload.get("tool_name", "")\n\n    if tool_name not in ("Write", "Edit", "MultiEdit"):\n        return\n\n    tool_input = payload.get("tool_input", {})\n    file_path = tool_input.get("file_path") or tool_input.get("path", "")\n\n    if Path(file_path).name in ALLOWED_PATHS:\n        return\n\n    # Get the content being written\n    content = tool_input.get("content", "") or tool_input.get("new_string", "")\n    if not content:\n        return\n\n    hits = []\n    for pattern, label in SECRET_PATTERNS:\n        if re.search(pattern, content):\n            hits.append(label)\n\n    if hits:\n        print(f"BLOCKED: Possible secret(s) detected: {\', \'.join(hits)}", file=sys.stderr)\n        print("Use environment variables or a secrets manager instead.", file=sys.stderr)\n        print("If this is a false positive, add the pattern to ALLOWED_PATHS.", file=sys.stderr)\n        sys.exit(1)\n\n\nif __name__ == "__main__":\n    main()\n',
    "post_tool_lint.py": '#!/usr/bin/env python3\n"""\nPostToolUse hook — auto-lint after every file write or edit.\n\nTriggered by: Write, Edit, MultiEdit tool calls.\nPurpose: Catch formatting issues immediately, not at commit time.\nSource: Agentic Engineering guide (Layer 4: Deterministic Hooks)\n\nClaude Code hook spec:\n  stdin  → JSON with keys: tool_name, tool_input, tool_response\n  stdout → ignored\n  exit 0 → proceed\n  exit 1 → block + show stderr to agent\n  exit 2 → block silently\n"""\n\nimport json\nimport subprocess\nimport sys\nfrom pathlib import Path\n\n\ndef main() -> None:\n    """Run lint checks on the file that was just written or edited."""\n    payload = json.loads(sys.stdin.read())\n    tool_name = payload.get("tool_name", "")\n\n    if tool_name not in ("Write", "Edit", "MultiEdit"):\n        return\n\n    # Resolve the file path that was touched\n    tool_input = payload.get("tool_input", {})\n    file_path = tool_input.get("file_path") or tool_input.get("path")\n    if not file_path:\n        return\n\n    path = Path(file_path)\n    if not path.exists() or path.suffix != ".py":\n        return\n\n    # Run non-mutating checks so the agent sees failures immediately.\n    # We do NOT auto-fix here — that\'s make fmt\'s job (mutating).\n    # The agent should call `make fmt` if these fail.\n    checks = [\n        ["uv", "run", "black", "--check", str(path)],\n        ["uv", "run", "isort", "--check-only", str(path)],\n    ]\n\n    failed = []\n    for cmd in checks:\n        result = subprocess.run(cmd, capture_output=True, text=True)\n        if result.returncode != 0:\n            failed.append(result.stdout + result.stderr)\n\n    if failed:\n        print("\\n".join(failed), file=sys.stderr)\n        print("Run `make fmt` to auto-fix.", file=sys.stderr)\n        sys.exit(1)\n\n\nif __name__ == "__main__":\n    main()\n',
}


# Only scaffold our implementation commands — BMAD planning commands
# come from npx bmad-method install (as .claude/skills/bmad-*/ stubs),
# NOT from .claude/commands/
COMMAND_TEMPLATES = {
    "implement.md": (
        "# /implement\n"
        "Activate Superpowers TDD for the given story file.\n\n"
        "Usage: `/implement <story-file>`\n\n"
        "Superpowers handles the full workflow automatically:\n"
        "brainstorm → git worktree → write plan → test-first → implement → review\n"
    ),
    "review.md": (
        "# /review\n"
        "Run the security-reviewer agent on the current PR.\n\n"
        "Checks: OWASP Top 10, secrets, CVEs, CLAUDE.md convention compliance.\n"
        "Use for security-sensitive PRs or before merging to main.\n"
    ),
    "commit-push-pr.md": (
        "# /commit-push-pr\n"
        "Stage, commit, push, and open a PR.\n\n"
        "Pre-computes git context. Only proceeds if `make check` passes.\n"
        'Usage: `/commit-push-pr "feat(auth): add JWT validation"` \n'
    ),
}

# Only scaffold our custom agent — Superpowers and BMAD provide the rest.
# Superpowers (global ~/.claude/): developer, code-reviewer
# BMAD (_bmad/ runtime): analyst, pm, architect, scrum-master
AGENT_TEMPLATES = {
    "security-reviewer.md": (
        "# Security Reviewer\n\n"
        "Read-only. Scan for:\n"
        "- OWASP Top 10\n"
        "- Hardcoded secrets / credentials\n"
        "- Known CVEs in dependencies\n"
        "- CWE classifications\n\n"
        "Never modify files. Output: security report with CWE IDs and remediation steps.\n"
    ),
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
    make_file(
        "docs/prd.md",
        "# Product Requirements Document\n\nTODO: Complete with `/prd` command.\n",
    )
    make_file(
        "docs/architecture.md",
        "# Architecture\n\nTODO: Complete with `/architecture` command.\n",
    )

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

    header("4 / HOOKS  (.claude/hooks/*.py)")
    hooks = audit_hooks(root)
    for name, exists in hooks.items():
        desc = EXPECTED_HOOKS[name]
        (ok if exists else missing)(f"{name}  ({desc})")

    header("5 / OUR COMMANDS  (.claude/commands/)")
    cmds = audit_commands(root)
    for name, exists in cmds.items():
        desc = EXPECTED_COMMANDS[name]
        (ok if exists else missing)(f"{name}  —  {desc}")

    header("5b / BMAD SKILL STUBS  (.claude/skills/bmad-*/)")
    info("These come from: npx bmad-method install + make bmad-trim-apply")
    stubs = audit_bmad_stubs(root)
    for name, exists in stubs.items():
        (ok if exists else missing)(f"{name}")
    if not any(stubs.values()):
        info("Run: npx bmad-method install && make bmad-trim-apply")

    header("6 / OUR AGENTS  (.claude/agents/)")
    info("Only security-reviewer.md should be here.")
    info("Superpowers owns: developer, code-reviewer (global ~/.claude/)")
    info("BMAD owns: analyst, pm, architect, scrum-master (_bmad/ runtime)")
    agents = audit_agents(root)
    for name, exists in agents.items():
        desc = EXPECTED_AGENTS[name]
        (ok if exists else missing)(f"{name}  —  {desc}")
    stale = audit_stale_agents(root)
    for item in stale:
        warn(f"REMOVE: {item}")

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
        warn(
            "post_tool_lint.py + Superpowers TDD detected — these may double-run tests."
        )
        info(
            "Superpowers already runs tests per subtask — consider disabling post_tool_lint.py in Superpowers sessions."
        )
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
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to project root (default: current dir)",
    )
    parser.add_argument(
        "--dry", action="store_true", help="Audit only — no files created"
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"{RED}Error:{RESET} Path does not exist: {root}")
        sys.exit(1)

    print(f"\n{BOLD}Agentic Engineering Migration{RESET}")
    print(f"Project: {CYAN}{root}{RESET}")
    print(
        f"Mode:    {'DRY RUN (audit only)' if args.dry else 'SCAFFOLD (create missing)'}"
    )

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
    print(
        "  2. Populate docs/prd.md and docs/architecture.md (or use /prd, /architecture)"
    )
    print("  3. Run `/gate-check` to validate PRD ↔ architecture consistency")
    print("  4. Move story files into stories/draft/ and review with /sprint-planning")
    print(
        "  5. For the CLAUDE.md judgment work, use the migration SKILL.md in Claude Code\n"
    )


if __name__ == "__main__":
    main()
