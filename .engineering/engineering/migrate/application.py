"""Validate the small, human-reviewed OpenSpec application contract."""

import re
from pathlib import Path
from typing import Any

from ..config import safe_path
from ..ownership import digest, json_object, read_bytes
from ..settings import load
from ..source import git
from .openspec import WORKSPACE

CANONICAL = {
    "KEEP_AS_CONTEXT",
    "KEEP_AS_ADR",
    "KEEP_AS_FEATURE_DOC",
    "REPRESENTED_BY_CODE_OR_TESTS_DROP",
    "OBSOLETE_DROP",
    "CONFLICT_REQUIRES_HUMAN",
    "UNCERTAIN_REQUIRES_HUMAN",
}
ROUTES = {
    "PLANNING": {"wayfinder"},
    "DECIDED_NOT_IMPLEMENTED": {"to-spec"},
    "PARTIALLY_IMPLEMENTED": {"wayfinder", "to-spec", "to-tickets"},
    "IMPLEMENTED_NOT_CLOSED": {"none"},
    "OBSOLETE": {"none"},
    "UNKNOWN": {"human"},
}


def fields(value: Any, expected: set[str]) -> dict[str, Any]:
    """Refuse extension fields and malformed record shapes."""
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"migration.manifest: expected fields {sorted(expected)}")
    return value


def strings(value: Any, *, nonempty: bool = False) -> list[str]:
    """Validate statement arrays without interpreting their prose."""
    if not isinstance(value, list) or any(
        not isinstance(x, str) or not x.strip() for x in value
    ):
        raise ValueError("migration.manifest: expected nonempty text statements")
    if nonempty and not value:
        raise ValueError("migration.manifest: evidence is required")
    return value


def sha(value: Any) -> str:
    """Require the exact lowercase SHA-256 representation."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("migration.manifest: invalid SHA-256")
    return value


def evidence(root: Path, names: Any, head: str) -> None:
    """Bind every cited regular file to reviewed application history."""
    for name in strings(names, nonempty=True):
        raw = read_bytes(root, name)
        if raw is None or git(root, "show", f"{head}:{name}") != raw:
            raise ValueError(f"migration.stale: evidence {name}")


def semantics(root: Path, data: dict[str, Any], inventory: dict[str, Any]) -> None:
    """Require full canonical/active coverage and refuse unresolved semantics."""
    covered = set()
    canonical = {item["path"] for item in inventory["canonical"]}
    for item in data["canonical"]:
        fields(item, {"source", "classification", "evidence", "reason"})
        if item["source"] not in canonical or item["classification"] not in CANONICAL:
            raise ValueError(
                "migration.manifest: invalid canonical classification/source"
            )
        strings([item["reason"]], nonempty=True)
        if item["classification"].endswith("REQUIRES_HUMAN"):
            raise ValueError("migration.unresolved: canonical decision requires human")
        evidence(root, item["evidence"], data["reviewed_head"])
        covered.add(item["source"])
    if covered != canonical:
        raise ValueError("migration.coverage: canonical sources missing")
    active = {item["name"] for item in inventory["active_changes"]}
    covered = set()
    for item in data["active"]:
        fields(
            item,
            {
                "source",
                "state",
                "route",
                "evidence",
                "implemented",
                "remaining",
                "missing_tests",
                "decisions",
            },
        )
        if item["source"] not in active or item["source"] in covered:
            raise ValueError("migration.coverage: invalid/duplicate active source")
        if item["state"] not in ROUTES or item["route"] not in ROUTES[item["state"]]:
            raise ValueError("migration.manifest: invalid active route/state")
        if item["state"] == "UNKNOWN":
            raise ValueError("migration.unresolved: unknown active work")
        for key in ("implemented", "remaining", "missing_tests", "decisions"):
            strings(item[key])
        if item["state"] in {"IMPLEMENTED_NOT_CLOSED", "OBSOLETE"} and any(
            item[k] for k in ("remaining", "missing_tests", "decisions")
        ):
            raise ValueError("migration.unresolved: completed work has remaining gaps")
        if item["decisions"] and item["route"] != "wayfinder":
            raise ValueError(
                "migration.unresolved: decisions require accepted Wayfinder deferral"
            )
        evidence(root, item["evidence"], data["reviewed_head"])
        covered.add(item["source"])
    if covered != active:
        raise ValueError("migration.coverage: active sources missing")


def dedicated(name: str) -> bool:
    """Recognize generated integration paths, never shared project files."""
    return name.startswith(
        (
            ".claude/commands/opsx/",
            ".claude/skills/openspec-",
            ".agents/skills/openspec-",
        )
    )


def changes(
    root: Path, data: dict[str, Any], inventory: dict[str, Any]
) -> dict[str, bytes | None]:
    """Constrain reviewed writes/removals and exact destination freshness."""
    result: dict[str, bytes | None] = {}
    integration = set(inventory["integrations"])
    sources = {
        name for name in inventory["source_paths"] if name.startswith("openspec/")
    }
    local = (
        load(root).get("tracker", {}).get("provider", "local-markdown")
        == "local-markdown"
    )
    for operation in ("writes", "deletes"):
        for item in data[operation]:
            fields(
                item,
                {"path", "before_sha256", "content"}
                if operation == "writes"
                else {"path", "before_sha256"},
            )
            name = item["path"]
            if not isinstance(name, str):
                raise ValueError("migration.manifest: path must be text")
            safe_path(root, name)
            if name in result:
                raise ValueError(f"migration.manifest: duplicate path {name}")
            before = item["before_sha256"]
            if before is not None:
                sha(before)
            if digest(read_bytes(root, name)) != before:
                raise ValueError(f"migration.stale: destination {name}")
            if operation == "deletes":
                if before is None or not (
                    name in sources or name in integration and dedicated(name)
                ):
                    raise ValueError(f"migration.scope: forbidden deletion {name}")
                result[name] = None
            else:
                allowed = (
                    name.startswith(("docs/context/", "docs/adr/", "docs/features/"))
                    or local
                    and name.startswith(".scratch/")
                    and name.endswith(".md")
                )
                if not (allowed or name in integration) or not isinstance(
                    item["content"], str
                ):
                    raise ValueError(f"migration.scope: forbidden write {name}")
                result[name] = item["content"].encode("utf-8")
    if not sources.union(integration).issubset(result):
        raise ValueError(
            "migration.coverage: every OpenSpec source/integration needs reviewed removal"
        )
    return result


def read(root: Path) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    """Read integrity-bound review artifacts with strict outer schema."""
    raw = read_bytes(root, f"{WORKSPACE}/reconciliation/application.json")
    inventory_raw = read_bytes(root, f"{WORKSPACE}/inventory.json")
    if raw is None or inventory_raw is None:
        raise ValueError(
            "migration.manifest: prepare inventory and semantic application.json first"
        )
    data = fields(
        json_object(raw),
        {
            "schema_version",
            "inventory_sha256",
            "reviewed_head",
            "plan",
            "writes",
            "deletes",
            "canonical",
            "active",
            "unresolved_decisions",
        },
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("migration.manifest: unsupported schema")
    for key in ("writes", "deletes", "canonical", "active", "unresolved_decisions"):
        if not isinstance(data[key], list):
            raise ValueError(f"migration.manifest: {key} must be an array")
    if strings(data["unresolved_decisions"]):
        raise ValueError(
            "migration.unresolved: resolve human decisions before finalizing"
        )
    if sha(data["inventory_sha256"]) != digest(inventory_raw):
        raise ValueError("migration.stale: inventory changed")
    fields(data["plan"], {"path", "sha256"})
    if data["plan"]["path"] != "reconciliation/plan.md" or sha(
        data["plan"]["sha256"]
    ) != digest(read_bytes(root, f"{WORKSPACE}/reconciliation/plan.md")):
        raise ValueError("migration.stale: readable plan changed")
    if not isinstance(data["reviewed_head"], str) or not re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}", data["reviewed_head"]
    ):
        raise ValueError("migration.manifest: reviewed_head must be a full commit ID")
    return data, json_object(inventory_raw), raw
