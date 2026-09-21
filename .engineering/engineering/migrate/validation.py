"""Run target-owned finalization gates and bind the successful receipt to bytes."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..ownership import digest, json_object, read_bytes
from .application import fields, sha
from .common import tree
from .openspec import WORKSPACE, integrations

REPORT = f"{WORKSPACE}/validation.json"


def unchanged(root: Path, expected: dict[str, Any]) -> None:
    """Refuse changed outputs or review artifacts, including reappeared sources."""
    for name, fingerprint in expected.items():
        if fingerprint is not None:
            sha(fingerprint)
        if digest(read_bytes(root, name)) != fingerprint:
            raise ValueError(
                f"migration.stale: finalized output or evidence changed: {name}"
            )


def completed(root: Path) -> bool:
    """An exact repeat is a read-only acknowledgement, not a new validation claim."""
    raw = read_bytes(root, REPORT)
    if raw is None:
        return False
    data = fields(
        json_object(raw),
        {"schema_version", "status", "recovery_commit", "files", "checks"},
    )
    if (
        type(data["schema_version"]) is not int
        or data["schema_version"] != 1
        or data["status"] != "PASS"
    ):
        raise ValueError("migration.report: invalid completion receipt")
    if not isinstance(data["files"], dict) or not data["files"]:
        raise ValueError("migration.report: missing output fingerprints")
    unchanged(root, data["files"])
    if tree(root, "openspec") or integrations(root):
        raise ValueError("migration.stale: OpenSpec sources or integration reappeared")
    print(
        "Already finalized; recorded validation passed at application time. No files changed; rerun project checks after subsequent development."
    )
    return True


def run(root: Path) -> list[dict[str, str | int]]:
    """Execute fixed offline checks; no manifest-supplied shell commands."""
    env = {**os.environ, "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}
    launcher = Path(__file__).resolve().parents[3] / "engineering"
    cli = [sys.executable, str(launcher), "--root", str(root)]
    checks: list[dict[str, str | int]] = []
    for label, command in (
        ("doctor", [*cli, "doctor"]),
        ("project check", ["make", "check"]),
        (
            "Graft check (NOT APPLICABLE when no application roots)",
            [*cli, "navigation", "check"],
        ),
    ):
        result = subprocess.run(
            command, cwd=root, env=env, capture_output=True, text=True
        )
        output = result.stdout + result.stderr
        print(f"Validation {label}: {'PASS' if result.returncode == 0 else 'FAIL'}")
        print(output, end="" if output.endswith("\n") else "\n")
        checks.append({"check": label, "exit_code": result.returncode})
        if result.returncode:
            raise ValueError(
                f"migration.validation: {label} failed; migration is not complete"
            )
    return checks
