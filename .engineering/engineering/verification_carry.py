"""Conservative report reuse after an unrelated advancement of the merge base."""

from pathlib import Path
from typing import Any

from .config import safe_path
from .source import git
from .verification_checkout import validate_checkout
from .verification_inputs import paths_from_git


def carried_reports(
    root: Path, previous: dict[str, Any], current: dict[str, Any]
) -> dict[str, Any]:
    """Carry only unchanged scoped patches, plans, probes and requirements.

    With identical baseline blobs and final bytes/modes on every scoped path,
    each path's own patch is identical, including additions and deletions.
    """
    old, new = previous["inputs"], current["inputs"]
    if old["base"] == new["base"] or not previous["reports"]:
        return {}
    for key in ("plan", "tools", "root", "runtime"):
        if old[key] != new[key]:
            return {}
    if old.get("starter_source") != new.get("starter_source"):
        return {}
    if previous["requirements"] != current["requirements"]:
        return {}
    try:
        git(root, "merge-base", "--is-ancestor", old["base"], new["base"])
        validate_checkout(safe_path(root, previous.get("checkout", "")), old)
        changed = paths_from_git(
            root,
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            old["base"],
            new["base"],
            "--",
        )
    except (ValueError, OSError):
        return {}
    selected = set(new["plan"]["paths"]) | set(new["plan"]["inputs"])
    selected.add(".engineering/state/dependencies.json")
    if changed & selected:
        return {}
    if any(old["files"].get(path) != new["files"].get(path) for path in selected):
        return {}
    return {
        role: {
            **report,
            "snapshot": current["snapshot"],
            "carried_from": previous["snapshot"],
        }
        for role, report in previous["reports"].items()
    }
