"""Derive required checks, tier floor and reviewer roles for a verification plan."""

import tomllib
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any

from .config import object_value
from .installation import MANIFEST_PATH, ROLES, STATE_PATH, installation_role
from .ownership import METADATA, json_object, read_bytes, validate_ownership
from .settings import (
    CONFIGURATION,
    graft_navigation,
    provider,
    review_settings,
    validate,
)
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

# Review tiers in increasing order, with the reviewer roles each requires.
TIERS = ("documentation", "ordinary", "sensitive")
REVIEWERS = {
    "documentation": ["behavioral"],
    "ordinary": ["maintainability", "behavioral"],
    "sensitive": ["maintainability", "behavioral", "security"],
}
# Starter-owned floor rules (ADR 0002); projects may add to them, never remove.
# A pattern without "/" matches a file name at any depth; others match the
# repository path, where "*" also crosses directories. A leading "/" anchors a
# pattern without another "/" to the repository root. Project review settings
# use the same pattern rules.
STARTER_SENSITIVE = {
    "dependency manifest or lock": (
        "pyproject.toml",
        "uv.lock",
        "package*.json",
        "*package-lock.json",
        ".engineering/dependencies.toml",
    ),
    "agent settings": (".claude/settings*.json",),
    "hook": (".claude/hooks/**",),
    "workflow": (".github/workflows/**",),
    "build recipe": ("Makefile", "GNUmakefile", "makefile", "*.mk"),
    "check script": (".engineering/scripts/**",),
    "agent-executed script": (".claude/statusline.sh",),
    "Engineering launcher": (
        "/engineering",
        ".engineering/bin/**",
        ".engineering/setup.sh",
    ),
}
MODULES = ".engineering/engineering/"
# Maintainer modules that execute dependencies, or destroy or publish data.
MAINTAINER_SENSITIVE = {
    "dependency module": (
        f"{MODULES}deps.py",
        f"{MODULES}registry.py",
        f"{MODULES}graft.py",
    ),
    "skill installation module": (f"{MODULES}skill_install.py",),
    "apply or transaction module": (f"{MODULES}apply.py", f"{MODULES}transaction.py"),
    "update module": (
        f"{MODULES}adoption.py",
        f"{MODULES}installation.py",
        f"{MODULES}updates.py",
    ),
    "migration module": (f"{MODULES}migrate/**", ".engineering/migrations/**"),
    "publication module": (f"{MODULES}publication*.py",),
    "verification module": (f"{MODULES}verification*.py",),
}
# Agent-policy files are never documentation: they change how agents behave.
AGENT_POLICY = (
    "CLAUDE.md",
    "AGENTS.md",
    "REVIEW.md",
    "ENGINEERING.md",
    ".claude/**",
    ".engineering/docs/**",
    "docs/agents/**",
)


def requirements(checkout: Path, plan: dict[str, Any]) -> dict[str, Any]:
    """Required checks, tier floor, per-path floor rules and reviewer roles.

    Rejects a plan that omits a required check or declares a tier below the
    floor. Checks come from recorded role and ownership, never from existing
    targets; the tier changes reviewers, never checks.
    """
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
    paths = tier_paths(role, plan["paths"], base_and_proposed_settings(checkout))
    floor = max((tier for tier in TIERS if paths[tier]), key=TIERS.index)
    if TIERS.index(plan["tier"]) < TIERS.index(floor):
        reasons = [f"{name} ({rule})" for name, rule in paths[floor].items()]
        raise ValueError(
            f"Declared tier {plan['tier']} is below the tier floor {floor}: "
            f"{', '.join(reasons)}. Declare at least {floor}."
        )
    return {
        "floor": floor,
        "paths": paths,
        "checks": required,
        "roles": REVIEWERS[plan["tier"]],
    }


def tier_paths(
    role: str, paths: list[str], settings: list[dict[str, tuple[str, ...]]]
) -> dict[str, dict[str, str]]:
    """Floor each path under every review settings version; the highest tier wins."""
    result: dict[str, dict[str, str]] = {tier: {} for tier in reversed(TIERS)}
    for name in sorted(paths):
        tier, rule = max(
            (path_floor(role, name, review) for review in settings),
            key=lambda floor: TIERS.index(floor[0]),
        )
        result[tier][name] = rule
    return result


def path_floor(
    role: str, name: str, review: dict[str, tuple[str, ...]]
) -> tuple[str, str]:
    """The first matching rule; starter rules precede project settings."""
    sensitive = dict(STARTER_SENSITIVE)
    if role == "maintainer":
        sensitive.update(MAINTAINER_SENSITIVE)
    sensitive["project sensitive setting"] = review["sensitive"]
    for rule, patterns in sensitive.items():
        if matches(name, patterns):
            return "sensitive", rule
    if matches(name, AGENT_POLICY):
        return "ordinary", "agent policy"
    if name == CONFIGURATION:
        # Changing review settings is itself reviewed, whatever they list.
        return "ordinary", "review settings"
    if matches(name, review["documentation"]):
        return "documentation", "project documentation setting"
    return "ordinary", "no documentation rule"


def base_and_proposed_settings(checkout: Path) -> list[dict[str, tuple[str, ...]]]:
    """Base and proposed review settings; a change cannot weaken its own floor.

    Starter lists are code in a module that is sensitive in the maintainer
    checkout and managed implementation elsewhere, so base and proposed agree
    whenever verification can pass (ADR 0002).
    """
    return [
        review_settings(baseline(checkout, CONFIGURATION)),
        review_settings(read_bytes(checkout, CONFIGURATION)),
    ]


def matches(name: str, patterns: tuple[str, ...]) -> bool:
    """Match file-name patterns at any depth and path patterns from the root."""
    return any(
        fnmatchcase(name, pattern.removeprefix("/"))
        if "/" in pattern
        else fnmatchcase(PurePosixPath(name).name, pattern)
        for pattern in patterns
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
