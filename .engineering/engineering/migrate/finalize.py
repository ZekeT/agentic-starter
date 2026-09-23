"""Apply exact reviewed OpenSpec proposals, preserving recoverable source history."""

import difflib
from pathlib import Path

from ..config import safe_path
from ..ownership import digest, encoded, read_bytes
from ..source import git
from ..transaction import write_files
from . import application, closure, openspec, validation
from .common import Migration, tree


def plan(root: Path) -> Migration:
    """Check current review evidence and construct only explicitly proposed changes."""
    root = root.resolve()
    data, inventory, raw = application.read(root)
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if data["reviewed_head"] != head:
        raise ValueError("migration.stale: HEAD differs from reviewed_head")
    # Reconstruct inventory using the preparation contract, including its original
    # history evidence. Edited, omitted and newly introduced sources all conflict.
    prepared = openspec.plan(root, inventory.get("history_policy", "git-only"))
    if prepared.conflicts or f"{openspec.WORKSPACE}/inventory.json" in prepared.changes:
        raise ValueError(
            "migration.stale: source inventory changed; prepare and review again"
        )
    if not tree(root, "openspec") and not openspec.integrations(root):
        raise ValueError("migration.stale: no inventoried OpenSpec sources remain")
    application.semantics(root, data, inventory)
    changes = application.changes(root, data, inventory)
    for name in changes:
        if name not in inventory["source_paths"]:
            continue
        original = read_bytes(root, name)
        if inventory["history_policy"] == "git-only":
            if git(root, "show", f"{inventory['source_head']}:{name}") != original:
                raise ValueError(
                    f"migration.history: source not preserved in Git: {name}"
                )
        elif read_bytes(root, f"{openspec.WORKSPACE}/snapshot/{name}") != original:
            raise ValueError(f"migration.history: retained snapshot differs: {name}")
    result = Migration(root, "openspec-finalization", head, changes)
    result.notes.extend(
        [f"Manifest SHA-256: {digest(raw)}", f"Recovery commit: {head}"]
    )
    return result


def show(proposal: Migration) -> None:
    """Print complete reviewed prose and byte-specific changes, including removals."""
    print("OpenSpec finalization preview")
    for note in proposal.notes:
        print(note)
    raw = read_bytes(proposal.root, str(f"{openspec.WORKSPACE}/reconciliation/plan.md"))
    assert raw is not None
    print(raw.decode("utf-8"))
    for name, content in proposal.changes.items():
        before = read_bytes(proposal.root, name)
        print(f"{'DELETE' if content is None else 'WRITE'} {name}")
        print(f"  SHA-256: {digest(before)} -> {digest(content)}")
        try:
            old = (before or b"").decode("utf-8").splitlines(keepends=True)
            new = (content or b"").decode("utf-8").splitlines(keepends=True)
            for line in difflib.unified_diff(
                old, new, fromfile=f"a/{name}", tofile=f"b/{name}"
            ):
                print(
                    line,
                    end=""
                    if line.endswith("\n")
                    else "\n\\ No newline at end of file\n",
                )
        except UnicodeDecodeError:
            print(
                "  Binary content; inspect original bytes using the path and digest above."
            )


def execute(root: Path, *, apply: bool) -> int:
    """Preview without mutation; explicit apply is the human authorization boundary."""
    root = root.resolve()
    if validation.completed(root):
        acceptance = closure.read(root)
        print(
            closure.PENDING
            if acceptance and acceptance["status"] == "accepted"
            else "Human acceptance and temporary cleanup pending; use --accept --plan."
        )
        return 0
    proposal = plan(root)
    show(proposal)
    if not apply:
        print(
            "No files changed. Human approval of this exact proposal is required before --finalize --apply."
        )
        return 0
    if git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise ValueError("git.repository: finalization requires a repository root")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError(
            "git.dirty: finalization requires a clean committed working tree"
        )
    if plan(root) != proposal:
        raise ValueError("migration.stale: inputs changed during preview; review again")
    fingerprints = {name: digest(content) for name, content in proposal.changes.items()}
    for name in (
        "inventory.json",
        "reconciliation/application.json",
        "reconciliation/plan.md",
    ):
        path = f"{openspec.WORKSPACE}/{name}"
        fingerprints[path] = digest(read_bytes(root, path))

    def validate() -> None:
        validation.unchanged(root, fingerprints)
        if tree(root, "openspec") or openspec.integrations(root):
            raise ValueError(
                "migration.validation: OpenSpec integration remains; revise the proposal"
            )
        checks = validation.run(root)
        validation.unchanged(root, fingerprints)
        if tree(root, "openspec") or openspec.integrations(root):
            raise ValueError(
                "migration.validation: checks recreated OpenSpec integration"
            )
        if git(root, "rev-parse", "HEAD").decode().strip() != proposal.head:
            raise ValueError("migration.stale: HEAD changed during validation")
        report = encoded(
            {
                "schema_version": 1,
                "status": "PASS",
                "recovery_commit": proposal.head,
                "files": fingerprints,
                "checks": checks,
            }
        )
        # The receipt is part of the rollback set and appears only after all gates.
        with safe_path(root, validation.REPORT).open("xb") as output:
            output.write(report)

    try:
        write_files(
            root, {**proposal.changes, validation.REPORT: None}, validate=validate
        )
    except ValueError:
        print(
            f"Finalization FAILED. Recovery commit: {proposal.head}. Inspect Git status; validation commands may have produced project-owned artifacts."
        )
        raise
    remove_empty_directories(root, proposal.changes)
    print(
        f"Finalization validation PASS. Report: {validation.REPORT}. Changes remain uncommitted for human review. Human acceptance and temporary cleanup pending. After human acceptance use --accept --apply, then --cleanup --plan; retain snapshots when requested."
    )
    return 0


def remove_empty_directories(root: Path, changes: dict[str, bytes | None]) -> None:
    """Remove only empty OpenSpec directories after the file transaction succeeds."""
    candidates: set[str] = set()
    for name, content in changes.items():
        if content is not None:
            continue
        for parent in Path(name).parents:
            relative = parent.as_posix()
            if (
                relative == "openspec"
                or relative.startswith("openspec/")
                or application.dedicated(relative + "/")
            ):
                candidates.add(relative)
    for name in sorted(candidates, key=lambda p: len(Path(p).parts), reverse=True):
        try:
            safe_path(root, name).rmdir()
        except OSError:
            pass  # Never remove nonempty directories or unreviewed files.
