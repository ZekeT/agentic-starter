"""Parse and validate the shared, stdlib-only eval case format without execution."""

from __future__ import annotations

import re


def parse_fields(content: str, label: str) -> dict[str, str]:
    """Read inline and indented literal/folded fields used by the eval runner."""
    fields: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for raw in content.splitlines():
        header = re.match(r"^([a-z_]+):[ \t]*(.*)$", raw)
        if header:
            if key:
                fields[key] = "\n".join(buf).rstrip()
            name, rest = header.groups()
            if name in fields or name == key:
                raise ValueError(f"{label}: duplicate field '{name}'")
            key, buf = name, []
            if rest.strip() not in ("|", ">"):
                fields[key] = rest
                key = None
            continue
        if key is not None:
            buf.append(raw[2:] if raw.startswith("  ") else raw)
    if key:
        fields[key] = "\n".join(buf).rstrip()
    for required in ("id", "kind", "why"):
        if not fields.get(required, "").strip():
            raise ValueError(f"{label}: missing required key '{required}'")
    if fields["kind"] not in {"static", "prompt"}:
        raise ValueError(f"{label}: kind must be static/prompt")
    body = "shell" if fields["kind"] == "static" else "prompt"
    if not fields.get(body, "").strip():
        raise ValueError(f"{label}: missing required key '{body}'")
    return fields
