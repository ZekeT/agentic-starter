"""Convert known starter ownership while preserving unknown project customizations."""

import json
import re
from pathlib import Path
from typing import Any

from ..adoption import SEEDS, template_manifest
from ..config import object_value, safe_path, validate_config
from ..installation import MANIFEST_PATH, STATE_PATH, build_state
from ..ownership import (
    digest,
    encoded,
    json_object,
    merge_owned,
    owned_content,
    read_bytes,
)
from .common import Migration, begin, finish
from .openspec import extract

OLD_MANIFEST = ".harness/template-manifest.json"
OLD_STATE = ".factory/state.json"


def translate_config(template: Path, root: Path, previous: dict[str, Any]) -> bytes:
    """Move supported project settings into TOML, retaining reviewed exceptions."""
    validate_config(root, {"schema_version": 1, **previous})
    content = (read_bytes(template, ".engineering/config.toml") or b"").decode()
    project = object_value(previous.get("project", {}), "legacy project")
    for section in ("maintainability", "navigation"):
        values = object_value(project.get(section, {}), section)
        for key, value in values.items():
            if key == "exceptions":
                value_text = (
                    "["
                    + ", ".join(
                        "{ path = "
                        + json.dumps(row["path"])
                        + ", reason = "
                        + json.dumps(row["reason"])
                        + " }"
                        for row in value
                    )
                    + "]"
                )
            else:
                value_text = json.dumps(value)
            content, count = re.subn(
                rf"(?m)^{re.escape(key)} = .*", f"{key} = {value_text}", content
            )
            if count != 1:
                raise ValueError(f"migration.config: unsupported legacy setting {key}")
    return content.encode()


def old_region(raw: bytes, name: str) -> bytes | None:
    """Recognize only a complete unique legacy integration region."""
    begin_marker = (
        b"<!-- factory:integration:begin -->"
        if name.endswith(".md")
        else b"# factory:integration:begin"
    )
    end_marker = begin_marker.replace(b":begin", b":end")
    if begin_marker not in raw and end_marker not in raw:
        return None
    pattern = (
        rb"(?m)^"
        + re.escape(begin_marker)
        + rb"\r?\n.*?^"
        + re.escape(end_marker)
        + rb"(?:\r?\n|\Z)"
    )
    matches = re.findall(pattern, raw, re.DOTALL)
    if len(matches) != 1 or raw.count(begin_marker) != 1 or raw.count(end_marker) != 1:
        raise ValueError(f"migration.markers: malformed legacy region in {name}")
    value: bytes = matches[0]
    return value


def plan(template: Path, root: Path, policy: str = "snapshot") -> Migration:
    """Install v3 and retire only evidenced legacy scopes in a single transaction."""
    result, completed = begin(root, "legacy-starter")
    if completed:
        return result
    previous_raw = read_bytes(root, OLD_MANIFEST)
    if previous_raw is None:
        result.notes.append(
            "No legacy ownership manifest found. Use engineering adopt for new projects; reconcile unowned legacy files manually."
        )
        if any(
            (root / name).exists()
            for name in (".harness", ".factory", "FACTORY.md", "HARNESS.md")
        ):
            result.conflicts.append(
                "migration.ownership: legacy files lack baseline evidence"
            )
        return result
    previous = json_object(previous_raw)
    known = json_object(
        read_bytes(template, ".engineering/migrations/baselines/v2-manifest.json")
        or b"{}"
    )
    offered = template_manifest(template)
    if read_bytes(root, STATE_PATH) is not None:
        result.conflicts.append(
            "migration.installed: v3 state already exists without completion metadata"
        )
        return result
    sources = extract(result, policy)
    sources[OLD_MANIFEST] = previous_raw
    old_files = object_value(previous.get("files", {}), "legacy files")
    old_state_raw = read_bytes(root, OLD_STATE)
    if old_state_raw:
        old_state = json_object(old_state_raw)
        if old_state.get("schema_version") != 1:
            raise ValueError("migration.schema: unsupported legacy installation state")
        sources[OLD_STATE] = old_state_raw
    # Historical hashes from the checked-in v2 distribution plus installed evidence.
    old_files = {**known.get("files", {}), **old_files}
    originals: dict[str, bytes] = {}
    for name, entry in old_files.items():
        if entry.get("ownership", {}).get("mode") == "preserve":
            continue
        raw = read_bytes(root, name)
        if raw is not None:
            originals[name] = raw
    # Include only metadata/version files outside the old manifest. Unrecognized
    # project files under .harness are preserved and reported, never deleted.
    for name in (
        OLD_MANIFEST,
        OLD_STATE,
        ".harness/TEMPLATE_VERSION",
        ".claude/template-version.json",
    ):
        raw = read_bytes(root, name)
        if raw is not None:
            originals[name] = raw
    custom_docs = []
    entries = {}
    new_files = offered["files"]
    for name, raw in originals.items():
        safe_path(root, name)
        entry = old_files.get(name, {})
        pristine = digest(raw) in [entry.get("sha256"), *entry.get("previous", [])]
        sources[name] = raw
        if name in new_files and new_files[name]["ownership"]["mode"] in {
            "section",
            "hooks",
        }:
            spec = new_files[name]["ownership"]
            incoming = owned_content(read_bytes(template, name), name, spec)
            assert incoming is not None
            if spec["mode"] == "hooks":
                current = owned_content(raw, name, spec)
                if not pristine and digest(current) != entry.get("owned_sha256"):
                    result.conflicts.append(
                        f"migration.destination_modified: customized hook scope in {name}"
                    )
                    continue
                replacement = merge_owned(raw, incoming, name, spec)
                settings = json_object(replacement)
                overrides = settings.get("skillOverrides", {})
                if isinstance(overrides, dict):
                    for retired in (
                        "gauntlet-loop",
                        "handoff",
                        "grilling",
                        "setup-update",
                        "rescan-docs",
                    ):
                        if overrides.get(retired) == "user-invocable-only":
                            del overrides[retired]
                    if not overrides:
                        settings.pop("skillOverrides", None)
                    replacement = encoded(settings)
            else:
                region = old_region(raw, name)
                if name == "Makefile" and pristine:
                    template_bytes = read_bytes(template, name)
                    assert template_bytes is not None
                    replacement = template_bytes
                elif region is not None and (
                    pristine or digest(region) == entry.get("owned_sha256")
                ):
                    replacement = (result.changes.get(name) or raw).replace(
                        region, incoming, 1
                    )
                    if name == "Makefile" and b".harness/" in replacement:
                        result.conflicts.append(
                            "migration.makefile: custom canonical check references legacy scripts; reconcile before apply"
                        )
                        continue
                elif pristine:
                    replacement = incoming
                else:
                    result.conflicts.append(
                        f"migration.destination_modified: customized managed region in {name}"
                    )
                    continue
            if name == ".gitignore" and b"/graphify-out/" in raw.splitlines():
                if b"/graphify-out/" not in replacement.splitlines():
                    replacement += (
                        b"\n# Preserved legacy navigation cache.\n/graphify-out/\n"
                    )
            result.add(name, replacement, replace=True)
        elif name in new_files and new_files[name]["ownership"]["mode"] == "file":
            incoming = read_bytes(template, name)
            if pristine or incoming == raw:
                result.add(name, incoming, replace=True)
            else:
                result.conflicts.append(
                    f"migration.destination_modified: {name}; reconcile customized managed file"
                )
        elif name in {"FACTORY.md", "HARNESS.md"}:
            if not pristine:
                custom_docs.append(name)
            result.add(f".engineering/migrations/legacy-docs/{name}", raw)
            result.add(name, None)
        elif (
            name
            in {
                OLD_MANIFEST,
                OLD_STATE,
                ".harness/TEMPLATE_VERSION",
                ".claude/template-version.json",
            }
            or pristine
        ):
            # Preserve source evidence, including removed local skill copies.
            result.add(f".engineering/migrations/legacy-starter/{name}", raw)
            result.add(name, None)
        else:
            result.conflicts.append(
                f"migration.destination_modified: {name}; preserve/reconcile customized legacy file"
            )
    for name, entry in new_files.items():
        spec = entry["ownership"]
        if spec["mode"] == "preserve":
            continue
        incoming = read_bytes(template, name)
        assert incoming is not None
        if name not in result.changes:
            current = read_bytes(root, name)
            content = owned_content(incoming, name, spec)
            assert content is not None
            if name == ".engineering/config.toml":
                content = translate_config(template, root, previous)
            result.add(name, merge_owned(current, content, name, spec))
        if entry.get("executable"):
            result.executables.add(name)
        entries[name] = {"ownership": spec, "upstream": entry["owned_sha256"]}
    # Tracker configuration is project-owned after initial creation.
    for name in SEEDS:
        if read_bytes(root, name) is None:
            result.add(name, read_bytes(template, name))
    result.add(MANIFEST_PATH, encoded(offered))
    result.add(STATE_PATH, encoded(build_state(offered["template_version"], entries)))
    result.add(
        ".engineering/migrations/legacy-doc-customizations.md",
        (
            "# Legacy documentation reconciliation\n\n"
            + (
                "Unclassified customized originals preserved in legacy-docs/:\n"
                + "\n".join("- " + name for name in custom_docs)
                if custom_docs
                else "No unclassified root documentation customizations found."
            )
            + "\n\nReview preserved copies; unknown prose has not been injected into ENGINEERING.md.\n"
        ).encode(),
    )
    result.notes += [
        "CONVERT installation ownership and project configuration to v3.",
        "PRESERVE unknown project files and all global installations.",
        "MANUAL run engineering deps install --apply after migration; optional skills require explicit selection.",
    ]
    finish(result, sources, str(previous.get("template_version", "unknown")))
    return result
