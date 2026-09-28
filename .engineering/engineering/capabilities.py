"""Reconcile optional-capability content with the provider each capability selects."""

from pathlib import Path
from typing import Any

from .apply import Action, Plan
from .ownership import (
    digest,
    encoded,
    hash_history,
    observe,
    owned_content,
    read_bytes,
    remove_owned,
)
from .registry import (
    REGISTRY,
    STATE,
    content,
    generated,
    output_scope,
    registry,
    state,
)
from .settings import CONFIGURATION, selected_provider


def configured(root: Path) -> bool:
    """Capability selection needs the project's configuration and registry."""
    return all((root / name).is_file() for name in (CONFIGURATION, REGISTRY))


def installer(root: Path, config: dict[str, Any], name: str) -> str | None:
    """Name the selected capability dependency that now installs this content."""
    if not configured(root):
        return None
    for row in registry(root)["dependency"]:
        capability = row.get("capability")
        if (
            capability
            and selected_provider(config, capability) == row["id"]
            and name in content(row["id"])
        ):
            return str(row["id"])
    return None


def handover(
    root: Path,
    config: dict[str, Any],
    name: str,
    entry: dict[str, Any],
    legacy: dict[str, Any],
) -> Action | None:
    """Transfer earlier distributed content to the dependency now installing it.

    Content matching no distributed, generated or recorded version was customized
    and is reported instead of being kept silently.
    """
    dependency = installer(root, config, name)
    if dependency is None:
        return None
    scope = owned_content(read_bytes(root, name), name, entry["ownership"])
    outputs = state(root)["dependencies"].get(dependency, {}).get("outputs", {})
    known = {entry["upstream"], outputs.get(name), digest(generated(dependency, name))}
    if name in legacy:
        known.update(hash_history(legacy[name], name))
    if scope is not None and digest(scope) not in known:
        reason = (
            f"Now installed by the {dependency} dependency, but local content was "
            "customized; remove or restore it, then re-plan"
        )
        return Action(name, "CONFLICT", reason)
    return Action(
        name, "PRESERVE", f"Now installed by the {dependency} dependency; kept"
    )


def plan_deselected(
    plan: Plan, config: dict[str, Any], handled: set[str], legacy: dict[str, Any]
) -> None:
    """Remove pristine content of deselected capabilities; conflict on customization.

    Evidence of pristine content is the recorded dependency output, the fixed
    content the capability generates, or an earlier distribution's hashes. Project
    data such as the Graft index and configuration values are never content.
    """
    root = plan.target
    if not configured(root):
        return
    evidence = state(root)
    records = evidence["dependencies"]
    forget = []
    for row in registry(root)["dependency"]:
        capability = row.get("capability")
        if not capability or selected_provider(config, capability) == row["id"]:
            continue
        label = (
            f"{capability} disabled (provider {selected_provider(config, capability)})"
        )
        outputs = records.get(row["id"], {}).get("outputs", {})
        for path in sorted((set(outputs) | set(content(row["id"]))) - handled):
            spec = output_scope(row["id"], path)
            local = read_bytes(root, path)
            plan.observed[path] = observe(root, path)
            scope = owned_content(local, path, spec)
            if scope is None:
                continue
            known = {outputs.get(path), digest(generated(row["id"], path))}
            if spec["mode"] == "file" and path in legacy:
                known.update(hash_history(legacy[path], path))
            if digest(scope) not in known:
                reason = (
                    f"{label}, but its {row['id']} content was customized; "
                    "remove or restore it, then re-plan"
                )
                plan.actions.append(Action(path, "CONFLICT", reason))
                continue
            reason = f"REMOVE_SAFE: {label}; remove {row['id']} content"
            # Compose with an update already proposed for this path (for example a
            # changed integration section) so one action carries both changes.
            earlier = next(
                (a for a in plan.actions if a.path == path and a.content is not None),
                None,
            )
            if earlier is not None:
                plan.actions.remove(earlier)
                reason = f"{earlier.reason}; {reason}"
            removed = remove_owned(earlier.content if earlier else local, path, spec)
            plan.actions.append(
                Action(
                    path, "REMOVE_SAFE" if removed is None else "MERGE", reason, removed
                )
            )
        if row["id"] in records:
            forget.append(row["id"])
    plan.observed[STATE] = observe(root, STATE)
    if forget:
        for name in forget:
            del records[name]
        reason = f"Forget installation records of deselected {', '.join(forget)}"
        plan.actions.append(Action(STATE, "MERGE", reason, encoded(evidence)))
