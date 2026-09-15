"""Apply preflight and recovery must be observable at the public boundary."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / ".harness"))

import pytest
from factory.adoption import plan_installation
from factory.apply import apply_plan
from factory.ownership import digest, encoded

from .test_lifecycle_checkpoint import checkpoint as checkpoint
from .test_lifecycle_checkpoint import commit, snapshot, write

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("change", ["dirty", "commit", "ignored-input", "template"])
def test_changed_inputs_refuse_before_writes(checkpoint, change):
    template, target = checkpoint
    plan = plan_installation(template, target)
    if change == "dirty":
        write(target, "untracked.txt", "work")
    elif change == "commit":
        write(target, "new-project.txt", "work")
        commit(target)
    elif change == "ignored-input":
        # A committed change is detected even when the changed contents become ignored.
        write(target, ".gitignore", ".harness/\n")
        commit(target)
    else:
        path = template / "CLAUDE.md"
        path.write_bytes(path.read_bytes() + b"template changed outside scope\n")
    before = snapshot(target)
    with pytest.raises(ValueError):
        apply_plan(plan)
    assert snapshot(target) == before


@pytest.mark.parametrize("stage", ["content", "state", "doctor"])
def test_failures_report_recovery_without_success(
    checkpoint, monkeypatch, capsys, stage
):
    from pathlib import Path

    from factory import apply

    template, target = checkpoint
    plan = plan_installation(template, target)
    original = Path.write_bytes

    def fail_write(path, content):
        if (stage == "state" and path == target / ".factory/state.json") or (
            stage == "content" and path == target / "factory"
        ):
            raise OSError("injected write failure")
        return original(path, content)

    if stage == "doctor":
        monkeypatch.setattr(apply.doctor, "run", lambda root: 1)
    else:
        monkeypatch.setattr(Path, "write_bytes", fail_write)
    assert apply_plan(plan) == 1
    output = capsys.readouterr().out
    assert "Recovery commit:" in output and plan.baseline in output
    assert "Affected files:" in output and "git restore" in output
    assert "Applied successfully" not in output


def test_copied_runtime_doctor_and_cli(checkpoint):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    result = subprocess.run(
        [sys.executable, str(target / "factory"), "doctor"],
        cwd="/",
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "name",
    [
        ".harness/template-manifest.json",
        ".factory/state.json",
        "CLAUDE.md",
        ".claude/settings.json",
        "pyproject.toml",
    ],
)
@pytest.mark.parametrize("kind", ["fifo", "directory", "symlink"])
def test_public_cli_nonregular_inputs_are_bounded(checkpoint, name, kind):
    import os
    from pathlib import Path

    template, target = checkpoint
    path = target / name
    if path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(target / "absent")
    cli = Path(__file__).parents[3] / "factory"
    result = subprocess.run(
        [sys.executable, str(cli), "adopt", str(target), "--template", str(template)],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Traceback" not in result.stderr


def test_local_only_update_and_upstream_removal_preserve(checkpoint):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    write(target, "HARNESS.md", "my customized documentation\n")
    commit(target)
    local = plan_installation(template, target, "update")
    assert not local.conflicts
    assert next(a for a in local.actions if a.path == "HARNESS.md").content is None
    manifest = json.loads((template / ".harness/template-manifest.json").read_text())
    del manifest["files"]["HARNESS.md"]
    write(template, ".harness/template-manifest.json", encoded(manifest))
    removed = plan_installation(template, target, "update")
    assert next(a for a in removed.actions if a.path == "HARNESS.md").kind == "PRESERVE"
    assert apply_plan(removed) == 0
    assert (target / "HARNESS.md").read_text() == "my customized documentation\n"


def test_dual_change_does_not_advance_state(checkpoint):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    write(target, "HARNESS.md", "local")
    commit(target)
    write(template, "HARNESS.md", "upstream")
    manifest = json.loads((template / ".harness/template-manifest.json").read_text())
    manifest["files"]["HARNESS.md"]["sha256"] = digest(b"upstream")
    write(template, ".harness/template-manifest.json", encoded(manifest))
    manifest["files"]["HARNESS.md"]["owned_sha256"] = digest(b"upstream")
    write(template, ".harness/template-manifest.json", encoded(manifest))
    before = snapshot(target)
    plan = plan_installation(template, target, "update")
    assert any(a.path == "HARNESS.md" for a in plan.conflicts)
    with pytest.raises(ValueError):
        apply_plan(plan)
    assert snapshot(target) == before


def test_metadata_corruption_cannot_rebase_customized_content(checkpoint):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    write(target, "HARNESS.md", "local customization")
    path = target / ".factory/state.json"
    state = json.loads(path.read_text())
    state["entries"]["HARNESS.md"]["upstream"] = digest(b"local customization")
    path.write_bytes(encoded(state))
    commit(target)
    before = snapshot(target)
    with pytest.raises(ValueError, match="baseline disagrees"):
        plan_installation(template, target, "update")
    assert snapshot(target) == before


def test_chmod_invalidates_an_existing_plan(checkpoint):
    template, target = checkpoint
    plan = plan_installation(template, target)
    path = target / "CLAUDE.md"
    path.chmod(0o600)
    before = snapshot(target)
    with pytest.raises(ValueError, match="changed|Changed"):
        apply_plan(plan)
    assert snapshot(target) == before


def test_restore_executable_permission_is_visible(checkpoint):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    (target / "factory").chmod(0o644)
    commit(target)
    plan = plan_installation(template, target, "update")
    assert next(a for a in plan.actions if a.path == "factory").kind == "MERGE"
    assert apply_plan(plan) == 0
    assert (target / "factory").stat().st_mode & 0o111


@pytest.mark.parametrize(
    "marker_change", ["closing-prefix", "opening-cr-junk", "closing-cr-junk"]
)
def test_update_cli_refuses_malformed_markers_without_writes(checkpoint, marker_change):
    template, target = checkpoint
    assert apply_plan(plan_installation(template, target)) == 0
    path = target / "Makefile"
    content = path.read_bytes()
    if marker_change == "closing-prefix":
        content = content.replace(
            b"# factory:integration:end", b"local# factory:integration:end"
        )
    elif marker_change == "opening-cr-junk":
        content = content.replace(
            b"# factory:integration:begin\n", b"# factory:integration:begin\rjunk\n"
        )
    else:
        content = content.replace(
            b"# factory:integration:end\n", b"# factory:integration:end\rjunk\n"
        )
    path.write_bytes(content)
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
    assert result.returncode == 1, result.stdout + result.stderr
    assert "complete LF/CRLF lines" in result.stderr
    assert "Traceback" not in result.stderr
    assert snapshot(target) == before
