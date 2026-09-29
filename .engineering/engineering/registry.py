"""Validate the concrete managed upstream dependencies and installation evidence."""

import re
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

from . import graft
from .config import object_value, read_text, safe_path
from .ownership import digest, json_object, owned_content, read_bytes
from .settings import CAPABILITIES, provider

REGISTRY = ".engineering/dependencies.toml"
STATE = ".engineering/state/dependencies.json"
SOURCES = {
    "matt-skills": ("skills", "mattpocock/skills"),
    "graft": ("npm", "@nanonets/graft"),
    "show-me": ("skills", "humanlayer/skills"),
    "karpathy-guidelines": ("skills", "multica-ai/andrej-karpathy-skills"),
}

# Modules owning the content a dependency installs besides skills, by dependency id.
CONTENT_OWNERS: dict[str, ModuleType] = {"graft": graft}


def content(dependency: str) -> tuple[str, ...]:
    """Name the content a dependency installs besides skills."""
    owner = CONTENT_OWNERS.get(dependency)
    return owner.CONTENT if owner else ()


def output_scope(dependency: str, path: str) -> dict[str, Any]:
    """Outputs are whole files unless the dependency's content owner bounds them."""
    owner = CONTENT_OWNERS.get(dependency)
    return owner.output_scope(path) if owner else {"mode": "file"}


def generated(dependency: str, path: str) -> bytes | None:
    """Return fixed content the dependency's content owner generates for a path."""
    owner = CONTENT_OWNERS.get(dependency)
    return owner.generated(path) if owner else None


def registry(root: Path) -> dict[str, Any]:
    """Keep source execution bounded to the four supported integrations."""
    data = tomllib.loads(read_text(root, REGISTRY))
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("deps.schema: registry schema_version must be 1")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(data.get("skills_installer"))):
        raise ValueError("deps.installer: require an exact installer version")
    rows = data.get("dependency")
    if not isinstance(rows, list):
        raise ValueError("deps.registry: dependency must be an array")
    ids, skills = set(), set()
    for raw in rows:
        row = object_value(raw, "dependency")
        name = row.get("id")
        if not isinstance(name, str) or name in ids or name not in SOURCES:
            raise ValueError(f"deps.id: unknown or duplicate dependency {name}")
        ids.add(name)
        if (row.get("kind"), row.get("source")) != SOURCES[name]:
            raise ValueError(f"deps.source: unsupported source for {name}")
        pattern = r"[0-9a-f]{40}" if row["kind"] == "skills" else r"\d+\.\d+\.\d+"
        if not re.fullmatch(pattern, str(row.get("version"))):
            raise ValueError(
                f"deps.pin: {name} requires an immutable commit/exact version"
            )
        if type(row.get("required")) is not bool:
            raise ValueError(f"deps.required: {name} requires a boolean")
        capability = row.get("capability")
        if capability is not None and (
            not isinstance(capability, str) or capability not in CAPABILITIES
        ):
            raise ValueError(f"deps.capability: {name} names an unknown capability")
        if capability is not None and (
            name not in CAPABILITIES[capability] or name == "none"
        ):
            raise ValueError(
                f"deps.capability: {name} is not a {capability} provider value"
            )
        if row["kind"] == "skills":
            names = row.get("skills")
            if not isinstance(names, list) or not names:
                raise ValueError(f"deps.skills: missing capabilities for {name}")
            for skill in names:
                if (
                    not isinstance(skill, str)
                    or not re.fullmatch(r"[a-z][a-z0-9-]*", skill)
                    or skill in skills
                ):
                    raise ValueError(
                        f"deps.skills: invalid or duplicate capability {skill}"
                    )
                skills.add(skill)
    if not {"matt-skills", "graft"} <= ids:
        raise ValueError("deps.required: registry must include Matt and Graft")
    return data


def state(root: Path) -> dict[str, Any]:
    """Read bookkeeping without taking ownership of global installations."""
    data = json_object(
        read_bytes(root, STATE) or b'{"schema_version":1,"dependencies":{}}'
    )
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("deps.state: unsupported schema")
    for name, raw in object_value(data.get("dependencies"), "dependencies").items():
        row = object_value(raw, name)
        if name not in SOURCES or row.get("managed") is not True:
            raise ValueError(f"deps.state: unknown unmanaged entry {name}")
        kind, source = SOURCES[name]
        pattern = r"[0-9a-f]{40}" if kind == "skills" else r"\d+\.\d+\.\d+"
        if row.get("installed_from") != source or not re.fullmatch(
            pattern, str(row.get("installed_version"))
        ):
            raise ValueError(f"deps.state: invalid installed source/version for {name}")
        for path, sha in object_value(row.get("outputs"), "outputs").items():
            safe_path(root, path)
            allowed = (
                path.startswith(".claude/skills/")
                if kind == "skills"
                else path in content(name)
            )
            if not allowed:
                raise ValueError(f"deps.state: unexpected managed output {path}")
            if not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
                raise ValueError(f"deps.state: invalid output digest {path}")
    return data


def output_digest(root: Path, dependency: str, path: str) -> str | None:
    """Fingerprint only the part of a file that a dependency output owns."""
    scope = output_scope(dependency, path)
    return digest(owned_content(read_bytes(root, path), path, scope))


def selected(root: Path, dependency: dict[str, Any]) -> bool:
    """A capability's dependency applies only while that capability's provider names it."""
    capability = dependency.get("capability")
    return capability is None or provider(root, capability) == dependency["id"]


def required(root: Path, dependency: dict[str, Any]) -> bool:
    """Apply the single rule used by dependency status, setup and doctor."""
    return bool(dependency["required"]) and selected(root, dependency)


def installed_status(
    root: Path, dependency: dict[str, Any], evidence: dict[str, Any]
) -> tuple[str, str]:
    """Compare installed bytes with recorded pins, entirely offline."""
    row = evidence.get(dependency["id"])
    if not selected(root, dependency):
        # Unselected dependencies are left untouched, whatever their recorded state.
        installed = "missing" if row is None else str(row["installed_version"])
        return installed, f"NOT SELECTED ({dependency['capability']})"
    if row is None:
        return "missing", "MISSING" if dependency["required"] else "OPTIONAL"
    name = dependency["id"]
    for path, sha in row["outputs"].items():
        if output_digest(root, name, path) != sha:
            return str(row["installed_version"]), "MODIFIED"
    version = str(row["installed_version"])
    # Installations predating complete owned content reinstall it.
    if set(content(name)) - set(row["outputs"]):
        return (
            version,
            "UPGRADE REQUIRED (installation record lacks navigation outputs)",
        )
    # Fixed content from an earlier release is refreshed by reinstalling.
    for path in content(name):
        fixed = generated(name, path)
        if fixed is not None and row["outputs"][path] != digest(fixed):
            return version, "OUTDATED"
    owner = CONTENT_OWNERS.get(name)
    if owner is not None and owner.installed_version(root) != version:
        return version, "MISSING"
    for skill in dependency.get("skills", []):
        path = f".claude/skills/{skill}/SKILL.md"
        if path not in row["outputs"] or not read_bytes(root, path):
            return version, "MISSING"
    return version, "OK" if version == dependency["version"] else "PIN DIFFERS"
