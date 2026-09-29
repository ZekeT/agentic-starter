"""Resolve the reviewed consumer payload in source and generated checkouts."""

from pathlib import Path

from .ownership import json_object, read_bytes, remove_owned
from .registry import CONTENT_OWNERS, output_scope
from .verification_inputs import source_path

INCLUSION = ".engineering/template/files.json"


def inclusion(root: Path) -> dict[str, dict[str, str]]:
    """Validate the single positive inventory; path checks happen when resolved."""
    data = json_object(read_bytes(root, INCLUSION) or b"{}")
    if (
        set(data) != {"schema_version", "managed", "application"}
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
    ):
        raise ValueError("Unsupported template inclusion schema")
    for group in ("managed", "application"):
        if not isinstance(data[group], dict):
            raise ValueError("Template inclusion groups must be objects")
        for origin in data[group].values():
            if not isinstance(origin, str):
                raise ValueError("Template sources must be paths")
    if data["managed"].keys() & data["application"].keys():
        raise ValueError("Duplicate template destination")
    selected = {**data["managed"], **data["application"]}
    if not selected or ".engineering/manifest.json" in selected:
        raise ValueError("Distribution metadata must be generated")
    return {group: data[group] for group in ("managed", "application")}


def payload_path(root: Path, name: str) -> Path:
    """Source checkouts select origins; generated distributions use destinations."""
    origin = name
    if source_path(root, INCLUSION).exists():
        origin = inclusion(root)["managed"].get(name, name)
    return source_path(root, origin)


def content(root: Path, name: str) -> bytes:
    """Read shipped bytes, excluding navigation content installed by dependencies."""
    path = payload_path(root, name)
    if not path.is_file():
        raise ValueError(f"Missing regular template input: {path.relative_to(root)}")
    raw = path.read_bytes()
    # Generated distributions are already projected; validate their exact bytes.
    if not source_path(root, INCLUSION).exists():
        return raw
    owner = next((d for d, m in CONTENT_OWNERS.items() if name in m.CONTENT), None)
    if owner is None:
        return raw
    scope = output_scope(owner, name)
    if scope["mode"] == "file":
        raise ValueError(f"{name}: navigation content is installed, never shipped")
    return remove_owned(raw, name, scope) or b""
