"""Remove explicit OpenSpec wiring while retaining unrelated project settings."""

import re

from ..config import object_value
from ..ownership import encoded, json_object, read_bytes
from .common import Migration

PACKAGE = "@fission-ai/openspec"
SECTIONS = ("dependencies", "devDependencies", "optionalDependencies")


def cleanup(plan: Migration) -> dict[str, bytes]:
    """Rewrite only known markers and npm dependency entries; never run npm."""
    originals = {}
    for name in ("CLAUDE.md", "AGENTS.md"):
        raw = read_bytes(plan.root, name)
        if raw is None or b"<!-- OPENSPEC:" not in raw:
            continue
        start, end = b"<!-- OPENSPEC:START -->", b"<!-- OPENSPEC:END -->"
        match = re.search(
            rb"(?ms)^"
            + re.escape(start)
            + rb"\r?\n.*?^"
            + re.escape(end)
            + rb"(?:\r?\n|\Z)",
            raw,
        )
        if raw.count(start) != 1 or raw.count(end) != 1 or match is None:
            plan.conflicts.append(
                f"migration.markers: malformed OpenSpec region in {name}"
            )
            continue
        originals[name] = raw
        plan.add(name, raw[: match.start()] + raw[match.end() :], replace=True)
    package_raw = read_bytes(plan.root, "package.json")
    if package_raw is None:
        return originals
    package = json_object(package_raw)
    changed = False
    for section in SECTIONS:
        values = object_value(package.get(section, {}), section)
        if PACKAGE in values:
            del values[PACKAGE]
            changed = True
    if not changed:
        return originals
    for name in (
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lock",
        "bun.lockb",
        "npm-shrinkwrap.json",
    ):
        if read_bytes(plan.root, name) is not None:
            plan.conflicts.append(
                f"migration.package_manager: remove {PACKAGE} using the project's package manager and re-plan; preserve {name}"
            )
    originals["package.json"] = package_raw
    plan.add("package.json", encoded(package), replace=True)
    lock_raw = read_bytes(plan.root, "package-lock.json")
    if lock_raw is not None:
        lock = json_object(lock_raw)
        if lock.get("lockfileVersion") not in {2, 3}:
            plan.conflicts.append(
                "migration.lockfile: unsupported npm lock version; remove OpenSpec with the project package manager and re-plan"
            )
            return originals
        packages = object_value(lock.get("packages"), "lock.packages")
        for section in SECTIONS:
            object_value(packages.get("", {}).get(section, {}), section).pop(
                PACKAGE, None
            )
        needed = any(
            PACKAGE in item.get(section, {})
            for name, item in packages.items()
            if name
            for section in SECTIONS
        )
        if not needed:
            packages.pop(f"node_modules/{PACKAGE}", None)
            object_value(lock.get("dependencies", {}), "lock.dependencies").pop(
                PACKAGE, None
            )
        originals["package-lock.json"] = lock_raw
        plan.add("package-lock.json", encoded(lock), replace=True)
    plan.notes.append(
        "Remove the direct OpenSpec npm dependency; preserve unrelated packages and scripts. Review custom script references manually."
    )
    return originals
