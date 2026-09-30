"""Read regular Git blobs for isolated verification and pinned starter sources."""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path

from .source import git
from .verification_inputs import STATE, source_path


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
