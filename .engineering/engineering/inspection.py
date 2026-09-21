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
    ".engineering/manifest.json",
    ".engineering/TEMPLATE_VERSION",
    ".claude/template-version.json",
    ".engineering/state/install.json",
)


def inspect_target(root: Path) -> list[str]:
    """Report evidenced tooling and unresolved configuration, never invent checks."""
    raw = read_bytes(root, "pyproject.toml")
    findings = []
    if raw is None:
        findings.append("No Python project detected; preserve native build tooling")
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
    for name in (
        "go.mod",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
        ".gitlab-ci.yml",
        "bitbucket-pipelines.yml",
    ):
        if read_bytes(root, name) is not None:
            findings.append(f"Existing {name}: preserve native build/CI")
    for name in (
        "docs",
        ".claude/skills",
        ".agents/skills",
        ".github/workflows",
        "openspec",
        ".superpowers",
    ):
        from .config import safe_path

        path = safe_path(root, name)
        if path.exists():
            if not path.is_dir():
                raise ValueError(f"{name} must be a directory")
            findings.append(f"Existing {name}: preserve project-owned content")
    from .migrate.openspec import detected

    if detected(root):
        findings.append(
            "OpenSpec detected. Recommended: ./engineering migrate openspec-project"
        )
    return findings
