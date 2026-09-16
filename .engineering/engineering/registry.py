"""Validate the concrete managed upstream dependencies and installation evidence."""

import re
import tomllib
from pathlib import Path
from typing import Any

from .config import object_value, read_text, safe_path
from .ownership import digest, json_object, read_bytes

REGISTRY = ".engineering/dependencies.toml"
STATE = ".engineering/state/dependencies.json"
SOURCES = {
    "matt-skills": ("skills", "mattpocock/skills"),
    "graft": ("npm", "@nanonets/graft"),
    "show-me": ("skills", "humanlayer/skills"),
    "karpathy-guidelines": ("skills", "multica-ai/andrej-karpathy-skills"),
}


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
                else path
                in {
                    ".engineering/graft/package.json",
                    ".engineering/graft/package-lock.json",
                    ".claude/skills/graft/SKILL.md",
                }
            )
            if not allowed:
                raise ValueError(f"deps.state: unexpected managed output {path}")
            if not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
                raise ValueError(f"deps.state: invalid output digest {path}")
    return data


def installed_status(
    root: Path, dependency: dict[str, Any], evidence: dict[str, Any]
) -> tuple[str, str]:
    """Compare installed bytes with recorded pins, entirely offline."""
    row = evidence.get(dependency["id"])
    if row is None:
        return "missing", "MISSING" if dependency["required"] else "OPTIONAL"
    for name, sha in row["outputs"].items():
        if digest(read_bytes(root, name)) != sha:
            return str(row["installed_version"]), "MODIFIED"
    version = str(row["installed_version"])
    if dependency["kind"] == "npm":
        package = json_object(
            read_bytes(
                root, ".engineering/graft/node_modules/@nanonets/graft/package.json"
            )
            or b"{}"
        )
        if package.get("version") != version:
            return version, "MISSING"
    else:
        for skill in dependency["skills"]:
            path = f".claude/skills/{skill}/SKILL.md"
            if path not in row["outputs"] or not read_bytes(root, path):
                return version, "MISSING"
    return version, "OK" if version == dependency["version"] else "PIN DIFFERS"
