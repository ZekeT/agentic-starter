"""Read project configuration independently of installation fingerprints."""

import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .config import Config, object_value, read_text, safe_path, validate_config

CONFIGURATION = ".engineering/config.toml"
SCHEMA_VERSION = 1
# MIGRATIONS[n] rewrites schema n text to schema n + 1, keeping project values.
MIGRATIONS: dict[int, Callable[[str], str]] = {}


class MigrationGap(ValueError):
    """The starter lacks a working schema step; the project cannot repair it."""


# Optional capabilities: each is selected by its section's provider (first is default).
CAPABILITIES = {"navigation": ("graft", "none")}


def load(root: Path) -> dict[str, Any]:
    """Reject unknown schemas and malformed policy before any operation."""
    return parse(root, read_text(root, CONFIGURATION))


def migrate(text: str) -> tuple[str, list[str]]:
    """Apply ordered schema migrations; unsupported versions fail in parse."""
    notes = []
    version = tomllib.loads(text).get("schema_version")
    while type(version) is int and 0 < version < SCHEMA_VERSION:
        step = MIGRATIONS.get(version)
        if step is None:
            raise MigrationGap(f"config.schema: no migration from version {version}")
        text = step(text)
        if tomllib.loads(text).get("schema_version") != version + 1:
            raise MigrationGap(f"config.schema: migration from {version} failed")
        notes.append(f"schema_version {version} → {version + 1}")
        version += 1
    return text, notes


def validate(root: Path, text: str) -> Config:
    """Check the complete configuration, including maintainability thresholds."""
    maintainability = parse(root, text).get("maintainability", {})
    return validate_config(
        root, {"schema_version": 1, "project": {"maintainability": maintainability}}
    )


def parse(root: Path, text: str) -> dict[str, Any]:
    """Validate configuration text against the current schema."""
    data = tomllib.loads(text)
    version = data.get("schema_version")
    if type(version) is not int or version != SCHEMA_VERSION:
        hint = (
            "; run engineering update to migrate it"
            if type(version) is int and 0 < version < SCHEMA_VERSION
            else ""
        )
        raise ValueError(
            f"config.schema: expected schema_version = {SCHEMA_VERSION}{hint}"
        )
    allowed = {
        "schema_version",
        "navigation",
        "verification",
        "documentation",
        "tracker",
        "maintainability",
        "migration",
        *CAPABILITIES,
    }
    if set(data) - allowed:
        raise ValueError(f"config.unknown: {sorted(set(data) - allowed)}")
    fields = {
        "navigation": {"provider", "application_roots"},
        "verification": {"base_branch"},
        "documentation": {"require_feature_docs"},
        "tracker": {"provider", "configuration"},
        "migration": {"legacy_history"},
    }
    for section, keys in fields.items():
        value = object_value(data.get(section, {}), section)
        if set(value) - keys:
            raise ValueError(f"config.unknown: {section}")
    for capability, providers in CAPABILITIES.items():
        # Every capability section is validated, including ones added later.
        chosen = object_value(data.get(capability, {}), capability)
        if chosen.get("provider", providers[0]) not in providers:
            raise ValueError(
                f"{capability}.provider must be one of: {', '.join(providers)}"
            )
    roots = data.get("navigation", {}).get("application_roots", [])
    if not isinstance(roots, list) or any(not isinstance(p, str) for p in roots):
        raise ValueError("navigation.application_roots must be a list of directories")
    if not isinstance(data.get("verification", {}).get("base_branch", ""), str):
        raise ValueError("verification.base_branch must be text")
    if (
        type(data.get("documentation", {}).get("require_feature_docs", True))
        is not bool
    ):
        raise ValueError("documentation.require_feature_docs must be boolean")
    tracker = data.get("tracker", {})
    if tracker.get("provider", "local-markdown") not in {
        "local-markdown",
        "github",
        "other",
    }:
        raise ValueError("tracker.provider must be local-markdown, github, or other")
    pointer = tracker.get("configuration", "docs/agents/issue-tracker.md")
    if not isinstance(pointer, str):
        raise ValueError("tracker.configuration must be a repository path")
    safe_path(root, pointer)
    if data.get("migration", {}).get("legacy_history", "snapshot") not in {
        "snapshot",
        "git-only",
    }:
        raise ValueError("migration.legacy_history must be snapshot or git-only")
    return data


def provider(root: Path, capability: str) -> str:
    """Name the provider an optional capability selects; "none" disables it."""
    return str(
        load(root).get(capability, {}).get("provider", CAPABILITIES[capability][0])
    )


def graft_navigation(root: Path) -> bool:
    """Graft navigation applies only while selected with application roots configured."""
    return provider(root, "navigation") == "graft" and bool(
        load(root).get("navigation", {}).get("application_roots")
    )
