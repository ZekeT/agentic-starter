"""The update adapter shares all baseline and conflict decisions with the new CLI."""

import subprocess
import sys
from pathlib import Path

import pytest
from factory.adoption import plan_installation
from factory.apply import apply_plan
from factory.ownership import digest, encoded, json_object

from .test_lifecycle_checkpoint import checkpoint as checkpoint
from .test_lifecycle_checkpoint import commit, snapshot, write

ROOT = Path(__file__).parents[3]
SCRIPT = ROOT / ".claude/skills/setup-update/scripts/setup_update.py"
pytestmark = pytest.mark.integration


def invoke(template, target, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target), "--template", str(template), *args],
        capture_output=True,
        text=True,
        timeout=20,
    )


@pytest.mark.parametrize("flags", [(), ("--dry",), ("--dry-run",)])
def test_run_update_dry_run_writes_nothing(checkpoint, flags):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    commit(target)
    before = snapshot(target)
    result = invoke(template, target, *flags)
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(target) == before


def test_adapter_and_new_cli_agree(checkpoint):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    commit(target)
    old = invoke(template, target)
    new = subprocess.run(
        [
            sys.executable,
            str(ROOT / "factory"),
            "update",
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


@pytest.mark.parametrize("local", [None, "customized", "old"])
def test_run_update_never_overwrites_unknown_or_deleted_content(checkpoint, local):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    if local is None:
        (target / ".harness/docs/design.md").unlink()
    elif local == "customized":
        write(target, ".harness/docs/design.md", "customized")
    commit(target)
    write(template, ".harness/docs/design.md", "upstream replacement")
    manifest = json_object((template / ".harness/template-manifest.json").read_bytes())
    manifest["files"][".harness/docs/design.md"]["sha256"] = digest(
        b"upstream replacement"
    )
    write(template, ".harness/template-manifest.json", encoded(manifest))
    manifest["files"][".harness/docs/design.md"]["owned_sha256"] = digest(b"upstream replacement")
    write(template, ".harness/template-manifest.json", encoded(manifest))
    before = snapshot(target)
    result = invoke(template, target, "--apply")
    if local == "old":
        assert result.returncode == 0, result.stdout + result.stderr
        assert (
            target / ".harness/docs/design.md"
        ).read_text() == "upstream replacement"
    else:
        assert result.returncode == 1 and "CONFLICT" in result.stdout
        assert snapshot(target) == before


def test_force_cannot_bypass_shared_engine(checkpoint):
    template, target = checkpoint
    before = snapshot(target)
    result = invoke(template, target, "--force")
    assert result.returncode == 1 and "--force" in result.stderr
    assert snapshot(target) == before
