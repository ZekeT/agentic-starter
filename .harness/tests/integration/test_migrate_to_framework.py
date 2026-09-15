"""Migration's public adapter must share conservative planning and explicit apply."""

import subprocess
import sys
from pathlib import Path

import pytest

from .test_lifecycle_checkpoint import checkpoint as checkpoint
from .test_lifecycle_checkpoint import commit, snapshot, write

ROOT = Path(__file__).parents[3]
SCRIPT = ROOT / ".harness/scripts/migrate_to_framework.py"
pytestmark = pytest.mark.integration


def invoke(template, target, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target), "--template", str(template), *args],
        capture_output=True,
        text=True,
        timeout=20,
    )


@pytest.mark.parametrize("flags", [(), ("--dry",), ("--dry-run",)])
def test_full_migration_dry_creates_nothing(checkpoint, flags):
    template, target = checkpoint
    before = snapshot(target)
    result = invoke(template, target, *flags)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "read-only plan" in result.stdout and "Canonical make check" in result.stdout
    assert snapshot(target) == before


def test_full_migration_preserves_python_configuration(checkpoint):
    template, target = checkpoint
    before = snapshot(target)
    result = invoke(template, target, "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (target / "pyproject.toml").read_bytes() == before["pyproject.toml"]
    assert not (target / "uv.lock").exists()
    assert (target / "CLAUDE.md").read_bytes().startswith(before["CLAUDE.md"])
    assert (target / "Makefile").read_bytes().startswith(before["Makefile"])
    assert not (target / "MIGRATION_REPORT.md").exists()
    assert "Recovery commit:" in result.stdout


def test_copy_framework_files_force_never_overwrites(checkpoint):
    template, target = checkpoint
    write(target, "factory", "project-owned executable")
    commit(target)
    before = snapshot(target)
    result = invoke(template, target, "--force", "--apply")
    assert result.returncode == 1 and "--force" in result.stderr
    assert snapshot(target) == before


@pytest.mark.parametrize(
    "kind",
    ["missing", "file", "overlap", "unsupported", "unknown-check", "malformed-python"],
)
def test_target_validation_and_inspection(checkpoint, kind):
    template, target = checkpoint
    if kind == "missing":
        target = target / "missing"
    elif kind == "file":
        target = write(target, "file", "content")
    elif kind == "overlap":
        target = template
    elif kind == "unsupported":
        (target / "pyproject.toml").unlink()
        write(target, "package.json", '{"name":"javascript-project"}')
    elif kind == "unknown-check":
        write(target, "Makefile", "# no canonical checks")
    else:
        write(target, "pyproject.toml", "[broken")
    result = invoke(template, target)
    assert result.returncode == 1 and "Traceback" not in result.stderr


def test_preflight_blocks_dirty_tree(checkpoint):
    template, target = checkpoint
    write(target, "work.txt", "uncommitted")
    before = snapshot(target)
    result = invoke(template, target, "--apply")
    assert result.returncode == 1 and "Dirty target" in result.stderr
    assert snapshot(target) == before


def test_adapter_and_new_cli_agree(checkpoint):
    template, target = checkpoint
    old = invoke(template, target)
    new = subprocess.run(
        [
            sys.executable,
            str(ROOT / "factory"),
            "adopt",
            str(target),
            "--template",
            str(template),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert old.returncode == new.returncode == 0
    assert old.stdout.splitlines()[1:] == new.stdout.splitlines()
