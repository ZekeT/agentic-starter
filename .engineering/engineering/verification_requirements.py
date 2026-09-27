"""Derive required checks from the recorded installation role and path ownership."""

import tomllib
from pathlib import Path
from typing import Any

from .config import object_value
from .installation import MANIFEST_PATH, ROLES, STATE_PATH, installation_role
from .ownership import METADATA, json_object, read_bytes, validate_ownership
from .settings import CONFIGURATION, graft_navigation, provider, validate
from .source import git

# Starter tooling directories; some files are distributed, but everything here
# is maintainer source in the maintainer checkout (never consumer policy).
MAINTAINER_TOOLING = tuple(
    f".engineering/{name}/"
    for name in ("template", "tests", "evals", "scripts", "migrations")
)
PROJECT = ["make", "check"]
HEALTH = ["make", "engineering-check"]
SUITES = [["make", "engineering-test"], ["make", "engineering-evals"]]
GRAFT = [".engineering/bin/graft", "check"]


def validate_requirements(checkout: Path, plan: dict[str, Any]) -> None:
    """Require checks from recorded role and ownership, never from existing targets."""
    # The recorded role is trusted (ADR 0001); absence blocks planning. The
    # stricter of base and proposed applies, so a role change counts once merged.
    role = installation_role(checkout)
    if baseline_role(checkout) == "maintainer":
        role = "maintainer"
    configured = (checkout / CONFIGURATION).is_file()
    if configured:
        # Invalid project configuration fails planning visibly, not only doctor.
        try:
            validate(checkout, (checkout / CONFIGURATION).read_text())
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"{CONFIGURATION}: {error}") from error
    graft = configured and graft_navigation(checkout)
    if (
        GRAFT in plan["checks"]
        and configured
        and provider(checkout, "navigation") != "graft"
    ):
        raise ValueError(
            "navigation disabled: remove the Graft check from the plan, or "
            'select [navigation] provider = "graft"'
        )
    categories = classify(checkout, role, plan["paths"])
    if edited := categories["managed implementation"]:
        raise ValueError(
            f"Managed implementation edited in a consumer project: {edited}. "
            "Engineering owns these files, so verification cannot pass. Restore "
            "them; get changes through `./engineering update <project>` from a "
            "starter checkout (review the preview, then rerun with --apply), or "
            "propose the change upstream in the starter repository. Manifest "
            "digests are proposed content, so update output is not yet verifiable."
        )
    required = [PROJECT]
    if (
        categories["project configuration"]
        or categories["managed integration"]
        or categories["installation metadata"]
    ):
        required.append(HEALTH)
    # In the maintainer checkout the metadata is the ownership contract every
    # consumer receives, so it is maintainer source as well as metadata.
    if categories["maintainer source"] or (
        role == "maintainer" and categories["installation metadata"]
    ):
        required += SUITES
    if graft:
        required.append(GRAFT)
    if missing := [command for command in required if command not in plan["checks"]]:
        reasons = [
            f"{category}: {', '.join(names)}"
            for category, names in categories.items()
            if names
        ]
        if graft:
            reasons.append("configured application roots require Graft check")
        raise ValueError(
            f"Required checks missing: {missing} (role {role}; {'; '.join(reasons)})"
        )


def classify(checkout: Path, role: str, paths: list[str]) -> dict[str, list[str]]:
    """Categorize each changed path by manifest ownership and installation role."""
    proposed = manifest_files(read_bytes(checkout, MANIFEST_PATH))
    if proposed is None:
        raise ValueError(
            f"{MANIFEST_PATH} is missing; ownership cannot be classified. "
            "Restore the installation manifest before verification."
        )
    # Baseline ownership keeps a dropped entry from lowering requirements.
    base = manifest_files(baseline(checkout, MANIFEST_PATH)) or {}
    categories: dict[str, list[str]] = {
        "project configuration": [],
        "managed integration": [],
        "maintainer source": [],
        "managed implementation": [],
        "installation metadata": [],
        "project": [],
    }
    for name in sorted(paths):
        modes = {
            entry["ownership"]["mode"]
            for entry in (proposed.get(name), base.get(name))
            if entry is not None
        }
        if role == "maintainer" and (
            "file" in modes or name.startswith(MAINTAINER_TOOLING)
        ):
            category = "maintainer source"
        elif "file" in modes and read_bytes(checkout, name) != baseline(checkout, name):
            # Manifest digests are proposed content too, so they never vouch
            # for an edit or removal; the update route is not yet verifiable.
            category = "managed implementation"
        elif modes == {"preserve"}:
            category = "project configuration"
        elif modes:
            # Integration sections, hooks and unchanged distributed files.
            category = "managed integration"
        elif name in METADATA:
            category = "installation metadata"
        else:
            category = "project"
        categories[category].append(name)
    return categories


def baseline_role(checkout: Path) -> str | None:
    """The comparison base's recorded role, or None before it was recorded."""
    raw = baseline(checkout, STATE_PATH)
    role = None if raw is None else json_object(raw).get("role")
    return role if role in ROLES else None


def baseline(checkout: Path, name: str) -> bytes | None:
    """Read a path from the checkout's baseline commit, None when absent.

    Relies on materialize() having set the checkout HEAD to the plan base.
    """
    if not git(checkout, "ls-tree", "--name-only", "HEAD", "--", name):
        return None
    return git(checkout, "show", f"HEAD:{name}")


def manifest_files(raw: bytes | None) -> dict[str, Any] | None:
    """Validate the ownership of every manifest entry before trusting it."""
    if raw is None:
        return None
    files = object_value(json_object(raw).get("files"), f"{MANIFEST_PATH}: files")
    for name, entry in files.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{MANIFEST_PATH}: invalid entry {name}")
        validate_ownership(name, entry.get("ownership"))
    return files
