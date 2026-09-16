"""Extract and reconcile explicit owned scopes without claiming project content."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .config import object_value, safe_path

METADATA = {".engineering/manifest.json", ".engineering/state/install.json"}


def digest(content: bytes | None) -> str | None:
    """Fingerprint bytes, distinguishing an absent scope from an empty scope."""
    return hashlib.sha256(content).hexdigest() if content is not None else None


def read_bytes(root: Path, name: str) -> bytes | None:
    """Inspect regular files only, including absent paths, through shared containment."""
    path = safe_path(root, name)
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f"{name}: expected a regular file")
    return path.read_bytes()


def validate_ownership(name: str, value: Any) -> dict[str, Any]:
    """Reject ambiguous or self-referential ownership descriptions."""
    spec = object_value(value, f"{name} ownership")
    mode = spec.get("mode")
    if mode not in {"file", "section", "hooks", "preserve"}:
        raise ValueError(f"{name}: unsupported ownership mode")
    if (
        name in METADATA
        or name.startswith((".git/", "src/"))
        or is_openspec_owned(name)
    ):
        raise ValueError(f"{name}: cannot fingerprint metadata or project sources")
    if name.startswith(("docs/", ".github/")) and mode != "preserve":
        raise ValueError(f"{name}: documentation and CI remain project-owned")
    allowed = {"mode", "marker"} if mode == "section" else {"mode"}
    if set(spec) != allowed:
        raise ValueError(f"{name}: unexpected ownership fields")
    if mode == "section" and not re.fullmatch(r"[a-z][a-z0-9-]*", str(spec["marker"])):
        raise ValueError(f"{name}: invalid section marker")
    if mode == "hooks" and name != ".claude/settings.json":
        raise ValueError("Hook ownership applies only to .claude/settings.json")
    return spec


def markers(name: str, spec: dict[str, Any]) -> tuple[bytes, bytes]:
    """Use Markdown comments for instructions and hash comments for build files."""
    tag = spec["marker"]
    if name.endswith(".md"):
        return (
            f"<!-- engineering:{tag}:begin -->".encode(),
            f"<!-- engineering:{tag}:end -->".encode(),
        )
    return f"# engineering:{tag}:begin".encode(), f"# engineering:{tag}:end".encode()


def section_bounds(
    content: bytes, name: str, spec: dict[str, Any]
) -> tuple[int, int] | None:
    """Validate exactly one complete line-delimited region, or an unmarked file."""
    begin, end = markers(name, spec)
    if begin not in content and end not in content:
        if b"engineering:" in content:
            raise ValueError(f"{name}: unrecognized engineering markers")
        return None
    if content.count(begin) != 1 or content.count(end) != 1:
        raise ValueError(f"{name}: duplicate or incomplete engineering markers")
    opening = re.search(rb"(?m)^" + re.escape(begin) + rb"\r?\n", content)
    closing = re.search(rb"(?m)^" + re.escape(end) + rb"(?:\r?\n|\Z)", content)
    if opening is None or closing is None or opening.end() > closing.start():
        raise ValueError(
            f"{name}: engineering markers must occupy complete LF/CRLF lines in order"
        )
    return opening.start(), closing.end()


def json_object(content: bytes) -> dict[str, Any]:
    """Reject duplicate JSON keys instead of silently choosing a setting."""

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return object_value(json.loads(content, object_pairs_hook=unique), "settings")


def hook_identity(hook: Any) -> str | None:
    """Recognize only shipped protection hook paths, not unrelated project hooks."""
    from .doctor_wiring import HOOKS

    item = object_value(hook, "hook")
    command = item.get("command", "")
    if not isinstance(command, str):
        raise ValueError("Hook command must be text")
    matches = [name for name in HOOKS if f"/.claude/hooks/{name}" in command]
    if len(matches) > 1:
        raise ValueError("Ambiguous engineering hook command")
    return matches[0] if matches else None


def hook_groups(data: dict[str, Any], owned: bool) -> dict[str, Any]:
    """Project hooks and engineering hooks partition by explicit shipped identity."""
    events = object_value(data.get("hooks", {}), "hooks")
    result: dict[str, Any] = {}
    for event, groups in events.items():
        if not isinstance(groups, list):
            raise ValueError("Hook event must contain matcher groups")
        kept = []
        for raw in groups:
            group = object_value(raw, "hook group")
            hooks = group.get("hooks")
            if not isinstance(hooks, list):
                raise ValueError("Hook group must contain hooks")
            selected = [h for h in hooks if (hook_identity(h) is not None) == owned]
            if selected:
                kept.append({**group, "hooks": selected})
        if kept:
            result[event] = kept
    return result


def encoded(value: Any) -> bytes:
    """Serialize deterministic JSON metadata and hook projections."""
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def owned_content(
    content: bytes | None, name: str, spec: dict[str, Any]
) -> bytes | None:
    """Return only the bytes or normalized settings attributed to this scope."""
    mode = spec["mode"]
    if mode == "preserve" or content is None:
        return None
    if mode == "file":
        return content
    if mode == "hooks":
        data = json_object(content)
        if data.get("disableAllHooks", False) is not False:
            raise ValueError("disableAllHooks conflicts with required protection hooks")
        hooks = hook_groups(data, True)
        return encoded(hooks) if hooks else None
    bounds = section_bounds(content, name, spec)
    return content[bounds[0] : bounds[1]] if bounds else None


def merge_owned(
    local: bytes | None, incoming: bytes, name: str, spec: dict[str, Any]
) -> bytes:
    """Replace a known scope or append a bounded scope, preserving surrounding bytes."""
    if spec["mode"] == "file":
        return incoming
    local = local or b""
    if spec["mode"] == "hooks":
        data = json_object(local) if local else {}
        project_hooks = hook_groups(data, False)
        for event, groups in json_object(incoming).items():
            project_hooks.setdefault(event, []).extend(groups)
        data["hooks"] = project_hooks
        return encoded(data)
    bounds = section_bounds(local, name, spec)
    if bounds:
        return local[: bounds[0]] + incoming + local[bounds[1] :]
    gap = b"\n" if local and not local.endswith(b"\n") else b""
    return local + gap + incoming


def distribution_ownership(name: str) -> dict[str, Any]:
    """Assign starter inventory ownership explicitly, preserving application artifacts."""
    if name in {
        ".engineering/dependencies.toml",
        ".engineering/graft/package.json",
        ".engineering/graft/package-lock.json",
    }:
        return {"mode": "preserve"}
    if name == ".env.template" or name.startswith(("docs/", ".github/")):
        return {"mode": "preserve"}
    if name in {"CLAUDE.md", "AGENTS.md", "Makefile", ".gitignore"}:
        return {"mode": "section", "marker": "integration"}
    if name == ".claude/settings.json":
        return {"mode": "hooks"}
    return {"mode": "file"}


def is_openspec_owned(name: str) -> bool:
    """Keep OpenSpec-generated configuration and tools outside engineering ownership."""
    return name.startswith(
        ("openspec/", ".claude/commands/opsx/", ".claude/skills/openspec-")
    )


def observe(root: Path, name: str) -> str | None:
    """Observe content and permissions so chmod changes also invalidate a plan."""
    content = read_bytes(root, name)
    if content is None:
        return None
    return f"{digest(content)}:{safe_path(root, name).stat().st_mode & 0o777}"


def hash_history(entry: dict[str, Any], label: str) -> list[str]:
    """Validate current and historical distribution fingerprints for every consumer."""
    history = entry.get("previous", [])
    if not isinstance(history, list):
        raise ValueError(f"{label}: invalid sha256/history metadata")
    values = [entry.get("sha256"), *history]
    if any(
        not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
        for value in values
    ):
        raise ValueError(f"{label}: invalid sha256/history metadata")
    return values
