"""Read project policy independently of installation fingerprints."""

import tomllib
from pathlib import Path
from typing import Any

from .config import object_value, read_text, safe_path


def load(root: Path) -> dict[str, Any]:
    """Reject unknown schemas and malformed policy before any operation."""
    data = tomllib.loads(read_text(root, ".engineering/config.toml"))
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("config.schema: expected schema_version = 1")
    allowed = {
        "schema_version",
        "navigation",
        "verification",
        "documentation",
        "tracker",
        "maintainability",
        "migration",
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
    if data.get("navigation", {}).get("provider", "graft") != "graft":
        raise ValueError("navigation.provider must be graft")
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
