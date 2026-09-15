"""Diagnose an installed factory offline; leave freshness to explicit Graft check."""

import json
import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import graft
from .config import load_config, object_value, read_text, safe_path
from .doctor_wiring import (
    check_commands,
    check_evals,
    check_git,
    check_hooks,
    external_tool,
)
from .installation import check_state, installation_version
from .ownership import hash_history


@dataclass(frozen=True)
class Diagnostic:
    """One stable installation finding and the action needed to resolve it."""

    code: str
    severity: str
    path: str | None
    explanation: str
    remediation: str


def check_manifest(root: Path) -> None:
    """Validate distribution metadata without rejecting project customizations."""
    data = object_value(
        json.loads(read_text(root, ".harness/template-manifest.json")), "manifest"
    )
    if "template_version" not in data or installation_version(root) is None:
        raise ValueError("manifest template_version is missing")
    files = object_value(data.get("files"), "manifest.files")
    if not files:
        raise ValueError("manifest.files must not be empty")
    if data.get("ownership_version") == 1:
        check_state(root, data)
    elif "ownership_version" in data:
        raise ValueError("Unsupported ownership_version")
    for name, entry in files.items():
        entry = object_value(entry, f"files.{name}")
        if data.get("ownership_version") == 1:
            # Explicitly project-owned inventory is not an installation requirement.
            if entry.get("ownership", {}).get("mode") == "preserve":
                continue
        # The template example is distributed, but doctor never opens env files.
        if name == ".env.template":
            example = root / name
            if example.is_symlink() or not example.is_file():
                raise ValueError(
                    "Missing regular .env.template example; restore it from the template"
                )
        else:
            path = safe_path(root, name)
            if data.get("ownership_version") != 1 and not path.is_file():
                raise ValueError(f"Missing installed manifest file: {name}")
        entry = object_value(entry, f"files.{name}")
        hash_history(entry, name)
    load_config(root)


def check_structure(root: Path) -> None:
    """Require the shipped runtime and lifecycle structure on ordinary installs."""
    for name in (
        ".claude/commands",
        ".claude/hooks",
        ".claude/agents",
        ".claude/skills",
        ".harness/factory",
        ".harness/scripts/lib",
        ".harness/evals/cases",
        "openspec/specs",
        "openspec/changes",
        "docs/decisions",
    ):
        if not safe_path(root, name).is_dir():
            raise ValueError(f"Missing required directory: {name}")
    for name in (
        "CLAUDE.md",
        "HARNESS.md",
        "FACTORY.md",
        "REVIEW.md",
        "Makefile",
        ".harness/factory/cli.py",
        ".harness/factory/doctor.py",
        ".harness/scripts/cmd_check.sh",
        ".harness/scripts/lib/run_quiet.sh",
    ):
        read_text(root, name)
    for name in ("factory", ".harness/bin/graft"):
        path = safe_path(root, name)
        if not path.is_file() or not path.stat().st_mode & 0o111:
            raise ValueError(
                f"{name} must exist and be executable; restore file and chmod +x"
            )


def check_openspec(root: Path) -> None:
    """Check one top-level schema name in the supported inline YAML form."""
    config = read_text(root, "openspec/config.yaml")
    values = re.findall(r"^schema:[ \t]*([^\r\n]*)", config, re.MULTILINE)
    # This is a bounded wiring check, not a YAML loader. Never let whitespace
    # consume the next key, or treat YAML comments/nulls/collections as names.
    name = r"[A-Za-z_][A-Za-z0-9_.-]*"
    match = (
        re.fullmatch(
            rf"(?:({name})|\"({name})\"|'({name})')[ \t]*(?:[ \t]#[^\r\n]*)?",
            values[0],
        )
        if len(values) == 1
        else None
    )
    if not match or (match[1] and match[1].lower() in {"null", "true", "false"}):
        raise ValueError(
            "openspec/config.yaml requires exactly one nonempty inline schema name "
            "(letters/underscore, then letters, digits, underscores, dots or hyphens), "
            "optionally quoted; use schema: spec-driven or your custom schema name. "
            "Block scalars, aliases and other YAML forms are unsupported by doctor."
        )


def check_navigation(root: Path) -> None:
    """Inspect the pinned dependency and local wiring without invoking Graft."""
    graft.application_roots(root)
    node = external_tool(root, "node")
    # Do not inherit NODE_OPTIONS or dotenv/preload settings into this probe.
    result = subprocess.run(
        [node, "--version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env={"PATH": os.defpath},
    )
    match = re.fullmatch(r"v(\d+)\.(\d+)\.\d+\s*", result.stdout)
    if result.returncode or not match or tuple(map(int, match.groups())) < (22, 12):
        raise ValueError("Node.js 22.12+ required; repair the Node runtime")
    package = object_value(
        json.loads(read_text(root, f"{graft.PACKAGE}/package.json")), "Graft package"
    )
    expected = object_value(package.get("dependencies"), "Graft dependencies").get(
        "@nanonets/graft"
    )
    if expected != "0.18.0":
        raise ValueError(
            "Expected tested Graft pin 0.18.0; restore the shipped package manifest"
        )
    lock = object_value(
        json.loads(read_text(root, f"{graft.PACKAGE}/package-lock.json")), "Graft lock"
    )
    packages = object_value(lock.get("packages"), "lock packages")
    locked = object_value(packages.get("node_modules/@nanonets/graft"), "locked Graft")
    installed = f"{graft.PACKAGE}/node_modules/@nanonets/graft"
    actual = object_value(
        json.loads(read_text(root, f"{installed}/package.json")), "installed Graft"
    )
    if locked.get("version") != expected or actual.get("version") != expected:
        raise ValueError(
            "Graft package, lock and installed versions disagree; run make graft-install"
        )
    read_text(root, f"{installed}/dist/cli.js")
    if not read_text(root, graft.SKILL).strip():
        raise ValueError("Graft skill is empty; restore it with make graft-install")
    launcher = read_text(root, ".harness/bin/graft")
    if not re.search(
        r'^[ \t]*exec .*"\$root/factory"[ \t]+navigation(?:[ \t]|$)',
        launcher,
        re.MULTILINE,
    ):
        raise ValueError("Graft launcher must delegate to factory navigation")
    ignores = read_text(root, ".gitignore").splitlines()
    if missing := set(graft.IGNORES) - set(ignores):
        raise ValueError(
            f"Missing Graft cache ignore rules: {', '.join(sorted(missing))}"
        )


def diagnose(root: Path) -> list[Diagnostic]:
    """Collect independent errors so one broken subsystem does not hide the rest."""
    checks: list[tuple[str, str, Callable[[Path], None], str]] = [
        (
            "manifest",
            ".harness/template-manifest.json",
            check_manifest,
            "Restore valid installed metadata/configuration; on the starter run make manifest after corrections.",
        ),
        (
            "structure",
            ".harness",
            check_structure,
            "Restore missing factory files/directories from the installed template.",
        ),
        (
            "hooks",
            ".claude/settings.json",
            check_hooks,
            "Restore the shipped protection hooks and their event/tool matchers in settings.json.",
        ),
        (
            "commands",
            ".claude/commands",
            check_commands,
            "Restore command preamble wiring and executable statusline permissions.",
        ),
        (
            "openspec",
            "openspec/config.yaml",
            check_openspec,
            "Initialize OpenSpec or restore its schema configuration; preserve existing specs.",
        ),
        (
            "git-protections",
            ".gitignore",
            check_git,
            "Repair Git/ignore rules; keep secret files ignored and .env.template trackable.",
        ),
        (
            "navigation",
            ".harness/graft",
            check_navigation,
            "Check application_roots, install Node.js 22.12+, then run make graft-install.",
        ),
        (
            "evals",
            ".harness/evals/cases",
            check_evals,
            "Restore the eval runner and valid cases with unique ids and nonempty bodies.",
        ),
    ]
    findings = []
    for code, path, check, remediation in checks:
        try:
            check(root)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            findings.append(Diagnostic(code, "ERROR", path, str(exc), remediation))
    findings.append(
        Diagnostic(
            "navigation-freshness",
            "INFO",
            None,
            "Freshness not assessed: doctor is offline and never invokes Graft.",
            "Run .harness/bin/graft check separately; run .harness/bin/graft build if structural preparation is needed.",
        )
    )
    return findings


def run(root: Path) -> int:
    """Print actionable findings and fail only for installation errors."""
    findings = diagnose(root)
    for finding in findings:
        location = f" ({finding.path})" if finding.path else ""
        print(
            f"{finding.severity} {finding.code}{location}: {finding.explanation}\n  {finding.remediation}"
        )
    errors = sum(f.severity == "ERROR" for f in findings)
    print(f"{'✗' if errors else '✓'} doctor: {errors} installation error(s)")
    return int(errors > 0)
