"""Reconcile legacy installation metadata without advancing preserved baselines."""

import json
import re
from pathlib import Path

from .config import initialize_manifest, object_value, safe_path
from .graft import IGNORES


def installation_version(root: Path) -> str | None:
    """Read existing version authorities and reject invalid or conflicting values."""
    versions: dict[str, str] = {}
    for name in (
        ".harness/template-manifest.json",
        ".harness/TEMPLATE_VERSION",
        ".claude/template-version.json",
    ):
        path = safe_path(root, name)
        if not path.exists():
            continue
        if not path.is_file():
            raise ValueError(f"{name}: expected a regular file")
        if name.endswith(".json"):
            data = object_value(json.loads(path.read_text()), name)
            # Old growth-only manifests did not record an installed version.
            if (
                name == ".harness/template-manifest.json"
                and "template_version" not in data
            ):
                continue
            version = data.get("template_version")
        else:
            version = path.read_text().strip()
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


def inspect_legacy_metadata(root: Path) -> str | None:
    """Validate metadata and ignore destinations before any migration writes."""
    ignore = safe_path(root, ".gitignore")
    if ignore.exists() and not ignore.is_file():
        raise ValueError(".gitignore: expected a regular file")
    version = installation_version(root)
    manifest = safe_path(root, ".harness/template-manifest.json")
    if manifest.exists():
        data = object_value(json.loads(manifest.read_text()), "manifest")
        if "schema_version" in data and (
            type(data["schema_version"]) is not int or data["schema_version"] != 1
        ):
            raise ValueError("Cannot initialize unsupported manifest schema_version")
        object_value(data.get("files", {}), "manifest.files")
    return version


def complete_installation_metadata(
    target: Path, starter: Path, copied: list[str]
) -> None:
    """Preserve installed versions and fingerprints; append installation ignores."""
    version = inspect_legacy_metadata(target)
    upstream = object_value(
        json.loads(safe_path(starter, ".harness/template-manifest.json").read_text()),
        "upstream manifest",
    )
    upstream_version = installation_version(starter)
    if upstream_version is None:
        raise ValueError("Upstream template_version is missing")
    initialize_manifest(target)
    path = safe_path(target, ".harness/template-manifest.json")
    data = object_value(json.loads(path.read_text()), "manifest")
    data.setdefault("template_version", version or upstream_version)
    files = object_value(data.setdefault("files", {}), "manifest.files")
    for name in copied:
        if name in upstream["files"]:
            files.setdefault(name, upstream["files"][name])
    path.write_text(json.dumps(data, indent=2) + "\n")
    ignore = safe_path(target, ".gitignore")
    prior = ignore.read_text() if ignore.exists() else ""
    required = (".env", ".env.*", "*.pem", "*.key", *IGNORES)
    missing = [line for line in required if line not in prior.splitlines()]
    if missing or "!.env.template" not in prior.splitlines():
        missing.append("!.env.template")
    if missing:
        gap = "\n" if prior and not prior.endswith("\n") else ""
        ignore.write_text(prior + gap + "\n".join(missing) + "\n")
