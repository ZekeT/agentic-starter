"""Reconcile optional-capability content with the provider each capability selects."""

from pathlib import Path
from typing import Any

from . import graft
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
from .registry import REGISTRY, STATE, registry, state
from .settings import CAPABILITIES, CONFIGURATION


def content(row: dict[str, Any]) -> tuple[str, ...]:
    """Name the content a capability dependency installs besides recorded outputs."""
    return graft.CONTENT if row["id"] == "graft" else ()


def configured(root: Path) -> bool:
    """Capability selection needs the project's configuration and registry."""
    return all((root / name).is_file() for name in (CONFIGURATION, REGISTRY))


def provider(config: dict[str, Any], capability: str) -> str:
    """Read a capability's provider from validated (possibly migrated) settings."""
    default = CAPABILITIES[capability][0]
    return str(config.get(capability, {}).get("provider", default))


def installer(root: Path, config: dict[str, Any], name: str) -> str | None:
    """Name the selected capability dependency that now installs this content."""
    if not configured(root):
        return None
    for row in registry(root)["dependency"]:
        capability = row.get("capability")
        if (
            capability
            and provider(config, capability) == row["id"]
            and name in content(row)
        ):
            return str(row["id"])
    return None


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
        if not capability or provider(config, capability) == row["id"]:
            continue
        label = f"{capability} disabled (provider {provider(config, capability)})"
        outputs = records.get(row["id"], {}).get("outputs", {})
        for path in sorted((set(outputs) | set(content(row))) - handled):
            spec = graft.output_scope(path)
            local = read_bytes(root, path)
            plan.observed[path] = observe(root, path)
            scope = owned_content(local, path, spec)
            if scope is None:
                continue
            known = {outputs.get(path), digest(graft.generated(path))}
            if spec["mode"] == "file" and path in legacy:
                known.update(hash_history(legacy[path], path))
            if digest(scope) not in known:
                reason = (
                    f"{label}, but its {row['id']} content was customized; "
                    "remove or restore it, then re-plan"
                )
                plan.actions.append(Action(path, "CONFLICT", reason))
                continue
            plan.actions.append(
                Action(
                    path,
                    "REMOVE_SAFE" if spec["mode"] == "file" else "MERGE",
                    f"REMOVE_SAFE: {label}; remove {row['id']} content",
                    remove_owned(local, path, spec),
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
