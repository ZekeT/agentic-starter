"""Validate factory configuration while preserving project-owned overrides."""

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

DEFAULTS: dict[str, Any] = {
    "enabled": True,
    "warn_file_lines": 300,
    "max_file_lines": 500,
    "substantial_growth_lines": 150,
    "exceptions": [],
}


@dataclass(frozen=True)
class Config:
    """Validated code-line thresholds and reasoned exceptions."""

    enabled: bool = True
    warn_file_lines: int = 300
    max_file_lines: int = 500
    substantial_growth_lines: int = 150
    exceptions: dict[str, str] = field(default_factory=dict)


def safe_path(root: Path, name: str) -> Path:
    """Reject ambiguous paths and symlinks before inspecting repository files."""
    rel = PurePosixPath(name)
    if (
        not name
        or rel.is_absolute()
        or ".." in rel.parts
        or rel.as_posix() != name
        or "\\" in name
        or any(c in name for c in "*?[]")
        or any(p == ".git" or p == ".env" or p.startswith(".env.") for p in rel.parts)
    ):
        raise ValueError(f"Unsafe source path: {name}")
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"Symlink source path is unsupported: {name}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Source path escapes repository: {name}")
    return path


def object_value(value: Any, label: str) -> dict[str, Any]:
    """Require a JSON object with a useful diagnostic."""
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def load_config(root: Path) -> Config:
    """Read defaults and project overrides from the existing template manifest."""
    path = safe_path(root, ".harness/template-manifest.json")
    data = object_value(json.loads(path.read_text()), "manifest")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError(
            "Unsupported manifest schema_version; refresh the factory manifest"
        )
    merged = dict(DEFAULTS)
    for section in ("defaults", "project"):
        group = object_value(data.get(section, {}), section)
        if set(group) - {"maintainability"}:
            raise ValueError(
                f"Unknown {section} configuration: {sorted(set(group) - {'maintainability'})}"
            )
        values = object_value(
            group.get("maintainability", {}), section + ".maintainability"
        )
        if set(values) - DEFAULTS.keys():
            raise ValueError(
                f"Unknown maintainability settings: {sorted(set(values) - DEFAULTS.keys())}"
            )
        merged.update(values)
    if type(merged["enabled"]) is not bool:
        raise ValueError("maintainability.enabled must be boolean")
    for key in ("warn_file_lines", "max_file_lines", "substantial_growth_lines"):
        if type(merged[key]) is not int or merged[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if merged["warn_file_lines"] >= merged["max_file_lines"]:
        raise ValueError("warn_file_lines must be below max_file_lines")
    if not isinstance(merged["exceptions"], list):
        raise ValueError("exceptions must be a list of path/reason objects")
    exceptions: dict[str, str] = {}
    for entry in merged["exceptions"]:
        entry = object_value(entry, "exception")
        name, reason = entry.get("path"), entry.get("reason")
        if set(entry) != {"path", "reason"} or not isinstance(name, str):
            raise ValueError("Each exception requires exactly path and reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"Exception {name} requires a nonempty reason")
        if name in exceptions:
            raise ValueError(f"Duplicate exception path: {name}")
        if not safe_path(root, name).is_file():
            raise ValueError(f"Exception path does not exist: {name}")
        exceptions[name] = reason.strip()
    return Config(**{**merged, "exceptions": exceptions})


def initialize_manifest(root: Path) -> None:
    """Add growth configuration to a legacy installation without losing overrides."""
    path = safe_path(root, ".harness/template-manifest.json")
    data = (
        object_value(json.loads(path.read_text()), "manifest") if path.exists() else {}
    )
    if "schema_version" in data and data["schema_version"] != 1:
        raise ValueError("Cannot initialize unsupported manifest schema_version")
    data.setdefault("schema_version", 1)
    data.setdefault("defaults", {"maintainability": dict(DEFAULTS)})
    data.setdefault("project", {})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
