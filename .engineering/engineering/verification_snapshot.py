"""Bind verification to explicit scope and observable repository inputs."""

import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from .config import safe_path
from .growth import merge_base
from .ownership import digest, encoded, json_object
from .source import git

STATE = ".engineering/state/verification"


def source_path(root: Path, name: str) -> Path:
    """Permit the public environment template, never secret variants or links."""
    if Path(name).name == ".env.template":
        path = safe_path(root, str(Path(name).with_name("template-placeholder")))
        path = path.with_name(".env.template")
        if path.is_symlink():
            raise ValueError(f"Symlink source path is unsupported: {name}")
        return path
    return safe_path(root, name)


def strings(value: Any, label: str, *, empty: bool = False) -> list[str]:
    """Require a list of nonempty strings without coercion."""
    if not isinstance(value, list) or (not value and not empty):
        raise ValueError(f"{label}: expected a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label}: expected nonempty strings")
    return value


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
    if (root / ".engineering/config.toml").is_file():
        from .settings import load

        if load(root).get("navigation", {}).get("application_roots"):
            if [".engineering/bin/graft", "check"] not in plan["checks"]:
                raise ValueError("Configured application roots require Graft check")


def paths_from_git(root: Path, *args: str) -> set[str]:
    """Read NUL-delimited paths without quoting or newline ambiguity."""
    return set(
        filter(None, git(root, *args).decode(errors="surrogateescape").split("\0"))
    )


def files(root: Path, names: set[str]) -> dict[str, Any]:
    """Fingerprint regular bytes and executable bits, including deletions."""
    result: dict[str, Any] = {}
    for name in sorted(names):
        path = source_path(root, name)
        if not path.exists():
            result[name] = None
        elif not path.is_file():
            raise ValueError(f"Unsupported nonregular verification input: {name}")
        else:
            result[name] = {
                "sha256": digest(path.read_bytes()),
                "executable": bool(path.stat().st_mode & 0o111),
            }
    return result


def repository_inputs(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Refuse unrelated changes and snapshot all tracked context plus explicit inputs."""
    baseline = merge_base(root, plan["base"])
    changed = paths_from_git(
        root, "diff", "--name-only", "--no-renames", "-z", baseline, "--"
    )
    changed |= paths_from_git(
        root, "diff", "--cached", "--name-only", "--no-renames", "-z", baseline, "--"
    )
    changed |= paths_from_git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if unrelated := changed - set(plan["paths"]):
        raise ValueError(
            f"Unrelated changes prevent exact-scope verification: {sorted(unrelated)}"
        )
    if paths_from_git(root, "ls-files", "--unmerged", "-z"):
        raise ValueError("Resolve unmerged entries before verification")
    names = paths_from_git(root, "ls-files", "--cached", "-z")
    names |= set(plan["paths"]) | set(plan["inputs"])
    # Installed dependency evidence is ignored local input, not verification output.
    names.add(".engineering/state/dependencies.json")
    if any(name == STATE or name.startswith(STATE + "/") for name in names):
        raise ValueError("Verification records must not be tracked")
    # Index deletion/intent-to-add must not turn index bookkeeping into freshness.
    names |= paths_from_git(root, "ls-tree", "-r", "--name-only", "-z", baseline)
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
    return {"base": baseline, "base_tip": resolved, "files": files(root, names)}


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
    tools = [run_command(root, command, timeout=15) for command in plan["tools"]]
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
