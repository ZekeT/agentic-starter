"""Regular verification inputs and configuration validation shared by checkout and identity."""

from pathlib import Path
from typing import Any

from .config import safe_path
from .ownership import digest
from .source import git

STATE = ".engineering/state/verification"


def source_path(root: Path, name: str) -> Path:
    """Permit the public environment template, never secret variants or links."""
    if Path(name).name == ".env.template":
        path = safe_path(root, str(Path(name).with_name("template-placeholder")))
        path = path.with_name(".env.template")
        if path.is_symlink():
            raise ValueError(f"Symlink source path is unsupported: {name}")
        return path
    return safe_path(root, name)


def strings(value: Any, label: str, *, empty: bool = False) -> list[str]:
    """Require a list of nonempty strings without coercion."""
    if not isinstance(value, list) or (not value and not empty):
        raise ValueError(f"{label}: expected a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label}: expected nonempty strings")
    return value


def validate_navigation(root: Path, plan: dict[str, Any]) -> None:
    """Assess applicable navigation using the proposed configuration."""
    if (root / ".engineering/config.toml").is_file():
        from .settings import load

        if load(root).get("navigation", {}).get("application_roots"):
            if [".engineering/bin/graft", "check"] not in plan["checks"]:
                raise ValueError("Configured application roots require Graft check")


def paths_from_git(root: Path, *args: str) -> set[str]:
    """Read NUL-delimited paths without quoting or newline ambiguity."""
    return set(
        filter(None, git(root, *args).decode(errors="surrogateescape").split("\0"))
    )


def files(root: Path, names: set[str]) -> dict[str, Any]:
    """Fingerprint regular bytes and executable bits, including deletions."""
    result: dict[str, Any] = {}
    for name in sorted(names):
        path = source_path(root, name)
        if not path.exists():
            result[name] = None
        elif not path.is_file():
            raise ValueError(f"Unsupported nonregular verification input: {name}")
        else:
            result[name] = {
                "sha256": digest(path.read_bytes()),
                "executable": bool(path.stat().st_mode & 0o111),
            }
    return result
