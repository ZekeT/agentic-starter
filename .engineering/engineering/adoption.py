"""Build shared read-only adoption/update plans from verified local templates."""

import re
from pathlib import Path
from typing import Any

from .apply import Action, Plan, baseline
from .config import object_value, safe_path, validate_config
from .inspection import INSPECTED, inspect_target
from .installation import (
    MANIFEST_PATH,
    STATE_PATH,
    build_state,
    check_state,
    installation_version,
    load_state,
)
from .ownership import (
    digest,
    encoded,
    hash_history,
    json_object,
    merge_owned,
    observe,
    owned_content,
    read_bytes,
    validate_ownership,
)
from .updates import classify, legacy_baseline

SEEDS = (
    "docs/agents/issue-tracker.md",
    "docs/agents/domain.md",
    ".engineering/dependencies.toml",
    ".engineering/graft/package.json",
    ".engineering/graft/package-lock.json",
)

DIRECTORIES = (
    "docs/context",
    "docs/adr",
    "docs/features",
    "docs/migrations",
    ".claude/skills",
)


def template_manifest(root: Path) -> dict[str, Any]:
    """Verify distribution bytes and ownership descriptors before planning changes."""
    from .registry import registry
    from .settings import load

    load(root)
    registry(root)
    data = json_object(read_bytes(root, MANIFEST_PATH) or b"{}")
    if (
        type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
        or type(data.get("ownership_version")) is not int
        or data["ownership_version"] != 1
    ):
        raise ValueError(
            "Template requires supported schema/ownership version 1; run make manifest"
        )
    if not re.fullmatch(
        r"\d+\.\d+\.\d+(?:-[\w.-]+)?", str(data.get("template_version", ""))
    ):
        raise ValueError("Invalid template release version")
    for name, raw in object_value(data.get("files"), "manifest.files").items():
        item = object_value(raw, name)
        hash_history(item, name)
        if type(item.get("executable", False)) is not bool:
            raise ValueError(f"{name}: executable metadata must be boolean")
        spec = validate_ownership(name, item.get("ownership"))
        if name != ".env.template":
            safe_path(root, name)
        if spec["mode"] == "preserve":
            continue
        content = read_bytes(root, name)
        if content is None or digest(content) != item.get("sha256"):
            raise ValueError(
                f"{name}: template distribution hash mismatch; refresh manifest"
            )
        scope = owned_content(content, name, spec)
        if digest(scope) != item.get("owned_sha256"):
            raise ValueError(f"{name}: owned scope hash mismatch; refresh manifest")
        if scope is None:
            raise ValueError(f"{name}: template lacks its declared owned scope")
    return data


def plan_scope(
    plan: Plan,
    name: str,
    entry: dict[str, Any],
    old: dict[str, Any] | None,
    legacy: dict[str, Any],
) -> tuple[Action, dict[str, Any] | None]:
    """Reconcile one owned scope; historical whole-file hashes authorize conversion."""
    spec = validate_ownership(name, entry["ownership"])
    if spec["mode"] == "preserve":
        return Action(name, "SKIP", "Project-owned; never copied or updated"), None
    local = read_bytes(plan.target, name)
    incoming = owned_content(read_bytes(plan.template, name), name, spec)
    assert incoming is not None
    scope = owned_content(local, name, spec)
    prior = old.get("upstream") if old else None
    if old and old.get("ownership") != spec:
        return Action(
            name, "CONFLICT", "Ownership changed; explicit migration required"
        ), old
    if plan.operation == "update" and not old:
        history = object_value(legacy.get(name, entry), name)
        pristine = legacy_baseline(local, history) or legacy_baseline(local, entry)
        if local is not None and pristine is None:
            return Action(
                name, "CONFLICT", "Legacy customization has no pristine evidence"
            ), None
        if pristine is not None:
            # A historical full-file match permits moving into bounded ownership.
            prior = digest(scope) if scope is not None else pristine
            if scope is None and spec["mode"] == "section":
                if name == "Makefile":
                    return Action(
                        name,
                        "CONFLICT",
                        "Pristine legacy Makefile needs bounded-region conversion while retaining its canonical check recipe",
                    ), None
                scope = local
    if not old and plan.operation == "adopt" and name == "Makefile" and scope is None:
        # Appending a second recipe would override the project's own command.
        proposed_targets = set(
            re.findall(rb"^([a-z][a-z-]*)[ \t]*:", incoming, re.MULTILINE)
        ) - {b"check"}
        existing_targets = set(
            re.findall(rb"^([a-z][a-z-]*)[ \t]*:", local or b"", re.MULTILINE)
        )
        if proposed_targets & existing_targets:
            return Action(
                name,
                "CONFLICT",
                "Engineering System target names already exist; reconcile named region explicitly",
            ), None
    kind, reason = classify(scope, incoming, prior)
    if kind == "CONFLICT":
        return Action(name, kind, reason), old
    content = None
    if kind in {"ADD", "MERGE"}:
        content = merge_owned(local, incoming, name, spec)
        # Confirmed pristine legacy whole-file instructions can be converted
        # without appending a duplicate old instruction body.
        if (
            plan.operation == "update"
            and scope == local
            and local is not None
            and spec["mode"] == "section"
            and owned_content(local, name, spec) is None
        ):
            content = incoming
    if (
        content is None
        and local is not None
        and entry.get("executable")
        and not safe_path(plan.target, name).stat().st_mode & 0o111
    ):
        kind, reason, content = (
            "MERGE",
            "Restore required executable permission without changing content",
            local,
        )
    new_entry = {"ownership": spec, "upstream": digest(incoming)}
    return Action(
        name, kind, reason, content, bool(entry.get("executable", False))
    ), new_entry


def plan_installation(template: Path, target: Path, operation: str = "adopt") -> Plan:
    """Use one inventory, preservation contract and state transition for both paths."""
    template, target = template.resolve(), target.resolve()
    if operation not in {"adopt", "update"}:
        raise ValueError("Expected adopt or update")
    if not target.is_dir() or not template.is_dir():
        raise ValueError("Template and target must be existing directories")
    if template.is_relative_to(target) or target.is_relative_to(template):
        raise ValueError("Template and target must not overlap")
    offered = template_manifest(template)
    if (target / ".harness").exists() or (target / ".factory").exists():
        raise ValueError(
            "Legacy starter detected; use engineering migrate legacy-starter first"
        )
    state = load_state(target)
    if state is not None and operation == "adopt":
        raise ValueError("Installation state already exists; use update")
    if state is None:
        installation_version(
            target
        )  # Validate all legacy authorities before conversion.
    prior_raw = read_bytes(target, MANIFEST_PATH)
    prior_manifest = json_object(prior_raw) if prior_raw else {}
    if prior_raw:
        validate_config(target, {"schema_version": 1, **prior_manifest})
    if state is not None:
        check_state(target, prior_manifest)
    if prior_manifest.get("schema_version", 1) != 1:
        raise ValueError("Unsupported installed manifest schema")
    plan = Plan(template, target, operation, baseline(target))
    plan.detections = inspect_target(target)
    for finding in plan.detections:
        if finding.startswith(("Unsupported", "Unresolved")):
            plan.actions.append(Action("Makefile", "CONFLICT", finding))
    entries = object_value(state["entries"], "state.entries") if state else {}
    legacy = object_value(prior_manifest.get("files", {}), "legacy.files")
    next_entries: dict[str, object] = {}
    files = object_value(offered["files"], "manifest.files")
    for name, raw in files.items():
        entry = object_value(raw, name)
        if entry["ownership"]["mode"] != "preserve":
            plan.observed[name] = observe(target, name)
        action, next_entry = plan_scope(plan, name, entry, entries.get(name), legacy)
        plan.actions.append(action)
        if next_entry is not None:
            next_entries[name] = next_entry
    for name, entry in entries.items():
        if name not in files:
            plan.observed[name] = observe(target, name)
            local = read_bytes(target, name)
            spec = entry["ownership"]
            scope = owned_content(local, name, spec)
            if scope is None:
                continue
            if digest(scope) != entry["upstream"]:
                plan.actions.append(
                    Action(
                        name,
                        "CONFLICT",
                        "REMOVE_CONFLICT: removed upstream scope was customized",
                    )
                )
                next_entries[name] = entry
            elif spec["mode"] == "file":
                plan.actions.append(
                    Action(name, "REMOVE_SAFE", "Pristine scope removed upstream")
                )
            else:
                incoming = encoded({}) if spec["mode"] == "hooks" else b""
                plan.actions.append(
                    Action(
                        name,
                        "MERGE",
                        "REMOVE_SAFE: remove only the owned scope",
                        merge_owned(local, incoming, name, spec),
                    )
                )
    for name in SEEDS:
        plan.observed[name] = observe(target, name)
        if read_bytes(target, name) is None:
            plan.actions.append(
                Action(
                    name,
                    "ADD",
                    "Seed initial project configuration; future changes are project/dependency-owned",
                    read_bytes(template, name),
                )
            )
    for name in INSPECTED:
        plan.observed[name] = observe(target, name)
    for name in DIRECTORIES:
        path = safe_path(target, name)
        if path.exists() and not path.is_dir():
            raise ValueError(f"{name}: required directory is not a directory")
    plan.directories = DIRECTORIES
    if not plan.conflicts:
        installed = {**offered, "project": prior_manifest.get("project", {})}
        metadata = [
            (MANIFEST_PATH, encoded(installed)),
            (
                STATE_PATH,
                encoded(build_state(offered["template_version"], next_entries)),
            ),
        ]
        for name, content in metadata:
            before = read_bytes(target, name)
            if before != content:
                plan.actions.append(
                    Action(
                        name,
                        "ADD" if before is None else "MERGE",
                        "Reconciled installation metadata; preserve project overrides",
                        content,
                    )
                )
    return plan
