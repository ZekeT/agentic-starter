"""Explicit human acceptance and bounded, byte-bound temporary cleanup."""

import re
from pathlib import Path
from typing import Any

from ..config import safe_path
from ..ownership import digest, encoded, json_object, observe, read_bytes
from ..transaction import write_files
from . import application, validation
from .common import tree
from .openspec import WORKSPACE

RECORD = ".engineering/migration-work/openspec-closure.json"
PENDING = "Migration accepted; cleanup pending. Ordinary development may continue."


def artifacts(root: Path) -> dict[str, str | None]:
    """Inventory only regular workspace files, including modes and unknown additions."""
    return {name: observe(root, name) for name in tree(root, WORKSPACE)}


def read(root: Path) -> dict[str, Any] | None:
    """Validate local bookkeeping before trusting a cleanup boundary."""
    raw = read_bytes(root, RECORD)
    if raw is None:
        return None
    data = application.fields(
        json_object(raw),
        {
            "schema_version",
            "status",
            "artifacts",
            "retained",
            "cleanup_sha256",
        },
    )
    if (
        type(data["schema_version"]) is not int
        or data["schema_version"] != 1
        or data["status"] not in {"accepted", "closed"}
    ):
        raise ValueError("migration.closure: invalid acceptance record")
    for key in ("artifacts", "retained"):
        if not isinstance(data[key], dict):
            raise ValueError("migration.closure: expected artifact fingerprints")
        for name, value in data[key].items():
            safe_path(root, name)
            if (
                not name.startswith(WORKSPACE + "/")
                or not isinstance(value, str)
                or not re.fullmatch(r"[0-9a-f]{64}:[0-9]+", value)
            ):
                raise ValueError(
                    "migration.closure: invalid artifact scope/fingerprint"
                )
    if data["status"] == "closed":
        application.sha(data["cleanup_sha256"])
    elif data["cleanup_sha256"] is not None or data["retained"]:
        raise ValueError("migration.closure: invalid pending cleanup")
    if not data["artifacts"]:
        raise ValueError("migration.closure: missing accepted artifacts")
    return data


def accept_migration(root: Path, apply: bool) -> int:
    """Record explicit human acceptance only while validated bytes remain current."""
    if not validation.completed(root):
        raise ValueError(
            "migration.closure: successful finalization validation required"
        )
    data, inventory, _ = application.read(root)
    application.semantics(root, data, inventory)
    current = artifacts(root)
    print(
        "Validated outputs ready for human acceptance. Temporary cleanup remains pending."
    )
    if apply:
        write_files(
            root,
            {
                RECORD: encoded(
                    {
                        "schema_version": 1,
                        "status": "accepted",
                        "artifacts": current,
                        "retained": {},
                        "cleanup_sha256": None,
                    }
                )
            },
        )
        print(PENDING)
    else:
        print("After human acceptance, use --accept --apply. No files changed.")
    return 0


def cleanup_plan(root: Path, data: dict[str, Any], retain: list[str]) -> dict[str, Any]:
    """Bind exact removals/retentions; edited or new files require explicit retention."""
    current = artifacts(root)
    kept = set()
    for choice in retain:
        prefix = WORKSPACE if choice == "." else f"{WORKSPACE}/{choice}"
        safe_path(root, prefix)
        matches = {
            name for name in current if name == prefix or name.startswith(prefix + "/")
        }
        if not matches:
            raise ValueError(
                f"migration.closure: retention matches no artifacts: {choice}"
            )
        kept.update(matches)
    missing = set(data["artifacts"]) - set(current)
    if missing:
        raise ValueError(
            f"migration.closure: accepted artifacts missing: {sorted(missing)}"
        )
    for name, value in current.items():
        if name not in kept and data["artifacts"].get(name) != value:
            raise ValueError(
                f"migration.closure: changed/new artifact preserved; explicitly retain it: {name}"
            )
    return {
        "acceptance_sha256": digest(read_bytes(root, RECORD)),
        "remove": {name: value for name, value in current.items() if name not in kept},
        "retain": {name: value for name, value in current.items() if name in kept},
    }


def execute(
    root: Path, *, accept: bool, apply: bool, retain: list[str], approved: str | None
) -> int:
    """Expose pending cleanup and authorize only the exact presented disposition."""
    root = root.resolve()
    data = read(root)
    if data is None:
        if accept:
            return accept_migration(root, apply)
        raise ValueError(
            "migration.closure: human acceptance required via --accept --apply"
        )
    if data["status"] == "closed":
        if artifacts(root) != data["retained"]:
            raise ValueError(
                "migration.closure: artifacts changed or reappeared after closure; no files changed"
            )
        if approved is not None and approved != data["cleanup_sha256"]:
            raise ValueError(
                "migration.closure: cleanup approval differs from recorded closure"
            )
        print(
            "Migration closed; recorded cleanup/retention acknowledged. No files changed."
        )
        return 0
    print(PENDING)
    if accept:
        print("Acceptance already recorded; no files changed.")
        return 0
    plan = cleanup_plan(root, data, retain)
    token = digest(encoded(plan))
    for action in ("remove", "retain"):
        for name, fingerprint in plan[action].items():
            print(f"{action.upper()} {name} ({fingerprint})")
    print(
        f"KEEP local acceptance/cleanup record: {RECORD} (optional retry bookkeeping; no normal gate reads it)"
    )
    print(f"Cleanup SHA-256: {token}")
    if not apply:
        print(
            "No files changed. After human removal/retention approval, repeat choices with --apply --approved-cleanup <SHA-256>."
        )
        return 0
    if approved != token:
        raise ValueError(
            "migration.closure: exact cleanup approval required; review --cleanup --plan"
        )
    if cleanup_plan(root, data, retain) != plan:
        raise ValueError("migration.closure: artifacts changed during preview")
    closed = {
        **data,
        "status": "closed",
        "retained": plan["retain"],
        "cleanup_sha256": token,
    }

    def validate() -> None:
        if artifacts(root) != plan["retain"]:
            raise ValueError("migration.closure: cleanup outputs changed")

    write_files(
        root,
        {**{name: None for name in plan["remove"]}, RECORD: encoded(closed)},
        validate=validate,
    )
    base = safe_path(root, WORKSPACE)
    for path in sorted(
        [*base.rglob("*"), base], key=lambda p: len(p.parts), reverse=True
    ):
        if path.is_dir() and not path.is_symlink():
            try:
                path.rmdir()
            except OSError:
                pass
    print(
        "Migration closed; temporary artifacts removed or explicitly retained. Ordinary development does not depend on the local record."
    )
    return 0
