"""Inspect supported project signals without executing project tooling."""

import re
import tomllib
from pathlib import Path

from .config import object_value
from .ownership import read_bytes

INSPECTED = (
    "pyproject.toml",
    "uv.lock",
    "Makefile",
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/settings.json",
    ".gitignore",
    "package.json",
    "openspec/config.yaml",
    ".harness/template-manifest.json",
    ".harness/TEMPLATE_VERSION",
    ".claude/template-version.json",
    ".factory/state.json",
)


def inspect_target(root: Path) -> list[str]:
    """Report evidenced tooling and unresolved configuration, never invent checks."""
    raw = read_bytes(root, "pyproject.toml")
    findings = []
    if raw is None:
        findings.append(
            "Unsupported adoption stack: Python pyproject.toml evidence required"
        )
    else:
        project = tomllib.loads(raw.decode())
        object_value(project.get("project", {}), "pyproject.project")
        findings.append(
            f"Python project: requires-python={project.get('project', {}).get('requires-python', 'unspecified')}; preserve application environment"
        )
    make = (read_bytes(root, "Makefile") or b"").decode()
    if re.search(r"^check[ \t]*:", make, re.MULTILINE):
        findings.append("Canonical make check detected; preserve its recipe")
    else:
        findings.append(
            "Unresolved canonical check: define an explicit make check before adoption"
        )
    for name in (
        "CLAUDE.md",
        "AGENTS.md",
        ".claude/settings.json",
        ".gitignore",
        "package.json",
    ):
        if read_bytes(root, name) is not None:
            findings.append(f"Existing {name}: preserve project content")
    workflows = root / ".github/workflows"
    if workflows.exists():
        from .config import safe_path

        path = safe_path(root, ".github/workflows")
        if not path.is_dir():
            raise ValueError(".github/workflows must be a directory")
        findings.append("Existing CI: project-owned; no workflow replacement")
    return findings
