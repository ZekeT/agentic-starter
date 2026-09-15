"""Convert legacy metadata without guessing customization or competing authorities."""

import json
import sys
from pathlib import Path

import pytest
from factory.adoption import plan_installation
from factory.apply import apply_plan
from factory.doctor import diagnose
from factory.installation import installation_version
from factory.ownership import encoded

from .test_lifecycle_checkpoint import checkpoint as checkpoint
from .test_lifecycle_checkpoint import commit, snapshot, write

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("existing_config", [False, True])
@pytest.mark.parametrize("version_source", [None, "stamp", "manifest", "version-file"])
def test_migration_passes_doctor_after_external_setup(
    checkpoint, existing_config, version_source
):
    template, target = checkpoint
    custom = {"maintainability": {"max_file_lines": 700}}
    if existing_config:
        write(
            target,
            ".harness/template-manifest.json",
            encoded({"schema_version": 1, "project": custom}),
        )
    paths = {
        "stamp": ".claude/template-version.json",
        "manifest": ".harness/template-manifest.json",
        "version-file": ".harness/TEMPLATE_VERSION",
    }
    if version_source:
        name = paths[version_source]
        if version_source == "version-file":
            write(target, name, "1.4.0\n")
        else:
            data = (
                json.loads((target / name).read_text())
                if (target / name).exists()
                else {}
            )
            data["template_version"] = "1.4.0"
            write(target, name, encoded(data))
    commit(target)
    assert apply_plan(plan_installation(template, target)) == 0
    assert not [f for f in diagnose(target) if f.severity == "ERROR"]
    current = json.loads((template / ".harness/template-manifest.json").read_text())[
        "template_version"
    ]
    assert installation_version(target) == current
    state = json.loads((target / ".factory/state.json").read_text())
    assert state["installed_version"] == current
    manifest = json.loads((target / ".harness/template-manifest.json").read_text())
    if existing_config:
        assert manifest["project"] == custom
    # The state supersedes historical conversion inputs without rewriting them.
    if version_source in {"stamp", "version-file"}:
        assert "1.4.0" in (target / paths[version_source]).read_text()
    commit(target)
    before = snapshot(target)
    assert apply_plan(plan_installation(template, target, "update")) == 0
    assert snapshot(target) == before


@pytest.mark.parametrize("stamp", ['{"template_version":"1.3.0"}', "{bad", "{}"])
def test_migration_rejects_conflicting_or_invalid_versions_before_writes(
    checkpoint, stamp
):
    template, target = checkpoint
    write(target, ".claude/template-version.json", stamp)
    write(target, ".harness/TEMPLATE_VERSION", "1.4.0\n")
    before = snapshot(target)
    with pytest.raises(ValueError):
        plan_installation(template, target)
    assert snapshot(target) == before


@pytest.mark.parametrize("kind", ["outside", "inside", "dangling", "directory", "fifo"])
def test_migration_rejects_unsafe_ignore_before_writes(checkpoint, kind):
    import os

    template, target = checkpoint
    ignore = target / ".gitignore"
    ignore.unlink()
    if kind == "directory":
        ignore.mkdir()
    elif kind == "fifo":
        os.mkfifo(ignore)
    else:
        ignore.symlink_to(
            template / "CLAUDE.md" if kind == "outside" else target / "missing"
        )
    with pytest.raises(ValueError):
        plan_installation(template, target)
    assert not (target / ".factory/state.json").exists()


def test_unknown_legacy_customization_is_a_conflict(checkpoint):
    template, target = checkpoint
    write(target, "HARNESS.md", "unknown historical customization")
    commit(target)
    before = snapshot(target)
    plan = plan_installation(template, target, "update")
    assert any(a.path == "HARNESS.md" for a in plan.conflicts)
    assert snapshot(target) == before


@pytest.mark.parametrize("history", [None, "not-a-list", [None], ["invalid-hash"]])
def test_legacy_bad_hash_history_has_actionable_cli_refusal(checkpoint, history):
    import subprocess

    template, target = checkpoint
    write(
        target,
        ".harness/template-manifest.json",
        encoded(
            {
                "schema_version": 1,
                "template_version": "1.5.0",
                "files": {"factory": {"sha256": "a" * 64, "previous": history}},
            }
        ),
    )
    commit(target)
    before = snapshot(target)
    cli = Path(__file__).parents[3] / "factory"
    result = subprocess.run(
        [
            sys.executable,
            str(cli),
            "update",
            str(target),
            "--template",
            str(template),
            "--apply",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert "invalid sha256/history" in result.stderr
    assert "Traceback" not in result.stderr
    assert snapshot(target) == before
