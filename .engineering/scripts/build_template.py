#!/usr/bin/env python3
"""Build a consumer directory from the reviewed positive inclusion manifest."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from generate_template_manifest import build_manifest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".engineering"))
from engineering.adoption import template_manifest  # noqa: E402
from engineering.ownership import encoded, json_object  # noqa: E402
from engineering.verification_inputs import source_path  # noqa: E402


def build(destination: Path) -> None:
    """Validate all inputs before creating a new directory; never replace a project."""
    destination = destination.absolute()
    for path in (destination, *destination.parents):
        if path.is_symlink():
            raise ValueError(f"Symlink output path is unsupported: {path}")
    if destination.exists():
        raise ValueError("Output already exists; choose a new directory")
    if not destination.parent.is_dir():
        raise ValueError("Output parent must already exist")
    data = json_object((ROOT / ".engineering/template/files.json").read_bytes())
    if (
        set(data) != {"schema_version", "managed", "application"}
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
    ):
        raise ValueError("Unsupported template inclusion schema")
    if not all(isinstance(data[key], dict) for key in ("managed", "application")):
        raise ValueError("Template inclusion groups must be objects")
    if data["managed"].keys() & data["application"].keys():
        raise ValueError("Duplicate template destination")
    selected = {**data["managed"], **data["application"]}
    if any(not isinstance(origin, str) for origin in selected.values()):
        raise ValueError("Template sources must be paths")
    if not selected or ".engineering/manifest.json" in selected:
        raise ValueError("Distribution metadata must be generated")
    with tempfile.TemporaryDirectory(prefix="engineering-template-") as temporary:
        stage = Path(temporary)
        for name, origin in sorted(selected.items()):
            source = source_path(ROOT, origin)
            target = source_path(stage, name)
            if not source.is_file():
                raise ValueError(f"Missing regular template input: {origin}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            target.chmod(0o755 if source.stat().st_mode & 0o111 else 0o644)
        manifest = build_manifest(
            {}, root=stage, files=[stage / name for name in data["managed"]]
        )
        metadata = stage / ".engineering/manifest.json"
        metadata.write_bytes(encoded(manifest))
        metadata.chmod(0o644)
        template_manifest(stage)
        # copytree refuses every existing destination, including a late arrival.
        shutil.copytree(stage, destination)
    print(f"Consumer template: {destination} ({len(selected) + 1} files)")


def main() -> int:
    """Expose the maintainer build without dependency installs or publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        build(args.destination)
        return 0
    except (OSError, ValueError) as exc:
        print(f"Template build refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
