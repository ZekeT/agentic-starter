"""Read regular Git blobs for isolated verification and pinned starter sources."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

from .verification_inputs import STATE, source_path


def git_environment() -> dict[str, str]:
    """Keep Git bound to the selected repository and its original objects."""
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_TERMINAL_PROMPT="0",
        GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=yes",
    )
    return environment


def read_objects(root: Path, *args: str, batch: bytes | None = None) -> bytes:
    """Read object plumbing without inherited repository/configuration overrides."""
    return subprocess.run(
        ["git", "-C", str(root), *args],
        env=git_environment(),
        input=batch,
        capture_output=True,
        timeout=60,
        check=True,
    ).stdout


def baseline_files(root: Path, base: str) -> dict[str, tuple[str, str]]:
    """Read regular baseline blobs; never check out links or run Git filters."""
    entries = {}
    for entry in read_objects(root, "ls-tree", "-r", "-z", base).split(b"\0"):
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
    raw_objects = read_objects(
        root,
        "cat-file",
        "--batch",
        batch="".join(oid + "\n" for _, oid in entries.values()).encode(),
    )
    offset = 0
    for name, (mode, _) in entries.items():
        end = raw_objects.index(b"\n", offset)
        size = int(raw_objects[offset:end].split()[-1])
        offset = end + 1
        yield name, mode, raw_objects[offset : offset + size]
        offset += size + 1
