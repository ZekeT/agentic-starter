"""Derive required checks from the recorded installation role and path ownership."""

from pathlib import Path
from typing import Any

from .installation import MANIFEST_PATH, installation_role
from .ownership import digest, json_object, read_bytes, validate_ownership
from .settings import CONFIGURATION, graft_navigation, validate
from .source import git

# Starter tooling that is never distributed; it is maintainer source there only.
MAINTAINER_TOOLING = tuple(
    f".engineering/{name}/"
    for name in ("template", "tests", "evals", "scripts", "migrations")
)
PROJECT = ["make", "check"]
HEALTH = ["make", "engineering-check"]
SUITES = [["make", "engineering-test"], ["make", "engineering-evals"]]
GRAFT = [".engineering/bin/graft", "check"]


def validate_requirements(checkout: Path, plan: dict[str, Any]) -> None:
    """Require checks from proposed role and ownership, never from existing targets."""
    # The proposed recorded role is trusted (ADR 0001); absence blocks planning.
    role = installation_role(checkout)
    configured = (checkout / CONFIGURATION).is_file()
    if configured:
        # Invalid project configuration fails planning visibly, not only doctor.
        validate(checkout, (checkout / CONFIGURATION).read_text())
    graft = configured and graft_navigation(checkout)
    categories = classify(checkout, role, plan["paths"])
    if edited := categories["managed implementation"]:
        raise ValueError(
            f"Managed implementation edited in a consumer project: {edited}. "
            "Engineering owns these files, so verification cannot pass. Restore "
            "them; get changes through `./engineering update <project>` from a "
            "starter checkout (review the preview, then rerun with --apply), or "
            "propose the change upstream in the starter repository."
        )
    required = [PROJECT]
    if categories["project configuration"] or categories["managed integration"]:
        required.append(HEALTH)
    if categories["maintainer source"]:
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
    baseline = manifest_files(baseline_manifest(checkout)) or {}
    categories: dict[str, list[str]] = {
        "project configuration": [],
        "managed integration": [],
        "maintainer source": [],
        "managed implementation": [],
        "project": [],
    }
    for name in sorted(paths):
        modes = {
            entry["ownership"]["mode"]
            for entry in (proposed.get(name), baseline.get(name))
            if entry is not None
        }
        if role == "maintainer" and (
            "file" in modes or name.startswith(MAINTAINER_TOOLING)
        ):
            category = "maintainer source"
        elif "file" in modes and not distributed(checkout, name, proposed.get(name)):
            category = "managed implementation"
        elif modes == {"preserve"}:
            category = "project configuration"
        elif modes:
            # Integration sections, hooks and consumer bytes matching the
            # proposed distribution (the update route's output); doctor checks them.
            category = "managed integration"
        else:
            category = "project"
        categories[category].append(name)
    return categories


def distributed(checkout: Path, name: str, entry: dict[str, Any] | None) -> bool:
    """Proposed bytes equal the proposed manifest, including an update's removal."""
    content = read_bytes(checkout, name)
    if entry is None or entry["ownership"]["mode"] != "file":
        return content is None
    return content is not None and digest(content) == entry.get("sha256")


def baseline_manifest(checkout: Path) -> bytes | None:
    """Read the comparison base's manifest from the checkout's baseline commit."""
    if not git(checkout, "ls-tree", "--name-only", "HEAD", "--", MANIFEST_PATH):
        return None
    return git(checkout, "show", f"HEAD:{MANIFEST_PATH}")


def manifest_files(raw: bytes | None) -> dict[str, Any] | None:
    """Validate the ownership of every manifest entry before trusting it."""
    if raw is None:
        return None
    files = json_object(raw).get("files")
    if not isinstance(files, dict):
        raise ValueError(f"{MANIFEST_PATH}: files must be an object")
    for name, entry in files.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{MANIFEST_PATH}: invalid entry {name}")
        validate_ownership(name, entry.get("ownership"))
    return files
