"""Reconcile optional-capability content with the provider each capability selects."""

import re
import tomllib
from pathlib import Path
from typing import Any

from .apply import Action, Plan
from .config import safe_path
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


def upgrade_navigation(
    plan: Plan, text: str, config: dict[str, Any]
) -> tuple[str, str]:
    """Preview retaining used Graft or disabling an unused template default."""
    if plan.operation != "update" or selected_provider(config, "navigation") != "graft":
        return text, ""
    records = state(plan.target)["dependencies"]
    plan.observed[STATE] = observe(plan.target, STATE)
    index = safe_path(plan.target, "graft/.graph/wiring.json")
    if index.exists() or "graft" in records:
        plan.detections.append(
            "Keep navigation provider graft: Graft index or recorded installation exists."
        )
        if "graft" in records and set(content("graft")) - set(
            records["graft"]["outputs"]
        ):
            plan.detections.append(
                "graft: UPGRADE REQUIRED (installation record lacks navigation outputs); "
                "after update run engineering deps install graft --apply to install "
                "and record the current launcher and guidance."
            )
        return text, ""
    return disable_navigation(text, config), (
        "navigation graft → none: no Graft index or recorded installation; "
        'to re-enable, set [navigation] provider = "graft", then run '
        "engineering deps install graft --apply"
    )


def disable_navigation(text: str, config: dict[str, Any]) -> str:
    """Change one TOML value, accepting only edits that preserve all other values."""
    expected = {
        **config,
        "navigation": {**config.get("navigation", {}), "provider": "none"},
    }
    # A parsed comparison disambiguates provider literals from comments and other
    # fields, and supports ordinary, dotted and inline navigation tables.
    candidates = [
        text[: match.start()] + '"none"' + text[match.end() :]
        for match in re.finditer(r"([\"'])graft\1", text)
    ]
    # Older configurations may omit the provider or the entire navigation table.
    candidates.append('navigation.provider = "none"\n' + text)
    for header in re.finditer(r"(?m)^[ \t]*\[[^\n]+\][ \t]*(?:#.*)?$", text):
        candidates.append(
            text[: header.end()] + '\nprovider = "none"' + text[header.end() :]
        )
    for proposed in candidates:
        try:
            if tomllib.loads(proposed) == expected:
                return proposed
        except tomllib.TOMLDecodeError:
            continue
    raise ValueError(
        'Cannot preserve navigation formatting; use [navigation] provider = "graft" and re-plan'
    )


def configured(root: Path) -> bool:
    """Capability selection needs the project's configuration and registry."""
    return all((root / name).is_file() for name in (CONFIGURATION, REGISTRY))


def plan_registry(plan: Plan) -> list[dict[str, Any]]:
    """Add missing capability declarations without changing project dependency pins."""
    if not configured(plan.target):
        return []
    data = registry(plan.target)
    rows = data["dependency"]
    if plan.operation != "update":
        return list(rows)
    offered = {row["id"]: row for row in registry(plan.template)["dependency"]}
    additions = {
        row["id"]: offered[row["id"]]["capability"]
        for row in rows
        if "capability" not in row and offered.get(row["id"], {}).get("capability")
    }
    if not additions:
        return list(rows)
    raw = read_bytes(plan.target, REGISTRY)
    assert raw is not None
    text = raw.decode()
    headers = list(
        re.finditer(
            r'(?m)^\[\[\s*(?:dependency|"dependency"|\'dependency\')\s*\]\]', text
        )
    )
    if len(headers) != len(rows):
        raise ValueError(f"{REGISTRY}: use [[dependency]] tables and re-plan")
    for header, row in reversed(list(zip(headers, rows, strict=True))):
        if capability := additions.get(row["id"]):
            row["capability"] = capability
            text = (
                text[: header.end()]
                + f'\ncapability = "{capability}"'
                + text[header.end() :]
            )
    if tomllib.loads(text) != data:
        raise ValueError(f"{REGISTRY}: cannot preserve dependency settings; re-plan")
    plan.observed[REGISTRY] = observe(plan.target, REGISTRY)
    plan.actions.append(
        Action(
            REGISTRY,
            "MIGRATE",
            "Declare optional capabilities for "
            + ", ".join(additions)
            + "; pins and other settings kept",
            text.encode(),
        )
    )
    return list(rows)


def installer(
    rows: list[dict[str, Any]], config: dict[str, Any], name: str
) -> str | None:
    """Name the selected capability dependency that now installs this content."""
    for row in rows:
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
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    name: str,
    entry: dict[str, Any],
    legacy: dict[str, Any],
) -> Action | None:
    """Transfer earlier distributed content to the dependency now installing it.

    Content matching no distributed, generated or recorded version was customized
    and is reported instead of being kept silently.
    """
    dependency = installer(rows, config, name)
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
    plan: Plan,
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    handled: set[str],
    legacy: dict[str, Any],
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
    for row in rows:
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
