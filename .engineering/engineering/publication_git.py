"""Scoped Git publication with enforced hooks and content checks before transport."""

import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .ownership import digest
from .source import git
from .verification_checkout import baseline_content
from .verification_inputs import paths_from_git, source_path

ORIGINAL_GIT_PARAMETERS = "ENGINEERING_PUBLISH_ORIGINAL_GIT_CONFIG_PARAMETERS"


def validate_tree(root: Path, data: dict[str, Any]) -> None:
    """Compare committed bytes/modes, not merely working bytes or a new commit ID."""
    actual = {
        name: {"sha256": digest(raw), "executable": mode == "100755"}
        for name, mode, raw in baseline_content(root, "HEAD")
    }
    expected = dict(data["inputs"]["files"])
    for name in set(data["inputs"]["plan"]["inputs"]) | {
        ".engineering/state/dependencies.json"
    }:
        if name not in data["inputs"]["plan"]["paths"] and name not in actual:
            expected.pop(name, None)
    expected = {name: value for name, value in expected.items() if value is not None}
    if actual != expected:
        raise ValueError(
            "Committed content differs from accepted content; return to verification"
        )


def commit_scope(root: Path, data: dict[str, Any], title: str) -> None:
    """Commit only accepted working paths while retaining unrelated staged work."""
    try:
        validate_tree(root, data)
        return
    except ValueError:
        pass
    tracked = paths_from_git(root, "ls-files", "--cached", "-z")
    paths = [
        name
        for name in data["inputs"]["plan"]["paths"]
        if name in tracked or source_path(root, name).exists()
    ]
    # Literal pathspecs prevent filenames from selecting additional paths.
    selected = [f":(literal){name}" for name in paths]
    git(root, "add", "--", *selected)
    git(root, "commit", "--only", "-m", title, "--", *selected)


def pre_push_guard(
    root: Path, change: str, head: str, original: str, args: list[str]
) -> int:
    """Run the original hook, then validate content before Git sends any objects."""
    # This process is the temporary guard. Remove only our command-line override
    # before running project hooks or their nested Git commands, preserving the
    # caller's original parameters and all other Git configuration mechanisms.
    parameters = os.environ.pop(ORIGINAL_GIT_PARAMETERS, None)
    if parameters is None:
        os.environ.pop("GIT_CONFIG_PARAMETERS", None)
    else:
        os.environ["GIT_CONFIG_PARAMETERS"] = parameters
    if Path(original).is_file() and os.access(original, os.X_OK):
        result = subprocess.run([original, *args], cwd=root)
        if result.returncode:
            return result.returncode
    from .publication import current

    try:
        data = current(root, change)
        validate_tree(root, data)
        if git(root, "rev-parse", "HEAD").decode().strip() != head:
            raise ValueError(
                "HEAD changed during pre-push hook; reassess before publishing"
            )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Publication stopped after pre-push hook: {exc}", file=sys.stderr)
        return 1
    return 0


def guard_push(
    root: Path, change: str, plan: dict[str, Any], data: dict[str, Any]
) -> None:
    """Wrap, never skip, the configured pre-push hook and stop mutations in time."""
    validate_tree(root, data)
    original = Path(
        git(root, "rev-parse", "--git-path", "hooks/pre-push").decode().strip()
    )
    if not original.is_absolute():
        original = root / original
    head = git(root, "rev-parse", "HEAD").decode().strip()
    with tempfile.TemporaryDirectory(prefix="engineering-push-") as folder:
        runner = Path(folder) / "guard.py"
        runner.write_text(
            "import sys\nfrom pathlib import Path\n"
            f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})\n"
            "from engineering.publication_git import pre_push_guard\n"
            f"raise SystemExit(pre_push_guard(Path({str(root)!r}), {change!r}, {head!r}, {str(original)!r}, sys.argv[1:]))\n"
        )
        hook = Path(folder) / "pre-push"
        hook.write_text(
            f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(runner))} "$@"\n'
        )
        hook.chmod(0o755)
        environment = dict(os.environ)
        environment.pop(ORIGINAL_GIT_PARAMETERS, None)
        if "GIT_CONFIG_PARAMETERS" in environment:
            environment[ORIGINAL_GIT_PARAMETERS] = environment["GIT_CONFIG_PARAMETERS"]
        subprocess.run(
            [
                "git",
                "-c",
                f"core.hooksPath={folder}",
                "push",
                "--no-follow-tags",
                "--",
                plan["remote"],
                f"{head}:refs/heads/{plan['branch']}",
            ],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
