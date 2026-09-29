"""Read project configuration independently of installation fingerprints."""

import re
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .config import Config, object_value, read_text, safe_path, validate_config

CONFIGURATION = ".engineering/config.toml"
SCHEMA_VERSION = 2
# Review settings defaults (ADR 0002): documentation paths may use the
# documentation tier; sensitive paths add to the starter's sensitive rules.
REVIEW_DEFAULTS = (
    '[review]\ndocumentation = ["README.md", "docs/**/*.md"]\nsensitive = []\n'
)


def add_review_settings(text: str) -> str:
    """Schema 1 → 2: add default review settings, keeping every existing value."""
    text = re.sub(
        r"(?m)^(schema_version\s*=\s*)1(\s*(?:#.*)?)$", r"\g<1>2\2", text, count=1
    )
    return text.rstrip("\n") + "\n\n" + REVIEW_DEFAULTS


# MIGRATIONS[n] rewrites schema n text to schema n + 1, keeping project values.
MIGRATIONS: dict[int, Callable[[str], str]] = {1: add_review_settings}


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
        "review",
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
        "review": {"documentation", "sensitive"},
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
    review_patterns(data)
    return data


def review_patterns(data: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Review settings as documentation and sensitive glob lists (empty if unset)."""
    review = object_value(data.get("review", {}), "review")
    if set(review) - {"documentation", "sensitive"}:
        raise ValueError("config.unknown: review")
    result = {}
    for key in ("documentation", "sensitive"):
        patterns = review.get(key, [])
        if not isinstance(patterns, list) or not all(
            isinstance(pattern, str) and pattern.strip() for pattern in patterns
        ):
            raise ValueError(f"review.{key} must be a list of path patterns")
        result[key] = tuple(patterns)
    return result


def review_settings(raw: bytes | None) -> dict[str, tuple[str, ...]]:
    """Review settings from configuration bytes of any schema; absent means none."""
    try:
        return review_patterns(tomllib.loads(raw.decode()) if raw is not None else {})
    except (tomllib.TOMLDecodeError, UnicodeDecodeError, ValueError) as error:
        raise ValueError(f"{CONFIGURATION} review settings: {error}") from error


def selected_provider(config: dict[str, Any], capability: str) -> str:
    """Name the provider parsed configuration selects for an optional capability."""
    default = CAPABILITIES[capability][0]
    return str(config.get(capability, {}).get("provider", default))


def provider(root: Path, capability: str) -> str:
    """Name the provider an optional capability selects; "none" disables it."""
    return selected_provider(load(root), capability)


def graft_navigation(root: Path) -> bool:
    """Graft navigation applies only while selected with application roots configured."""
    return provider(root, "navigation") == "graft" and bool(
        load(root).get("navigation", {}).get("application_roots")
    )
