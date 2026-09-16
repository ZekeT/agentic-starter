"""Apply preflighted file changes with byte-and-mode rollback on failure."""

from collections.abc import Callable
from pathlib import Path

from .config import safe_path
from .ownership import read_bytes


def write_files(
    root: Path,
    changes: dict[str, bytes | None],
    *,
    executables: set[str] | None = None,
    validate: Callable[[], None] | None = None,
) -> None:
    """Restore affected files on an ordinary filesystem/validation error."""
    original = {name: read_bytes(root, name) for name in changes}
    modes = {
        name: safe_path(root, name).stat().st_mode & 0o777
        for name in changes
        if original[name] is not None
    }
    created: list[Path] = []
    touched: list[str] = []
    try:
        for name, content in changes.items():
            path = safe_path(root, name)
            missing = []
            parent = path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for parent in reversed(missing):
                parent.mkdir()
                created.append(parent)
            touched.append(name)
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(content)
                if name in (executables or set()):
                    path.chmod(path.stat().st_mode | 0o111)
        if validate:
            validate()
    except (OSError, ValueError) as exc:
        failures = []
        for name in reversed(touched):
            try:
                path = safe_path(root, name)
                before = original[name]
                if before is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(before)
                    path.chmod(modes[name])
            except OSError:
                failures.append(name)
        for path in reversed(created):
            try:
                path.rmdir()
            except OSError:
                pass
        recovery = (
            f"Rollback incomplete for {failures}; restore these paths from the reported recovery commit."
            if failures
            else "Affected files restored."
        )
        raise ValueError(f"apply.failed: {exc}. {recovery}") from exc
