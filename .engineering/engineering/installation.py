"""Reconcile legacy installation metadata without advancing preserved baselines."""

import json
import re
from pathlib import Path
from typing import Any

from .config import object_value, read_text, safe_path


def installation_version(root: Path) -> str | None:
    """Read existing version authorities and reject invalid or conflicting values."""
    state = load_state(root)
    if state is not None:
        return str(state["installed_version"])
    versions: dict[str, str] = {}
    for name in (
        ".engineering/manifest.json",
        ".engineering/TEMPLATE_VERSION",
        ".claude/template-version.json",
    ):
        path = safe_path(root, name)
        if not path.exists():
            continue
        if not path.is_file():
            raise ValueError(f"{name}: expected a regular file")
        if name.endswith(".json"):
            data = object_value(json.loads(read_text(root, name)), name)
            # Old growth-only manifests did not record an installed version.
            if name == ".engineering/manifest.json" and "template_version" not in data:
                continue
            version = data.get("template_version")
        else:
            version = read_text(root, name).strip()
        if not isinstance(version, str) or not re.fullmatch(
            r"\d+\.\d+\.\d+(?:-[\w.-]+)?", version
        ):
            raise ValueError(f"{name}: template_version must be a semantic version")
        versions[name] = version
    if len(set(versions.values())) > 1:
        raise ValueError(
            f"Installed template versions disagree: {versions}; reconcile metadata before migration"
        )
    return next(iter(versions.values()), None)


STATE_PATH = ".engineering/state/install.json"
MANIFEST_PATH = ".engineering/manifest.json"


def load_state(root: Path) -> dict[str, Any] | None:
    """Validate installed authority; legacy stamps apply only before conversion."""
    from .ownership import json_object, read_bytes, validate_ownership

    raw = read_bytes(root, STATE_PATH)
    if raw is None:
        return None
    state = json_object(raw)
    if type(state.get("schema_version")) is not int or state["schema_version"] != 1:
        raise ValueError("Unsupported installation state schema_version")
    if not isinstance(state.get("installed_version"), str) or not re.fullmatch(
        r"\d+\.\d+\.\d+(?:-[\w.-]+)?", state["installed_version"]
    ):
        raise ValueError("Invalid installed_version in state")
    if set(state) != {"schema_version", "installed_version", "entries"}:
        raise ValueError(
            "Installation state must contain only version and baseline metadata"
        )
    entries = object_value(state.get("entries"), "state.entries")
    for name, value in entries.items():
        safe_path(root, name)
        entry = object_value(value, f"state entry {name}")
        validate_ownership(name, entry.get("ownership"))
        fingerprint = entry.get("upstream")
        if not isinstance(fingerprint, str) or not re.fullmatch(
            r"[0-9a-f]{64}", fingerprint
        ):
            raise ValueError(f"{name}: invalid upstream baseline")
    return state


def build_state(version: str, entries: dict[str, Any]) -> dict[str, Any]:
    """Keep only installation authority and per-scope upstream fingerprints."""
    return {"schema_version": 1, "installed_version": version, "entries": entries}


def initialize(root: Path) -> None:
    """Seed missing state from verified distribution bytes, never reset a baseline."""
    from .adoption import template_manifest
    from .ownership import encoded, json_object, read_bytes

    if load_state(root) is not None:
        check_state(root, json_object(read_bytes(root, MANIFEST_PATH) or b"{}"))
        print("Existing installation baseline preserved")
        return
    manifest = template_manifest(root)
    entries = {
        name: {"ownership": entry["ownership"], "upstream": entry["owned_sha256"]}
        for name, entry in manifest["files"].items()
        if entry["ownership"]["mode"] != "preserve"
    }
    content = encoded(build_state(manifest["template_version"], entries))
    destination = safe_path(root, STATE_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects a baseline created by concurrent setup.
    with destination.open("xb") as stream:
        try:
            stream.write(content)
            stream.flush()
        except OSError:
            destination.unlink()
            raise
    print("Initialized installation baseline from the distribution manifest")


def check_state(root: Path, manifest: dict[str, Any]) -> None:
    """Check baseline consistency while allowing intentional local customization."""
    from .ownership import owned_content, read_bytes, validate_ownership

    state = load_state(root)
    if state is None:
        raise ValueError(
            "Ownership manifest requires .engineering/state/install.json; plan a legacy update"
        )
    if state["installed_version"] != manifest.get("template_version"):
        raise ValueError("Installed state and distribution manifest versions disagree")
    entries = object_value(state["entries"], "state.entries")
    for name, raw in object_value(manifest.get("files"), "manifest.files").items():
        item = object_value(raw, name)
        spec = validate_ownership(name, item.get("ownership"))
        if spec["mode"] == "preserve":
            continue
        entry = object_value(entries.get(name), f"state entry {name}")
        if entry.get("upstream") != item.get("owned_sha256"):
            raise ValueError(
                f"{name}: state baseline disagrees with manifest owned_sha256"
            )
        if entry.get("ownership") != spec:
            raise ValueError(f"{name}: installed ownership disagrees with manifest")
        # Local contents need not match the upstream baseline. Validate their
        # representation, never repair a baseline to hide a customization.
        owned_content(read_bytes(root, name), name, spec)
