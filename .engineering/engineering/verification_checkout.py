"""Materialize proposed content without touching the user's index or working tree."""

import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .ownership import digest
from .source import git
from .verification_inputs import (
    STATE,
    files,
    paths_from_git,
    source_path,
    validate_navigation,
)


def baseline_files(root: Path, base: str) -> dict[str, tuple[str, str]]:
    """Read regular baseline blobs; never check out links or run Git filters."""
    entries = {}
    for entry in git(root, "ls-tree", "-r", "-z", base).split(b"\0"):
        if not entry:
            continue
        metadata, raw_name = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        name = raw_name.decode(errors="surrogateescape")
        source_path(root, name)
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError(f"Unsupported baseline verification input: {name}")
        if name == STATE or name.startswith(STATE + "/"):
            raise ValueError("Verification records must not be tracked")
        entries[name] = (mode, oid)
    return entries


def baseline_content(root: Path, base: str) -> Iterator[tuple[str, str, bytes]]:
    """Read validated blobs in one plumbing call, without filters or archive rules."""
    entries = baseline_files(root, base)
    result = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input="".join(oid + "\n" for _, oid in entries.values()).encode(),
        capture_output=True,
        check=True,
    )
    offset = 0
    for name, (mode, _) in entries.items():
        end = result.stdout.index(b"\n", offset)
        size = int(result.stdout[offset:end].split()[-1])
        offset = end + 1
        yield name, mode, result.stdout[offset : offset + size]
        offset += size + 1


def proposed_files(root: Path, base: str, plan: dict[str, Any]) -> dict[str, Any]:
    """Working bytes win for selected paths; other files come from the base."""
    result: dict[str, Any] = {}
    tracked = paths_from_git(root, "ls-files", "--cached", "-z")
    if set(plan["inputs"]) & tracked - set(plan["paths"]):
        raise ValueError("Tracked explicit inputs must be included in intended paths")
    selected = set(plan["paths"]) | set(plan["inputs"])
    selected.add(".engineering/state/dependencies.json")
    for name, mode, raw in baseline_content(root, base):
        if name not in selected:
            result[name] = {
                "sha256": digest(raw),
                "executable": mode == "100755",
            }
    result.update(files(root, selected))
    return result


def materialize(root: Path, destination: Path, inputs: dict[str, Any]) -> None:
    """Create an independent local Git repository with baseline history and bytes."""
    plan = inputs["plan"]
    git(root, "clone", "--no-local", "--no-checkout", "--", str(root), str(destination))
    git(destination, "update-ref", "HEAD", inputs["base"])
    git(destination, "read-tree", inputs["base"])
    for name, mode, raw in baseline_content(root, inputs["base"]):
        target = source_path(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o755 if mode == "100755" else 0o644)
    # Baseline paths were validated before checkout. Selected contents are copied
    # as regular bytes, never linked to the user's working files.
    selected = set(plan["paths"]) | set(plan["inputs"])
    selected.add(".engineering/state/dependencies.json")
    for name in sorted(selected):
        target = source_path(destination, name)
        value = inputs["files"][name]
        if value is None:
            if target.exists():
                target.unlink()
            continue
        source = source_path(root, name)
        raw = source.read_bytes()
        if digest(raw) != value["sha256"]:
            raise ValueError("Verification inputs changed during checkout preparation")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o755 if value["executable"] else 0o644)
    (destination / STATE).mkdir(parents=True, exist_ok=True)
    validate_checkout(destination, inputs)
    validate_navigation(destination, plan)


def validate_checkout(checkout: Path, inputs: dict[str, Any]) -> None:
    """Detect modified, removed and unexpected nonignored source in the review tree."""
    expected = inputs["files"]
    names = set(expected) | paths_from_git(checkout, "ls-files", "--cached", "-z")
    names |= paths_from_git(
        checkout, "ls-files", "--others", "--exclude-standard", "-z"
    )
    if files(checkout, names) != expected:
        raise ValueError(
            "STALE: isolated checkout inputs mutated; prepare and reverify"
        )


@contextmanager
def temporary_checkout(
    root: Path, inputs: dict[str, Any], plan: dict[str, Any]
) -> Iterator[Path]:
    """Disposable version-probe context, excluded from snapshot identity."""
    with tempfile.TemporaryDirectory(prefix="engineering-verify-") as folder:
        checkout = Path(folder) / "checkout"
        materialize(root, checkout, {**inputs, "plan": plan})
        yield checkout
        validate_checkout(checkout, inputs)
