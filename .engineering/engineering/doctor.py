"""Diagnose installation integrity offline, without evaluating development work."""

import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import graft
from .config import load_config, read_text, safe_path
from .doctor_wiring import check_git, check_hooks, external_tool
from .installation import MANIFEST_PATH, check_state
from .ownership import json_object, read_bytes
from .registry import installed_status, registry, state
from .settings import load


@dataclass(frozen=True)
class Diagnostic:
    """A stable category, affected path, and concrete remediation."""

    code: str
    severity: str
    path: str
    explanation: str
    remediation: str


def structure(root: Path) -> None:
    """Check portable policy and the Claude adapter without running project code."""
    if sys.version_info < (3, 12):  # noqa: UP036
        raise ValueError("Python 3.12+ required")
    for name in (
        "ENGINEERING.md",
        "CLAUDE.md",
        "AGENTS.md",
        "REVIEW.md",
        "Makefile",
        ".engineering/engineering/cli.py",
        ".engineering/scripts/cmd_check.sh",
    ):
        read_text(root, name)
    for name in ("engineering", ".engineering/bin/graft"):
        if not safe_path(root, name).stat().st_mode & 0o111:
            raise ValueError(f"{name}: chmod +x required")
    for name in ("maintainability-reviewer", "verifier", "security-reviewer"):
        content = read_text(root, f".claude/agents/{name}.md")
        if "readonly: true" not in content:
            raise ValueError(f"{name}: restore read-only definition")
    for name in ("review", "ship"):
        read_text(root, f".claude/commands/{name}.md")
    if not re.search(r"^check\s*:", read_text(root, "Makefile"), re.MULTILINE):
        raise ValueError("Makefile must define the project's canonical check target")


def configuration(root: Path) -> None:
    """Validate project policy, scope and the upstream tracker configuration pointer."""
    config = load(root)
    load_config(root)
    graft.application_roots(root)
    read_text(
        root,
        config.get("tracker", {}).get("configuration", "docs/agents/issue-tracker.md"),
    )


def metadata(root: Path) -> None:
    """Validate bookkeeping without requiring pristine customized files."""
    manifest = json_object(read_bytes(root, MANIFEST_PATH) or b"{}")
    check_state(root, manifest)
    for name, entry in manifest["files"].items():
        if entry["ownership"]["mode"] != "preserve" and read_bytes(root, name) is None:
            raise ValueError(f"Managed file missing: {name}")
    state(root)
    base = safe_path(root, ".engineering/state/migrations")
    if base.exists():
        from .migrate.common import read_metadata

        for path in base.glob("*.json"):
            read_metadata(root, path.relative_to(root).as_posix())
    overlays = safe_path(root, ".engineering/overlays")
    if overlays.exists():
        raise ValueError(
            "No overlays are shipped; reconcile orphaned local overlays explicitly"
        )


def navigation(root: Path) -> None:
    """Check pin/lock/launcher wiring, never graph freshness or model credentials."""
    node = external_tool(root, "node")
    version = subprocess.run(
        [node, "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        env={"PATH": os.defpath},
        check=False,
    )
    match = re.fullmatch(r"v(\d+)\.(\d+)\.\d+\s*", version.stdout)
    if version.returncode or not match or tuple(map(int, match.groups())) < (22, 12):
        raise ValueError("Node.js 22.12+ required; repair the Node runtime")
    rows = registry(root)["dependency"]
    expected = next(row["version"] for row in rows if row["id"] == "graft")
    package = json_object(read_bytes(root, f"{graft.PACKAGE}/package.json") or b"{}")
    lock = json_object(read_bytes(root, f"{graft.PACKAGE}/package-lock.json") or b"{}")
    if (
        package.get("dependencies", {}).get("@nanonets/graft") != expected
        or lock.get("packages", {})
        .get("node_modules/@nanonets/graft", {})
        .get("version")
        != expected
    ):
        raise ValueError(
            "Graft registry/package/lock pins disagree; run engineering deps update graft --apply"
        )
    if '"$root/engineering" navigation' not in read_text(
        root, ".engineering/bin/graft"
    ):
        raise ValueError("Restore Graft launcher delegation to engineering navigation")
    missing = set(graft.IGNORES) - set(read_text(root, ".gitignore").splitlines())
    if missing:
        raise ValueError(f"Missing generated-path ignore rules: {sorted(missing)}")


def diagnose(root: Path) -> list[Diagnostic]:
    """Collect independent installation findings so one failure hides no others."""
    checks: list[tuple[str, str, Callable[[Path], None], str]] = [
        (
            "repository",
            ".gitignore",
            check_git,
            "Initialize Git and restore secret ignore rules.",
        ),
        (
            "structure",
            ".engineering",
            structure,
            "Restore missing managed files and executable permissions.",
        ),
        (
            "configuration",
            ".engineering/config.toml",
            configuration,
            "Repair policy and run /setup-matt-pocock-skills with local Markdown.",
        ),
        (
            "hooks",
            ".claude/settings.json",
            check_hooks,
            "Restore protection hooks and their tool matchers.",
        ),
        (
            "metadata",
            ".engineering/state",
            metadata,
            "Reconcile installation metadata; use engineering update from a verified template.",
        ),
        (
            "navigation",
            graft.PACKAGE,
            navigation,
            "Restore pinned Graft wiring; run engineering deps install --apply.",
        ),
    ]
    findings = []
    for code, path, check, remediation in checks:
        try:
            check(root)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            findings.append(Diagnostic(code, "ERROR", path, str(exc), remediation))
    try:
        data, evidence = registry(root), state(root)["dependencies"]
        for row in data["dependency"]:
            _, health = installed_status(root, row, evidence)
            if health != "OK":
                findings.append(
                    Diagnostic(
                        "dependency",
                        "ERROR" if row["required"] else "WARN",
                        row["id"],
                        health,
                        f"Run engineering deps install {row['id']} --apply (or deps update for an existing pin).",
                    )
                )
    except (OSError, ValueError) as exc:
        findings.append(
            Diagnostic(
                "dependency",
                "ERROR",
                ".engineering/dependencies.toml",
                str(exc),
                "Repair dependency registry/state.",
            )
        )
    return findings


def run(root: Path) -> int:
    """Print stable, actionable errors; project correctness is assessed separately."""
    print("Engineering System Doctor")
    findings = diagnose(root)
    for finding in findings:
        print(
            f"{finding.severity} [{finding.code}] {finding.path}: {finding.explanation}\n  {finding.remediation}"
        )
    errors = sum(f.severity == "ERROR" for f in findings)
    print(
        "Not assessed: project tests, remote dependency freshness, Graft graph freshness, model-backed capabilities."
    )
    print(f"{errors} installation error(s)." if errors else "Healthy.")
    return int(errors > 0)
