"""Preflight and apply migrations with source evidence and recovery metadata."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..apply import baseline, git
from ..config import object_value, safe_path
from ..ownership import digest, encoded, json_object, observe, read_bytes
from ..transaction import write_files


@dataclass
class Migration:
    """A reviewable immutable-by-convention set of repository file changes."""

    root: Path
    name: str
    head: str | None
    changes: dict[str, bytes | None] = field(default_factory=dict)
    observed: dict[str, str | None] = field(default_factory=dict)
    conflicts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    executables: set[str] = field(default_factory=set)

    def add(self, name: str, content: bytes | None, *, replace: bool = False) -> None:
        """Refuse unknown destination collisions before recording a mutation."""
        before = read_bytes(self.root, name)
        self.observed[name] = observe(self.root, name)
        if content == before:
            return
        if before is not None and content is not None and not replace:
            self.conflicts.append(f"migration.destination_modified: {name}")
            return
        self.changes[name] = content


def tree(root: Path, prefix: str) -> dict[str, bytes]:
    """Walk contained regular legacy files; refuse symlinks, devices and odd names."""
    base = safe_path(root, prefix)
    if not base.exists():
        return {}
    if not base.is_dir():
        raise ValueError(f"migration.structure: {prefix} must be a directory")
    result = {}
    for path in sorted(base.rglob("*")):
        name = path.relative_to(root).as_posix()
        checked = safe_path(root, name)
        if checked.is_dir():
            continue
        raw = read_bytes(root, name)
        assert raw is not None
        result[name] = raw
    return result


def read_metadata(root: Path, path: str) -> dict[str, Any] | None:
    """Validate path/digest bookkeeping before using it as prior evidence."""
    raw = read_bytes(root, path)
    if raw is None:
        return None
    data = json_object(raw)
    if (
        type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
        or not isinstance(data.get("migration"), str)
    ):
        raise ValueError(f"migration.metadata: unsupported schema at {path}")
    for section in ("source_paths", "outputs"):
        for name, sha in object_value(data.get(section), section).items():
            safe_path(root, name)
            if not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
                raise ValueError(f"migration.metadata: invalid fingerprint {name}")
    return data


def begin(root: Path, name: str) -> tuple[Migration, bool]:
    """Recognize completed migrations and surface edited output collisions."""
    root = root.resolve()
    plan = Migration(root, name, baseline(root))
    path = f".engineering/state/migrations/{name}.json"
    metadata = read_metadata(root, path)
    if metadata is None:
        return plan, False
    for output, sha in metadata["outputs"].items():
        if digest(read_bytes(root, output)) != sha:
            plan.conflicts.append(f"migration.destination_modified: {output}")
    for source in metadata["source_paths"]:
        if read_bytes(root, source) is not None and source not in metadata["outputs"]:
            plan.conflicts.append(f"migration.source_reappeared: {source}")
    plan.notes.append("Already migrated; no duplicate outputs will be created.")
    return plan, True


def finish(
    plan: Migration, sources: dict[str, bytes], source_version: str = "unknown"
) -> None:
    """Fingerprint exact sources and proposed outputs; avoid nondeterministic dates."""
    for name in sources:
        plan.observed[name] = observe(plan.root, name)
    retained = {name: raw for name, raw in sources.items() if name not in plan.changes}
    data = {
        "schema_version": 1,
        "migration": plan.name,
        "source_version": source_version,
        "source_head": plan.head,
        "source_paths": {name: digest(raw) for name, raw in sources.items()},
        "outputs": {
            name: digest(raw)
            for name, raw in {**retained, **plan.changes}.items()
            if raw is not None
        },
    }
    plan.add(f".engineering/state/migrations/{plan.name}.json", encoded(data))


def execute(planner: Callable[[], Migration], *, apply: bool) -> int:
    """Display a plan, then require clean Git and identical inputs before mutation."""
    plan = planner()
    print(f"{plan.name} migration plan")
    for note in plan.notes:
        print(note)
    for name, content in plan.changes.items():
        print(f"{'DELETE' if content is None else 'WRITE'} {name}")
    for conflict in plan.conflicts:
        print(f"CONFLICT [{conflict}]")
    if plan.conflicts:
        print("No files changed. Reconcile conflicts and re-plan.")
        return 1
    if not apply or not plan.changes:
        print(
            "No files changed. Apply requires --apply and a clean committed Git tree."
        )
        return 0
    if plan.head is None or git(plan.root, "rev-parse", "--show-toplevel") != str(
        plan.root
    ):
        raise ValueError("git.repository: apply requires a committed repository root")
    if git(plan.root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError(
            "git.dirty: Migration requires a clean committed working tree. Commit/stash existing changes and retry."
        )
    if planner() != plan:
        raise ValueError("migration.stale: inputs changed; re-plan; no files changed")
    print(f"Recovery commit: {plan.head}")

    def validate() -> None:
        for name, content in plan.changes.items():
            if read_bytes(plan.root, name) != content:
                raise ValueError(f"migration.validation: output differs at {name}")
        read_metadata(plan.root, f".engineering/state/migrations/{plan.name}.json")
        if plan.name == "legacy-starter":
            from ..doctor import diagnose

            failures = [
                f
                for f in diagnose(plan.root)
                if f.severity == "ERROR" and f.code != "dependency"
            ]
            if failures:
                raise ValueError(f"migration.validation: {failures}")

    try:
        write_files(
            plan.root, plan.changes, executables=plan.executables, validate=validate
        )
    except ValueError:
        print(
            f"Recovery: inspect git status; git restore --source={plan.head} -- <affected-tracked-paths>; remove only newly created paths listed above after review."
        )
        raise
    # Remove empty legacy directories only, never caches or unrecognized files.
    for prefix in ("openspec", ".harness", ".factory", ".claude/commands/opsx"):
        base = safe_path(plan.root, prefix)
        if base.is_dir():
            for path in sorted(
                [*base.rglob("*"), base], key=lambda p: len(p.parts), reverse=True
            ):
                if path.is_dir() and not path.is_symlink():
                    try:
                        path.rmdir()
                    except OSError:
                        pass
    print(
        "Applied; changes remain uncommitted. Inspect report, run engineering doctor and project checks, then review."
    )
    return 0
