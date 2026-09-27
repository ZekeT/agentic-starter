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
from .registry import installed_status, registry, required, selected, state
from .settings import graft_navigation, load, provider


def disable(capability: str) -> str:
    """Offer turning an optional capability off as an alternative fix."""
    return f'or disable {capability} with [{capability}] provider = "none" in .engineering/config.toml.'


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
    if not safe_path(root, "engineering").stat().st_mode & 0o111:
        raise ValueError("engineering: chmod +x required")
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
    if graft_navigation(root):
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
    overlays = safe_path(root, ".engineering/overlays")
    if overlays.exists():
        raise ValueError(
            "No overlays are shipped; reconcile orphaned local overlays explicitly"
        )


def navigation(root: Path) -> None:
    """Check pin/lock/launcher wiring, never graph freshness or model credentials."""
    if provider(root, "navigation") != "graft":
        return
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
    if not safe_path(root, ".engineering/bin/graft").stat().st_mode & 0o111:
        raise ValueError(".engineering/bin/graft: chmod +x required")
    missing = set(graft.IGNORES) - set(read_text(root, ".gitignore").splitlines())
    if missing:
        raise ValueError(f"Missing generated-path ignore rules: {sorted(missing)}")


def navigation_state(root: Path) -> list[Diagnostic]:
    """Report disabled or ineffective navigation without failing installation health."""
    if graft_navigation(root):
        return []
    if provider(root, "navigation") == "none":
        return [
            Diagnostic(
                "navigation",
                "INFO",
                ".engineering/config.toml",
                "navigation disabled (provider none); agents search and read source directly",
                'To enable, set [navigation] provider = "graft", then engineering deps install --apply.',
            )
        ]
    return [
        Diagnostic(
            "navigation",
            "WARN",
            ".engineering/config.toml",
            "Graft is selected but navigation.application_roots is empty, so it has no effect",
            f"Add application directories to navigation.application_roots, {disable('navigation')}",
        )
    ]


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
            f"Restore pinned Graft wiring with engineering deps install --apply, {disable('navigation')}",
        ),
    ]
    try:
        load(root)
        policy = True
    except (OSError, ValueError):
        # The configuration check reports invalid policy once; provider-dependent
        # checks cannot be assessed and are skipped rather than repeating it.
        policy = False
        checks = [check for check in checks if check[0] != "navigation"]
    findings = []
    for code, path, check, remediation in checks:
        try:
            check(root)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            findings.append(Diagnostic(code, "ERROR", path, str(exc), remediation))
    if policy:
        findings.extend(navigation_state(root))
    try:
        data, evidence = registry(root), state(root)["dependencies"]
        for row in data["dependency"]:
            if row.get("capability") and not policy or not selected(root, row):
                continue  # Unselected dependencies are left untouched.
            _, health = installed_status(root, row, evidence)
            if health == "OK":
                continue
            fix = f"Run engineering deps install {row['id']} --apply (or deps update for an existing pin)"
            findings.append(
                Diagnostic(
                    "dependency",
                    "ERROR" if required(root, row) else "WARN",
                    row["id"],
                    health,
                    f"{fix}, {disable(row['capability'])}"
                    if row.get("capability")
                    else f"{fix}.",
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
