#!/usr/bin/env python3
"""Fingerprint the consumer inventory for generation, adoption and updates.

Run make manifest after changing distributed source. Previous full-file hashes
remain available for legacy conversion. This maintainer tool is never shipped.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / ".engineering"))
from engineering.config import DEFAULTS  # noqa: E402
from engineering.distribution import content, inclusion, payload_path  # noqa: E402
from engineering.installation import build_state  # noqa: E402
from engineering.ownership import (  # noqa: E402
    digest,
    distribution_ownership,
    encoded,
    owned_content,
)

MANIFEST_PATH = ROOT / ".engineering" / "manifest.json"


def load_previous_manifest() -> dict[str, Any]:
    """Return the existing manifest, or an empty dict if none exists."""
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text())  # type: ignore[no-any-return]


def build_manifest(
    previous: dict[str, Any], *, root: Path = ROOT, files: list[Path] | None = None
) -> dict[str, Any]:
    """Build the new manifest, carrying hash history forward.

    Args:
        previous: The previously generated manifest (may be empty).
        root: Distribution root for resolving selected paths and release version.
        files: Explicit staged payload files, or the shared consumer inventory.

    Returns:
        The new manifest dict ready to serialise.
    """
    if "schema_version" in previous and (
        type(previous["schema_version"]) is not int or previous["schema_version"] != 1
    ):
        raise ValueError(
            "Unsupported manifest schema_version; use engineering tooling compatible "
            "with this manifest before regenerating it"
        )
    prev_files: dict[str, Any] = previous.get("files", {})
    entries: dict[str, Any] = {}
    selected = (
        [root / name for name in inclusion(root)["managed"]] if files is None else files
    )
    for path in sorted(selected):
        rel = path.relative_to(root).as_posix()
        raw = content(root, rel)
        current_digest = digest(raw)
        old_entry = prev_files.get(rel, {})
        history: list[str] = list(old_entry.get("previous", []))
        old_current = old_entry.get("sha256")
        if old_current and old_current != current_digest and old_current not in history:
            history.append(old_current)
        ownership = distribution_ownership(rel)
        owned = owned_content(raw, rel, ownership)
        entries[rel] = {
            "sha256": current_digest,
            "previous": history,
            "ownership": ownership,
            "owned_sha256": digest(owned),
            "executable": bool(payload_path(root, rel).stat().st_mode & 0o111),
        }
    version = "unknown"
    version_path = root / ".engineering/TEMPLATE_VERSION"
    if version_path.exists():
        version = version_path.read_text().strip()
    return {
        "schema_version": 1,
        "defaults": {"maintainability": dict(DEFAULTS)},
        "project": previous.get("project", {}),
        "template_version": version,
        "ownership_version": 1,
        "files": entries,
    }


def main() -> None:
    """Regenerate the consumer manifest and maintainer installation baseline."""
    try:
        previous = load_previous_manifest()
        manifest = build_manifest(previous)
    except ValueError as exc:
        sys.exit(str(exc))
    MANIFEST_PATH.write_bytes(encoded(manifest))
    entries = {
        name: {"ownership": entry["ownership"], "upstream": entry["owned_sha256"]}
        for name, entry in manifest["files"].items()
        if entry["ownership"]["mode"] != "preserve"
    }
    state_path = ROOT / ".engineering/state/install.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_bytes(
        encoded(build_state(manifest["template_version"], entries, "maintainer"))
    )
    changed = sum(
        1
        for rel, entry in manifest["files"].items()
        if previous.get("files", {}).get(rel, {}).get("sha256") != entry["sha256"]
    )
    print(
        f"template-manifest.json written: {len(manifest['files'])} files, "
        f"{changed} changed since last generation "
        f"(template version {manifest['template_version']})"
    )


if __name__ == "__main__":
    main()
