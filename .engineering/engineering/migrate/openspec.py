"""Inventory OpenSpec references without interpreting or removing source material."""

import re
from pathlib import Path
from typing import Any

from ..apply import baseline
from ..config import safe_path
from ..ownership import digest, encoded, json_object, observe, read_bytes
from ..source import git
from .common import Migration, tree

WORKSPACE = ".engineering/migration-work/openspec"
HANDOFF = "OpenSpec preserved. Next: engineering migrate openspec-project --apply, then /migrate-from-openspec for semantic reconciliation and human review."


def integrations(root: Path) -> dict[str, bytes]:
    """Find explicit tool references, retaining whole shared files as evidence."""
    result = tree(root, ".claude/commands/opsx")
    for prefix in (".claude/skills", ".agents/skills"):
        base = safe_path(root, prefix)
        if base.is_dir():
            for path in sorted(base.glob("openspec-*")):
                result.update(tree(root, path.relative_to(root).as_posix()))
    for name in (
        "CLAUDE.md",
        "AGENTS.md",
        ".claude/settings.json",
        "package.json",
        "package-lock.json",
        "npm-shrinkwrap.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "Makefile",
    ):
        raw = read_bytes(root, name)
        if raw is not None and (b"openspec" in raw.lower() or b"opsx" in raw.lower()):
            result[name] = raw
    return dict(sorted(result.items()))


def detected(root: Path) -> bool:
    """Recognize standalone OpenSpec installations as well as runtime wiring."""
    return safe_path(root, "openspec").exists() or bool(integrations(root))


def capability(name: str, raw: bytes) -> dict[str, Any]:
    """Capture literal headings and paths, leaving semantic relationships unknown."""
    match = re.search(r"(?m)^#\s+(.+?)\s*$", raw.decode("utf-8", errors="replace"))
    return {
        "path": name,
        "title": match.group(1) if match else Path(name).parent.name,
        "status": "canonical",
        "related_tests": [],
        "related_code_candidates": [],
        "related_active_changes": [],
    }


def index(title: str, paths: list[str]) -> bytes:
    """Render source references without copying or classifying their prose."""
    return (
        f"# {title}\n\n" + "\n".join(f"- `{name}`" for name in paths) + "\n"
    ).encode()


def plan(root: Path, policy: str = "git-only") -> Migration:
    """Prepare deterministic temporary evidence; preserve every source byte."""
    root = root.resolve()
    result = Migration(root, "openspec-project", baseline(root))
    if policy not in {"git-only", "snapshot"}:
        raise ValueError("migration.history: expected git-only or snapshot")
    sources = tree(root, "openspec")
    wiring = integrations(root)
    if not sources and not wiring:
        result.notes.append("No OpenSpec source or project wiring found.")
        return result
    docs = {}
    for prefix in ("docs/adr", "docs/context", "docs/features"):
        docs.update(tree(root, prefix))
    canonical = [
        capability(name, raw)
        for name, raw in sources.items()
        if name.startswith("openspec/specs/") and name.endswith("/spec.md")
    ]
    active: dict[str, list[str]] = {}
    archived: dict[str, list[str]] = {}
    metadata = []
    for name in sources:
        parts = Path(name).parts
        if len(parts) > 3 and parts[1] == "changes":
            if parts[2] == "archive" and len(parts) > 4:
                archived.setdefault(parts[3], []).append(name)
            elif parts[2] != "archive":
                active.setdefault(parts[2], []).append(name)
            else:
                metadata.append(name)
        elif not name.startswith("openspec/specs/"):
            metadata.append(name)
    evidence = dict(sorted({**sources, **wiring, **docs}.items()))
    committed = {}
    for name, raw in evidence.items():
        result.observed[name] = observe(root, name)
        try:
            committed[name] = (
                bool(result.head) and git(root, "show", f"{result.head}:{name}") == raw
            )
        except ValueError:
            committed[name] = False
    branches = (
        git(
            root,
            "for-each-ref",
            "--format=%(refname) %(objectname)",
            "refs/heads",
            "refs/remotes",
        )
        .decode()
        .splitlines()
        if result.head
        else []
    )
    # Preserve the preparation commit on identical retries, even after evidence is committed.
    prior = read_bytes(root, f"{WORKSPACE}/inventory.json")
    source_head = result.head
    if prior:
        previous = json_object(prior)
        if previous.get("source_paths") == {
            name: digest(raw) for name, raw in evidence.items()
        }:
            source_head = previous.get("source_head")
            if not isinstance(source_head, str) or not re.fullmatch(
                r"[0-9a-f]{40}|[0-9a-f]{64}", source_head
            ):
                raise ValueError("migration.stale: invalid recorded source commit")
            try:
                git(root, "merge-base", "--is-ancestor", source_head, "HEAD")
                recorded_committed = previous.get("committed_at_head")
                if not isinstance(recorded_committed, dict) or set(
                    recorded_committed
                ) != set(evidence):
                    raise ValueError("invalid recorded source history")
                for name, raw in evidence.items():
                    try:
                        at_head = git(root, "show", f"{source_head}:{name}") == raw
                    except ValueError:
                        at_head = False
                    if recorded_committed[name] is not at_head:
                        raise ValueError("recorded source history differs")
                committed = recorded_committed
                recorded_branches = previous.get("branches")
                if not isinstance(recorded_branches, list):
                    raise ValueError("invalid recorded branches")
                for branch in recorded_branches:
                    if not isinstance(branch, str) or not re.fullmatch(
                        r"refs/(?:heads|remotes)/\S+ [0-9a-f]{40}(?:[0-9a-f]{24})?",
                        branch,
                    ):
                        raise ValueError("invalid recorded branch")
                    git(root, "cat-file", "-e", branch.rsplit(" ", 1)[1] + "^{commit}")
            except ValueError as exc:
                raise ValueError(
                    "migration.stale: recorded Git evidence is invalid; review inventory"
                ) from exc
            branches = previous.get("branches", branches)
    inventory = {
        "schema_version": 1,
        "migration": "openspec-project",
        "source_head": source_head,
        "history_policy": policy,
        "source_paths": {name: digest(raw) for name, raw in evidence.items()},
        "committed_at_head": committed,
        "branches": branches,
        "canonical": canonical,
        "active_changes": [
            {"name": name, "paths": paths} for name, paths in sorted(active.items())
        ],
        "archived_changes": [
            {"name": name, "paths": paths} for name, paths in sorted(archived.items())
        ],
        "metadata": metadata,
        "existing_docs": sorted(docs),
        "integrations": sorted(wiring),
        "legacy_starter": [
            name
            for name in (".factory", ".harness", "FACTORY.md", "HARNESS.md")
            if safe_path(root, name).exists()
        ],
    }
    result.add(f"{WORKSPACE}/inventory.json", encoded(inventory))
    for filename, title, indexed_paths in (
        (
            "canonical-spec-index.md",
            "Canonical source references — requires reconciliation",
            [item["path"] for item in canonical],
        ),
        (
            "active-change-index.md",
            "Active change source references",
            [path for paths in active.values() for path in paths],
        ),
        (
            "archived-change-index.md",
            "Archived change source references",
            [path for paths in archived.values() for path in paths],
        ),
        (
            "detected-integrations.md",
            "Detected OpenSpec integration — preserved",
            sorted(wiring),
        ),
    ):
        result.add(f"{WORKSPACE}/{filename}", index(title, indexed_paths))
    result.add(
        f"{WORKSPACE}/reconciliation/README.md",
        b"# Semantic reconciliation\n\nRun /migrate-from-openspec. Review prose against code and tests; resolve conflicts with the human before finalization. Inventory is not semantic approval.\n",
    )
    if policy == "snapshot":
        for name, raw in evidence.items():
            result.add(f"{WORKSPACE}/snapshot/{name}", raw)
    result.notes.extend(
        [
            f"Canonical capabilities: {len(canonical)}; active changes: {len(active)}; archived changes: {len(archived)}.",
            HANDOFF,
        ]
    )
    return result
