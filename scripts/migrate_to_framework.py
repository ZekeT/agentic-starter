#!/usr/bin/env python3
"""Migrate any existing codebase to the agentic engineering framework.

Copies hooks, commands, agents, config, and scripts from this starter
repository into a target project, then merges Python toolchain configuration
and Makefile targets.

Run from anywhere — the starter root is derived from this file's location:
    python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/target
    python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/target --dry
    python /path/to/agentic-starter/scripts/migrate_to_framework.py /path/to/target --force
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

if sys.version_info < (3, 11):
    print("Error: Python 3.11+ required (tomllib is stdlib from 3.11).")
    sys.exit(1)

# ── source root ───────────────────────────────────────────────────────────────
STARTER_DIR = Path(__file__).parent.parent

# ── files to copy: starter-relative → target-relative ────────────────────────
FILES_TO_COPY: dict[str, str] = {
    ".claude/hooks/pre_tool_dangerous.py": ".claude/hooks/pre_tool_dangerous.py",
    ".claude/hooks/pre_tool_env_guard.py": ".claude/hooks/pre_tool_env_guard.py",
    ".claude/hooks/post_tool_secrets.py": ".claude/hooks/post_tool_secrets.py",
    ".claude/hooks/post_tool_lint.py": ".claude/hooks/post_tool_lint.py",
    ".claude/hooks/stop_story_lifecycle.py": ".claude/hooks/stop_story_lifecycle.py",
    ".claude/hooks/pre_tool_graphify_remind.py": ".claude/hooks/pre_tool_graphify_remind.py",
    ".claude/agents/security-reviewer.md": ".claude/agents/security-reviewer.md",
    # Planning / implementation commands
    ".claude/commands/sprint-planning.md": ".claude/commands/sprint-planning.md",
    ".claude/commands/implement.md": ".claude/commands/implement.md",
    ".claude/commands/review.md": ".claude/commands/review.md",
    ".claude/commands/commit-push-pr.md": ".claude/commands/commit-push-pr.md",
    ".claude/commands/dev-story.md": ".claude/commands/dev-story.md",
    ".claude/settings.json": ".claude/settings.json",
    "config/models.json": "config/models.json",
    "scripts/configure.py": "scripts/configure.py",
    "stories/STORY_TEMPLATE.md": "stories/STORY_TEMPLATE.md",
    # Docs — prd.md/architecture.md are placeholders until planning fills them in
    "docs/SETUP.md": "docs/SETUP.md",
    "docs/coding-standards.md": "docs/coding-standards.md",
    "docs/local-models.md": "docs/local-models.md",
    "docs/prd.md": "docs/prd.md",
    "docs/architecture.md": "docs/architecture.md",
}

# ── our skills to copy whole, starter-relative dir names ─────────────────────
SKILL_DIRS_TO_COPY: list[str] = [
    "rescan-docs",
    "setup-base",
    "setup-migrate",
    "setup-update",
    "graphify",
]

_SKILL_COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")

# ── directories to create ─────────────────────────────────────────────────────
DIRS_TO_CREATE: list[str] = [
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
    "config",
    "scripts",
    "graphify-out",
]

# Directories that get a .gitkeep so git tracks them
_GITKEEP_DIRS: frozenset[str] = frozenset(
    {
        "stories/draft",
        "stories/ready",
        "stories/in-progress",
        "stories/review",
        "stories/done",
        "graphify-out",
    }
)

# ── tech stack indicators ─────────────────────────────────────────────────────
_STACK_INDICATORS: list[tuple[str, str]] = [
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("requirements.txt", "python"),
    ("package.json", "javascript"),
    ("go.mod", "go"),
    ("Cargo.toml", "rust"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
    ("Gemfile", "ruby"),
    ("global.json", "dotnet"),
]

# ── pyproject.toml tool sections to append if missing ─────────────────────────
PYPROJECT_TOOL_SECTIONS: dict[str, str] = {
    "tool.black": (
        "# --- Formatter ---\n"
        "[tool.black]\n"
        "line-length = 88\n"
        'target-version = ["py311"]\n'
    ),
    "tool.isort": (
        "# --- Import sorter (black-compatible) ---\n"
        "[tool.isort]\n"
        'profile = "black"\n'
        "line_length = 88\n"
    ),
    "tool.mypy": (
        "# --- Type checker ---\n"
        "[tool.mypy]\n"
        'python_version = "3.11"\n'
        "strict = true\n"
        "ignore_missing_imports = true\n"
    ),
    "tool.interrogate": (
        "# --- Docstring coverage ---\n"
        "[tool.interrogate]\n"
        "ignore-init-method = true\n"
        "ignore-init-module = true\n"
        "ignore-magic = true\n"
        "ignore-semiprivate = false\n"
        "ignore-private = false\n"
        "fail-under = 80\n"
        "verbose = 1\n"
        "quiet = false\n"
        "color = true\n"
    ),
    "tool.pytest": (
        "# --- Test runner ---\n"
        "[tool.pytest.ini_options]\n"
        'testpaths = ["tests"]\n'
        'addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"\n'
        "\n"
        "[tool.coverage.run]\n"
        'source = ["src"]\n'
        'omit = ["tests/*"]\n'
    ),
}

# ── Makefile ──────────────────────────────────────────────────────────────────
MAKEFILE_MARKER = "# ---- Agentic Engineering (added by migrate_to_framework.py) ----"

MAKEFILE_TARGET_BLOCKS: dict[str, str] = {
    "install": "install:\n\tuv sync --all-extras\n",
    "fmt": (
        "fmt:\n"
        "\tuv run autoflake --remove-all-unused-imports"
        " --remove-unused-variables \\\n"
        "\t\t--in-place --recursive $(SRC) tests\n"
        "\tuv run isort $(SRC) tests\n"
        "\tuv run black $(SRC) tests\n"
    ),
    "lint": (
        "lint:\n"
        "\tuv run black --check $(SRC) tests\n"
        "\tuv run isort --check-only $(SRC) tests\n"
        "\tuv run interrogate $(SRC)\n"
        "\tuv run mypy $(SRC)\n"
    ),
    "test": "test:\n\tuv run pytest\n",
    "check": "check: fmt lint test\n",
    "configure": (
        "configure:\n"
        "\tuv run python scripts/configure.py"
        " $(if $(PROFILE),--profile $(PROFILE),)\n"
    ),
    "configure-show": "configure-show:\n\tuv run python scripts/configure.py --show\n",
    "configure-list": "configure-list:\n\tuv run python scripts/configure.py --list\n",
    "setup-hooks": (
        "setup-hooks:\n"
        '\t@echo "Hooks live in .claude/hooks/ — Claude Code loads them automatically."\n'
    ),
    "clean": (
        "clean:\n"
        '\tfind . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true\n'
        '\tfind . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true\n'
        '\tfind . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true\n'
        '\t@echo "Cleaned."\n'
    ),
}

_REQUIRED_DEV_DEPS: list[str] = [
    "black>=24.0.0",
    "isort>=5.13.0",
    "autoflake>=2.3.0",
    "interrogate>=1.7.0",
    "mypy>=1.10.0",
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
]

# ── colour helpers ────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _ok(msg: str) -> None:
    """Print a success line."""
    print(f"  {GREEN}✓{RESET}  {msg}")


def _warn(msg: str) -> None:
    """Print a warning line."""
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def _info(msg: str) -> None:
    """Print an info line."""
    print(f"  {CYAN}→{RESET}  {msg}")


def _header(msg: str) -> None:
    """Print a bold section header."""
    print(f"\n{BOLD}{msg}{RESET}\n{'─' * 60}")


# ── data types ────────────────────────────────────────────────────────────────


@dataclass
class AuditResult:
    """Result of auditing the target project before migration."""

    target: Path
    is_git_repo: bool
    tech_stacks: list[str]
    has_claude_setup: bool
    existing_claude_files: set[str]
    has_pyproject: bool
    has_makefile: bool
    has_env_template: bool
    has_claude_md: bool
    missing_dirs: list[str]
    files_to_copy: list[str]
    files_to_skip: list[str]
    skill_dirs_to_copy: list[str]
    skill_dirs_to_skip: list[str]


@dataclass
class MigrationReport:
    """Record of every change made during migration."""

    timestamp: str
    starter_version: str
    target: str
    tech_stacks: list[str]
    dirs_created: list[str] = field(default_factory=list)
    copied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    skill_dirs_copied: list[str] = field(default_factory=list)
    skill_dirs_skipped: list[str] = field(default_factory=list)
    pyproject_sections_added: list[str] = field(default_factory=list)
    pyproject_deps_to_add_manually: list[str] = field(default_factory=list)
    makefile_targets_added: bool = False
    env_template_created: bool = False
    claude_md_created: bool = False


# ── validation ────────────────────────────────────────────────────────────────


def validate_target(target: Path) -> None:
    """Raise SystemExit if target is not a valid directory.

    Args:
        target: Resolved path to the target project root.
    """
    if not target.exists():
        print(f"{RED}Error:{RESET} Path does not exist: {target}")
        sys.exit(1)
    if not target.is_dir():
        print(f"{RED}Error:{RESET} Not a directory: {target}")
        sys.exit(1)


def is_inside_starter(target: Path, starter: Path) -> bool:
    """Return True if target is inside or equal to the starter repo.

    Args:
        target: The target project path.
        starter: The starter repo root.

    Returns:
        True if target is the starter itself or a subdirectory of it.
    """
    try:
        target.relative_to(starter)
        return True
    except ValueError:
        return False


# ── audit ─────────────────────────────────────────────────────────────────────


def detect_git_repo(target: Path) -> bool:
    """Return True if target contains a .git directory.

    Args:
        target: The project root to check.

    Returns:
        True if .git exists.
    """
    return (target / ".git").is_dir()


def detect_tech_stacks(target: Path) -> list[str]:
    """Detect which language ecosystems are present in the target.

    Args:
        target: The project root to scan.

    Returns:
        Ordered list of detected stack names, deduplicated.
    """
    seen: set[str] = set()
    stacks: list[str] = []
    for filename, stack in _STACK_INDICATORS:
        if stack not in seen and (target / filename).exists():
            seen.add(stack)
            stacks.append(stack)
    return stacks


def detect_existing_files(target: Path) -> set[str]:
    """Return relative POSIX paths of all files matching FILES_TO_COPY destinations.

    Args:
        target: The project root.

    Returns:
        Set of relative path strings that already exist in the target.
    """
    existing: set[str] = set()
    for dst_rel in FILES_TO_COPY.values():
        if (target / dst_rel).exists():
            existing.add(dst_rel)
    return existing


def audit_target(target: Path, starter: Path) -> AuditResult:
    """Run all audit checks and return a structured result.

    Args:
        target: The target project root.
        starter: The starter repo root.

    Returns:
        AuditResult populated with all detected state.
    """
    existing_files = detect_existing_files(target)

    files_to_copy = [dst for dst in FILES_TO_COPY.values() if dst not in existing_files]
    files_to_skip = [dst for dst in FILES_TO_COPY.values() if dst in existing_files]
    missing_dirs = [d for d in DIRS_TO_CREATE if not (target / d).is_dir()]

    skill_dirs_to_copy = [
        name
        for name in SKILL_DIRS_TO_COPY
        if not (target / ".claude" / "skills" / name).is_dir()
    ]
    skill_dirs_to_skip = [
        name for name in SKILL_DIRS_TO_COPY if name not in skill_dirs_to_copy
    ]

    claude_dir = target / ".claude"
    existing_claude = (
        {
            str(p.relative_to(target).as_posix())
            for p in claude_dir.rglob("*")
            if p.is_file()
        }
        if claude_dir.is_dir()
        else set()
    )

    return AuditResult(
        target=target,
        is_git_repo=detect_git_repo(target),
        tech_stacks=detect_tech_stacks(target),
        has_claude_setup=claude_dir.is_dir(),
        existing_claude_files=existing_claude,
        has_pyproject=(target / "pyproject.toml").exists(),
        has_makefile=(target / "Makefile").exists(),
        has_env_template=(target / ".env.template").exists(),
        has_claude_md=(target / "CLAUDE.md").exists(),
        missing_dirs=missing_dirs,
        files_to_copy=files_to_copy,
        files_to_skip=files_to_skip,
        skill_dirs_to_copy=skill_dirs_to_copy,
        skill_dirs_to_skip=skill_dirs_to_skip,
    )


# ── directory creation ────────────────────────────────────────────────────────


def create_missing_dirs(target: Path, audit: AuditResult, dry: bool) -> list[str]:
    """Create all required directories and .gitkeep files where needed.

    Args:
        target: The target project root.
        audit: Audit result containing missing_dirs.
        dry: If True, log what would be created without writing.

    Returns:
        List of relative paths created or that would be created.
    """
    created: list[str] = []
    for rel in audit.missing_dirs:
        if not dry:
            dir_path = target / rel
            dir_path.mkdir(parents=True, exist_ok=True)
            if rel in _GITKEEP_DIRS:
                gitkeep = dir_path / ".gitkeep"
                if not gitkeep.exists():
                    gitkeep.touch()
        created.append(rel)
    return created


# ── file copying ──────────────────────────────────────────────────────────────


def copy_framework_files(
    target: Path,
    starter: Path,
    force: bool,
    dry: bool,
) -> tuple[list[str], list[str]]:
    """Copy all framework files from starter to target.

    Skips files that already exist unless force is True. Sets executable bit
    on copied Python hook files.

    Args:
        target: The target project root.
        starter: The starter repo root.
        force: Whether to overwrite existing files.
        dry: Whether to log only without writing.

    Returns:
        Tuple of (copied, skipped) relative path lists.
    """
    copied: list[str] = []
    skipped: list[str] = []

    for src_rel, dst_rel in FILES_TO_COPY.items():
        src = starter / src_rel
        dst = target / dst_rel

        if not src.exists():
            _warn(f"Source missing in starter, skipping: {src_rel}")
            continue

        if dst.exists() and not force:
            skipped.append(dst_rel)
            continue

        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if dst.suffix == ".py":
                dst.chmod(dst.stat().st_mode | 0o111)

        copied.append(dst_rel)

    return copied, skipped


def copy_skill_dirs(
    target: Path,
    starter: Path,
    force: bool,
    dry: bool,
) -> tuple[list[str], list[str]]:
    """Copy our whole skill directories from starter to target.

    Skips skill directories that already exist unless force is True.

    Args:
        target: The target project root.
        starter: The starter repo root.
        force: Whether to overwrite existing skill directories.
        dry: Whether to log only without writing.

    Returns:
        Tuple of (copied, skipped) skill directory names.
    """
    copied: list[str] = []
    skipped: list[str] = []

    for name in SKILL_DIRS_TO_COPY:
        src = starter / ".claude" / "skills" / name
        dst = target / ".claude" / "skills" / name

        if not src.is_dir():
            _warn(f"Skill missing in starter, skipping: {name}")
            continue

        if dst.exists() and not force:
            skipped.append(name)
            continue

        if not dry:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=_SKILL_COPY_IGNORE)
            for py_file in dst.rglob("*.py"):
                py_file.chmod(py_file.stat().st_mode | 0o111)

        copied.append(name)

    return copied, skipped


# ── pyproject.toml merging ────────────────────────────────────────────────────


def read_pyproject_tool_keys(pyproject_path: Path) -> set[str]:
    """Return top-level [tool.*] key names already present in pyproject.toml.

    Args:
        pyproject_path: Absolute path to the target's pyproject.toml.

    Returns:
        Set of dotted keys like {"tool.black", "tool.mypy"}.
    """
    data = tomllib.loads(pyproject_path.read_bytes().decode())
    return {f"tool.{k}" for k in data.get("tool", {})}


def build_missing_toml_text(existing: set[str]) -> str:
    """Build TOML text for sections not yet present.

    Args:
        existing: Section keys already in pyproject.toml (e.g. {"tool.black"}).

    Returns:
        TOML string to append, empty if nothing to add.
    """
    blocks = [
        block
        for section_key, block in PYPROJECT_TOOL_SECTIONS.items()
        if section_key not in existing
    ]
    return "\n".join(blocks)


def read_dev_dep_names(pyproject_path: Path) -> set[str]:
    """Return package names from [project.optional-dependencies].dev.

    Args:
        pyproject_path: Path to pyproject.toml.

    Returns:
        Set of lowercased package names stripped of version specifiers.
    """
    data = tomllib.loads(pyproject_path.read_bytes().decode())
    dev_list: list[str] = (
        data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
    )
    return {re.split(r"[>=<!@]", dep)[0].strip().lower() for dep in dev_list}


def patch_pyproject(target: Path, dry: bool) -> tuple[list[str], list[str]]:
    """Merge missing tool sections into pyproject.toml.

    Creates pyproject.toml from the starter template if none exists. When the
    file already exists, appends only missing [tool.*] sections. Missing dev
    dependencies are reported rather than auto-edited to avoid TOML array
    formatting issues.

    Args:
        target: The target project root.
        dry: If True, log without writing.

    Returns:
        Tuple of (sections_added, deps_to_add_manually).
    """
    pyproject_path = target / "pyproject.toml"

    if not pyproject_path.exists():
        if not dry:
            shutil.copy2(STARTER_DIR / "pyproject.toml", pyproject_path)
        _info("Created pyproject.toml from starter template")
        return list(PYPROJECT_TOOL_SECTIONS.keys()), []

    existing = read_pyproject_tool_keys(pyproject_path)
    missing_text = build_missing_toml_text(existing)
    sections_added = [k for k in PYPROJECT_TOOL_SECTIONS if k not in existing]

    if missing_text and not dry:
        with pyproject_path.open("a") as f:
            f.write(f"\n# Added by migrate_to_framework.py\n{missing_text}")

    existing_names = read_dev_dep_names(pyproject_path)
    missing_deps = [
        dep
        for dep in _REQUIRED_DEV_DEPS
        if re.split(r"[>=<!@]", dep)[0].strip().lower() not in existing_names
    ]

    return sections_added, missing_deps


# ── Makefile merging ──────────────────────────────────────────────────────────


def makefile_has_marker(makefile_path: Path) -> bool:
    """Return True if the Makefile already contains our idempotency marker.

    Args:
        makefile_path: Path to the Makefile.

    Returns:
        True if MAKEFILE_MARKER is present.
    """
    return MAKEFILE_MARKER in makefile_path.read_text()


def get_existing_makefile_targets(makefile_path: Path) -> set[str]:
    """Return target names already defined in the Makefile.

    Args:
        makefile_path: Path to the Makefile.

    Returns:
        Set of target name strings found via regex.
    """
    content = makefile_path.read_text()
    return set(re.findall(r"^([\w][\w-]*):", content, re.MULTILINE))


def patch_makefile(target: Path, dry: bool) -> bool:
    """Merge or create Makefile with agentic engineering targets.

    Copies the starter Makefile if none exists. Appends only missing targets
    under a clearly-marked section when one does exist. Idempotent: a second
    run detects the marker and makes no changes.

    Args:
        target: The target project root.
        dry: If True, log without writing.

    Returns:
        True if any changes were made or would be made.
    """
    makefile_path = target / "Makefile"

    if not makefile_path.exists():
        if not dry:
            shutil.copy2(STARTER_DIR / "Makefile", makefile_path)
        _info("Created Makefile from starter")
        return True

    if makefile_has_marker(makefile_path):
        _info("Makefile already contains agentic targets — skipping")
        return False

    existing = get_existing_makefile_targets(makefile_path)
    missing = {
        name: block
        for name, block in MAKEFILE_TARGET_BLOCKS.items()
        if name not in existing
    }

    if not missing:
        _info("All Makefile targets already present — skipping")
        return False

    if not dry:
        header_line = f"\n{MAKEFILE_MARKER}\n\nSRC ?= src\n\n"
        target_text = "\n".join(block for block in missing.values())
        with makefile_path.open("a") as f:
            f.write(header_line + target_text)

    _info(f"Makefile: adding {len(missing)} target(s): {', '.join(missing)}")
    return True


# ── CLAUDE.md generation ──────────────────────────────────────────────────────

_CLAUDE_MD_TEMPLATE = """\
# {project_name}

> Generated by migrate_to_framework.py on {date}.
> Claude reads this file at the start of every session.
> TODO: Fill in all sections marked with TODO below.

---

## Build & Dev Commands

```bash
make install          # install all deps (uv sync)
make fmt              # format: black + isort + autoflake
make lint             # check: black --check, isort --check, interrogate, mypy
make test             # pytest
make check            # fmt + lint + test (run before every commit)
make configure        # apply config/models.json to all agents
```

TODO: Add any project-specific commands here.

---

## Coding Standards

TODO: Add your architecture decisions, language conventions, and style rules.

---

## Security Rules

- Never commit secrets — `post_tool_secrets.py` hook blocks writes containing credentials
- Claude must never read `.env` — use `.env.template` to understand available variables
- Follow OWASP Top 10 patterns
- Validate all external input at system boundaries

---

## Git Strategy

- Branch naming: `feat/story-<id>-<slug>`, `fix/<slug>`, `chore/<slug>`
- Commit format: `type(scope): description` (conventional commits)
- Never force-push to main

---

## Review Checklist

- [ ] `make check` passes (fmt + lint + test)
- [ ] No secrets in diff
- [ ] Acceptance criteria from story file met
- [ ] Tests added for new behaviour

---

## Active Model Config

Run `make configure` after editing `config/models.json` to apply model assignments.
See `config/models.json` for available profiles (anthropic-default, anthropic-budget, ollama-*).

---

## Rules

Add rules here when Claude makes a mistake — this is Claude's persistent memory.
"""

_PYTHON_BLOCK = """\

### Python

- **uv** for dependency management (`uv sync --all-extras`)
- **black** for formatting (line length 88)
- **isort** for import ordering (black-compatible profile)
- **mypy** strict mode — all public functions need type hints
- **interrogate** — 80%+ docstring coverage (Google style)
- **pytest** with 80%+ line coverage (`--cov=src`)
- No bare `except:` — catch the most specific exception type
- Use `pathlib.Path` for file paths, not string concatenation
"""

_JS_BLOCK = """\

### JavaScript/TypeScript

- **eslint** for linting, **prettier** for formatting
- `===` not `==`, `const`/`let` over `var`
- `import type` for type-only imports (TypeScript)
- Arrow functions preferred over `function` declarations
"""


def generate_claude_md_content(project_name: str, stacks: list[str]) -> str:
    """Render CLAUDE.md template with project name and stack-specific snippets.

    Args:
        project_name: The target directory name, title-cased.
        stacks: Detected tech stacks for tailoring the standards section.

    Returns:
        CLAUDE.md content string with TODO markers.
    """
    extra = ""
    if "python" in stacks:
        extra += _PYTHON_BLOCK
    if "javascript" in stacks:
        extra += _JS_BLOCK

    base = _CLAUDE_MD_TEMPLATE.format(
        project_name=project_name,
        date=datetime.now().strftime("%Y-%m-%d"),
    )

    if extra:
        marker = "## Coding Standards\n"
        idx = base.find(marker)
        if idx != -1:
            insert_at = idx + len(marker)
            base = base[:insert_at] + extra + base[insert_at:]

    return base


def create_claude_md(target: Path, stacks: list[str], dry: bool) -> bool:
    """Create CLAUDE.md if it does not already exist.

    Never overwrites an existing CLAUDE.md, even with --force — it is too
    project-specific to safely replace.

    Args:
        target: The target project root.
        stacks: Detected tech stacks for content customization.
        dry: If True, log without writing.

    Returns:
        True if the file was or would be created.
    """
    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        return False

    project_name = target.resolve().name.replace("-", " ").replace("_", " ").title()
    content = generate_claude_md_content(project_name, stacks)

    if not dry:
        claude_md.write_text(content)

    return True


# ── .env.template ─────────────────────────────────────────────────────────────


def create_env_template(target: Path, starter: Path, dry: bool) -> bool:
    """Copy .env.template from starter if the target does not have one.

    Args:
        target: The target project root.
        starter: The starter repo root.
        dry: If True, log without writing.

    Returns:
        True if the file was or would be created.
    """
    dst = target / ".env.template"
    if dst.exists():
        return False

    if not dry:
        shutil.copy2(starter / ".env.template", dst)

    return True


# ── git helper ────────────────────────────────────────────────────────────────


def get_starter_version(starter: Path) -> str:
    """Return the starter's template version.

    Prefers TEMPLATE_VERSION (what setup-update's manifest is keyed on);
    falls back to a git describe string if that file is absent.

    Args:
        starter: The starter repo root.

    Returns:
        The template version string, or "unknown" if neither is available.
    """
    version_file = starter / "TEMPLATE_VERSION"
    if version_file.exists():
        version = version_file.read_text().strip()
        if version:
            return version
    try:
        result = subprocess.run(
            ["git", "-C", str(starter), "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


# ── output helpers ────────────────────────────────────────────────────────────


def print_audit_summary(audit: AuditResult) -> None:
    """Print colour-coded audit results to stdout.

    Args:
        audit: The audit result to display.
    """
    _header("AUDIT")
    _info(f"Target:   {audit.target}")
    _info(f"Stacks:   {', '.join(audit.tech_stacks) or 'none detected'}")

    if audit.is_git_repo:
        _ok("git repo detected")
    else:
        _warn("No .git directory — git init is needed for worktree isolation")

    if audit.has_claude_setup:
        _ok(
            f".claude/ exists ({len(audit.existing_claude_files)} "
            "file(s) already present)"
        )
    else:
        _info(".claude/ will be created")

    _info(
        f"{len(audit.files_to_copy)} file(s) to copy, "
        f"{len(audit.files_to_skip)} already present"
    )
    _info(
        f"{len(audit.skill_dirs_to_copy)} skill(s) to copy, "
        f"{len(audit.skill_dirs_to_skip)} already present"
    )

    if audit.missing_dirs:
        _info(f"{len(audit.missing_dirs)} director(y/ies) to create")

    if not audit.has_env_template:
        _info(".env.template will be copied from starter")

    if audit.has_claude_md:
        _ok("CLAUDE.md found — will not be overwritten")
    else:
        _info("CLAUDE.md will be generated with TODO markers")

    if "python" in audit.tech_stacks:
        if audit.has_pyproject:
            _ok("pyproject.toml found — will merge missing tool sections")
        else:
            _info("Python project without pyproject.toml — will create from template")


def save_migration_report(target: Path, report: MigrationReport) -> None:
    """Write migration report JSON to .claude/migration-report.json.

    Args:
        target: The target project root.
        report: The migration report to serialise.
    """
    report_path = target / ".claude" / "migration-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(asdict(report), indent=2))
    _info(f"Report saved: {report_path.relative_to(target)}")


def save_template_version_stamp(target: Path, report: MigrationReport) -> None:
    """Record the template version baseline for the setup-update skill.

    Args:
        target: The target project root.
        report: The migration report (its starter_version is the baseline).
    """
    stamp_path = target / ".claude" / "template-version.json"
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(
        json.dumps(
            {
                "template_version": report.starter_version,
                "updated_at": report.timestamp,
            },
            indent=2,
        )
        + "\n"
    )


def print_next_steps(audit: AuditResult) -> None:
    """Print the manual steps the user must complete after migration.

    Args:
        audit: The audit result, used to show stack-specific steps.
    """
    _header("NEXT STEPS")
    steps = [
        f"cd {audit.target}",
        "make configure                # patch agents with model assignments",
        "cp .env.template .env         # then fill in real API keys",
    ]
    if "python" in audit.tech_stacks:
        steps += [
            "uv sync --all-extras          # install dev dependencies",
            "make check                    # verify toolchain passes",
        ]
    steps.append(
        "Plan in Claude Code (Superpowers brainstorming), then /sprint-planning"
    )
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")
    print()


# ── orchestration ─────────────────────────────────────────────────────────────


def run_migration(
    target: Path,
    starter: Path,
    audit: AuditResult,
    force: bool,
    dry: bool,
) -> MigrationReport:
    """Execute the full migration and return the report.

    Phases run in dependency order: directories → files → skills → env →
    CLAUDE.md → pyproject → Makefile → report.

    Args:
        target: The target project root.
        starter: The starter repo root.
        audit: Pre-computed audit result.
        force: Whether to overwrite existing copied files.
        dry: Whether to log only without writing.

    Returns:
        Populated MigrationReport.
    """
    report = MigrationReport(
        timestamp=datetime.now().isoformat(),
        starter_version=get_starter_version(starter),
        target=str(target),
        tech_stacks=audit.tech_stacks,
    )

    _header("CREATING DIRECTORIES")
    report.dirs_created = create_missing_dirs(target, audit, dry)
    for d in report.dirs_created:
        _ok(d)
    if not report.dirs_created:
        _info("All directories already exist")

    _header("COPYING FRAMEWORK FILES")
    report.copied, report.skipped = copy_framework_files(target, starter, force, dry)
    for f in report.copied:
        _ok(f"copied:  {f}")
    for f in report.skipped:
        _info(f"skipped: {f}  (exists — use --force to overwrite)")

    _header("COPYING SKILLS  (rescan-docs, setup-*, graphify)")
    report.skill_dirs_copied, report.skill_dirs_skipped = copy_skill_dirs(
        target, starter, force, dry
    )
    for s in report.skill_dirs_copied:
        _ok(f"copied:  .claude/skills/{s}/")
    for s in report.skill_dirs_skipped:
        _info(f"skipped: .claude/skills/{s}/  (exists — use --force to overwrite)")

    _header(".ENV TEMPLATE")
    report.env_template_created = create_env_template(target, starter, dry)
    if report.env_template_created:
        _ok(".env.template created")
    else:
        _info(".env.template already exists — skipped")

    _header("CLAUDE.md")
    report.claude_md_created = create_claude_md(target, audit.tech_stacks, dry)
    if report.claude_md_created:
        _ok("CLAUDE.md created with TODO markers")
    else:
        _info("CLAUDE.md already exists — skipped (never overwritten)")

    if "python" in audit.tech_stacks:
        _header("PYTHON TOOLCHAIN  (pyproject.toml)")
        sections, missing_deps = patch_pyproject(target, dry)
        report.pyproject_sections_added = sections
        report.pyproject_deps_to_add_manually = missing_deps
        for s in sections:
            _ok(f"Added section: [{s}]")
        if not sections:
            _info("All tool sections already present")
        if missing_deps:
            _warn(
                "Dev dependencies not found — add to "
                "[project.optional-dependencies].dev manually:"
            )
            for dep in missing_deps:
                print(f"      {dep}")

    _header("MAKEFILE")
    report.makefile_targets_added = patch_makefile(target, dry)

    if not dry:
        save_migration_report(target, report)
        save_template_version_stamp(target, report)

    return report


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments.

    Returns:
        Parsed namespace with target (str), dry (bool), force (bool).
    """
    parser = argparse.ArgumentParser(
        description="Migrate any codebase to the agentic engineering framework.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/migrate_to_framework.py /path/to/my-project\n"
            "  python scripts/migrate_to_framework.py /path/to/my-project --dry\n"
            "  python scripts/migrate_to_framework.py /path/to/my-project --force\n"
        ),
    )
    parser.add_argument("target", help="Path to the target project directory")
    parser.add_argument(
        "--dry",
        action="store_true",
        help="Audit and preview only — no files created or modified",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing copied files (CLAUDE.md is never overwritten)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: validate, audit, migrate, report."""
    args = parse_args()
    target = Path(args.target).resolve()

    validate_target(target)

    if is_inside_starter(target, STARTER_DIR):
        print(
            f"{RED}Error:{RESET} Target {target} is inside the starter repo. "
            "Run this script against your own project, not the starter itself."
        )
        sys.exit(1)

    print(f"\n{BOLD}Agentic Engineering — Framework Migration{RESET}")
    print(f"Starter: {CYAN}{STARTER_DIR}{RESET}")
    print(f"Target:  {CYAN}{target}{RESET}")
    mode = "DRY RUN (audit only — no writes)" if args.dry else "MIGRATE"
    print(f"Mode:    {mode}")

    audit = audit_target(target, STARTER_DIR)
    print_audit_summary(audit)

    if args.dry:
        _header("DRY RUN COMPLETE")
        _info("Re-run without --dry to apply the changes shown above.")
        return

    run_migration(target, STARTER_DIR, audit, args.force, dry=False)
    print_next_steps(audit)


if __name__ == "__main__":
    main()
