"""Stage unchanged upstream skills through their supported installer."""

import os
import subprocess
from pathlib import Path
from typing import Any

from .config import safe_path


def run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> str:
    """Run an explicit install command with bounded diagnostics."""
    result = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, timeout=300
    )
    if result.returncode:
        raise ValueError(
            f"deps.command: {command[0]} failed: {result.stderr[-2000:] or result.stdout[-2000:]}"
        )
    return result.stdout.strip()


def stage(
    directory: Path, dependency: dict[str, Any], installer: str
) -> dict[str, bytes]:
    """Clone a pinned commit and install selected capabilities in a disposable project."""
    source = directory / "source"
    run(
        [
            "git",
            "clone",
            "--no-checkout",
            "--filter=blob:none",
            "https://github.com/" + dependency["source"] + ".git",
            str(source),
        ],
        directory,
    )
    run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "checkout",
            "--detach",
            dependency["version"],
        ],
        source,
    )
    if run(["git", "rev-parse", "HEAD"], source) != dependency["version"]:
        raise ValueError("deps.pin: checkout does not match registry")
    project = directory / "project"
    project.mkdir()
    run(
        [
            "npx",
            "--yes",
            f"skills@{installer}",
            "add",
            str(source),
            "--skill",
            *dependency["skills"],
            "--agent",
            "claude-code",
            "--copy",
            "--yes",
        ],
        project,
        env={**os.environ, "DISABLE_TELEMETRY": "1"},
    )
    outputs = {}
    for skill in dependency["skills"]:
        base = safe_path(project, f".claude/skills/{skill}")
        if not base.is_dir() or not (base / "SKILL.md").is_file():
            raise ValueError(
                f"deps.contract: upstream installer did not provide {skill}"
            )
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(project).as_posix()
            checked = safe_path(project, relative)
            if checked.is_file():
                outputs[relative] = checked.read_bytes()
    return outputs
