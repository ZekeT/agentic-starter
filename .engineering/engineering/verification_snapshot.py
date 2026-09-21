"""Bind verification to explicit scope and observable repository inputs."""

import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from .config import safe_path
from .growth import merge_base
from .ownership import digest, encoded, json_object
from .verification_checkout import proposed_files, temporary_checkout
from .verification_inputs import STATE, paths_from_git, source_path, strings


def read_plan(root: Path, name: str) -> dict[str, Any]:
    """Validate explicit check/version commands before any execution."""
    plan = json_object(safe_path(root, name).read_bytes())
    validate_plan(root, plan)
    return plan


def validate_plan(root: Path, plan: dict[str, Any]) -> None:
    """Apply the same contract to new plans and stored evidence."""
    fields = {
        "base",
        "requirement",
        "paths",
        "checks",
        "tools",
        "inputs",
        "security_required",
        "security_reason",
    }
    if set(plan) != fields:
        raise ValueError(f"Plan requires exactly: {sorted(fields)}")
    for field in ("base", "requirement", "security_reason"):
        if not isinstance(plan[field], str) or not plan[field].strip():
            raise ValueError(f"{field}: nonempty text required")
    if plan["base"].startswith("-"):
        raise ValueError("Invalid base reference")
    if type(plan["security_required"]) is not bool:
        raise ValueError("security_required must be boolean")
    for field in ("paths", "inputs"):
        values = strings(plan[field], field, empty=field == "inputs")
        if len(values) != len(set(values)):
            raise ValueError(f"{field}: duplicate paths")
        for path in values:
            source_path(root, path)
            if path == STATE or path.startswith(STATE + "/"):
                raise ValueError("Verification bookkeeping cannot be a source input")
    for field in ("checks", "tools"):
        if not isinstance(plan[field], list) or not plan[field]:
            raise ValueError(f"{field}: nonempty argv list required")
        for command in plan[field]:
            strings(command, field)
        if len({tuple(c) for c in plan[field]}) != len(plan[field]):
            raise ValueError(f"{field}: duplicate commands")
    required = [["make", "check"]]
    if any(p.startswith(".engineering/") for p in plan["paths"]):
        required += [["make", "engineering-test"], ["make", "engineering-evals"]]
    if any(command not in plan["checks"] for command in required):
        raise ValueError(f"Required checks missing: {required}")


def repository_inputs(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Snapshot the baseline plus intended working content, excluding unrelated edits."""
    baseline = merge_base(root, plan["base"])
    committed = paths_from_git(
        root, "diff", "--name-only", "--no-renames", "-z", baseline, "HEAD", "--"
    )
    if omitted := committed - set(plan["paths"]):
        raise ValueError(f"Committed PR changes missing from scope: {sorted(omitted)}")
    if paths_from_git(root, "ls-files", "--unmerged", "-z"):
        raise ValueError("Resolve unmerged entries before verification")

    proposed = proposed_files(root, baseline, plan)
    helper = Path(__file__).resolve().parents[1] / "scripts/lib/change.sh"
    resolved = subprocess.run(
        [
            "bash",
            "-c",
            '. "$1"; git rev-parse --verify "$(base_ref)^{commit}"',
            "verification",
            str(helper),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        env={**os.environ, "ENGINEERING_BASE_BRANCH": plan["base"]},
        check=True,
    ).stdout.strip()
    return {"base": baseline, "base_tip": resolved, "files": proposed}


def run_command(root: Path, command: list[str], *, timeout: int) -> dict[str, Any]:
    """Execute an explicitly supplied argv without a shell or implicit installation."""
    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"},
    )
    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def snapshot(root: Path, plan: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Probe declared versions and detect changes during probing, not just HEAD."""
    before = repository_inputs(root, plan)

    with temporary_checkout(root, before, plan) as checkout:
        tools = [
            run_command(checkout, command, timeout=15) for command in plan["tools"]
        ]
    if any(result["exit_code"] for result in tools):
        raise ValueError(
            "A declared tool/version probe failed; verification is incomplete"
        )
    if before != repository_inputs(root, plan):
        raise ValueError("Repository inputs changed during version probes")
    inputs = {
        **before,
        "plan": plan,
        "tools": tools,
        "root": str(root.resolve()),
        "runtime": platform.python_version(),
    }
    return str(digest(encoded(inputs))), inputs
