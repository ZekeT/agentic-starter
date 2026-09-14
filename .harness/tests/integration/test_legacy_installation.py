"""Exercise legacy installation migration through metadata, doctor and copied CLIs."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
import migrate_to_framework as m  # noqa: E402

pytestmark = pytest.mark.integration
STARTER = m.STARTER_DIR


@pytest.mark.parametrize("existing_config", [False, True])
@pytest.mark.parametrize("version_source", [None, "stamp", "manifest", "version-file"])
def test_migration_passes_doctor_after_external_setup(
    tmp_path, existing_config, version_source
):
    """Exercise migration output, preserving customization and supplying only external prerequisites."""
    import shutil
    import subprocess

    sys.path.insert(0, str(STARTER / ".harness"))
    from factory.doctor import diagnose

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    custom = {"maintainability": {"max_file_lines": 700}}
    if existing_config:
        path = tmp_path / ".harness/template-manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"schema_version": 1, "project": custom}))
        (tmp_path / "CLAUDE.md").write_text("Project instructions\n")
        (tmp_path / ".gitignore").write_text("custom-output/\n.env*\n!.env.template\n")
        (tmp_path / "Makefile").write_text("check:\n\t@echo project-check\n")
    version_paths = {
        "stamp": ".claude/template-version.json",
        "manifest": ".harness/template-manifest.json",
        "version-file": ".harness/TEMPLATE_VERSION",
    }
    if version_source:
        version_path = tmp_path / version_paths[version_source]
        version_path.parent.mkdir(parents=True, exist_ok=True)
        if version_source == "version-file":
            version_path.write_text("1.4.0\n")
        else:
            data = (
                json.loads(version_path.read_text())
                if version_path.exists()
                else {"schema_version": 1}
            )
            data["template_version"] = "1.4.0"
            version_path.write_text(json.dumps(data))
    audit = m.audit_target(tmp_path, STARTER)
    m.run_migration(tmp_path, STARTER, audit, force=False, dry=False)
    # OpenSpec and npm/Graft installation remain explicit external setup steps.
    (tmp_path / "openspec/config.yaml").write_text("schema: spec-driven\n")
    for name in (
        ".harness/graft/node_modules/@nanonets/graft/package.json",
        ".harness/graft/node_modules/@nanonets/graft/dist/cli.js",
        ".claude/skills/graft/SKILL.md",
    ):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(STARTER / name, dest)
    findings = [f for f in diagnose(tmp_path) if f.severity == "ERROR"]
    assert not findings, findings
    result = subprocess.run(
        [sys.executable, str(tmp_path / "factory"), "doctor"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    # Exercise the copied runner too: it must ship the shared parser dependency.
    (tmp_path / ".harness/evals/cases/999-smoke.yaml").write_text(
        "id: smoke\nkind: static\nwhy: runner packaging\nshell: true\n"
    )
    evaluation = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".harness/evals/run_evals.py"),
            "--only",
            "999",
        ],
        cwd="/",
        capture_output=True,
        text=True,
    )
    assert evaluation.returncode == 0, evaluation.stdout + evaluation.stderr
    data = json.loads((tmp_path / ".harness/template-manifest.json").read_text())
    upstream = json.loads((STARTER / ".harness/template-manifest.json").read_text())
    assert data["files"]["factory"] == upstream["files"]["factory"]
    assert data["template_version"] == (
        "1.4.0" if version_source else upstream["template_version"]
    )
    if existing_config:
        assert data["project"] == custom
        assert (tmp_path / "CLAUDE.md").read_text() == "Project instructions\n"
        assert (tmp_path / ".gitignore").read_text().startswith("custom-output/\n")
        assert (
            (tmp_path / "Makefile")
            .read_text()
            .startswith("check:\n\t@echo project-check\n")
        )
        assert "evals:" in (tmp_path / "Makefile").read_text()
    before = (tmp_path / ".harness/template-manifest.json").read_bytes()
    m.run_migration(
        tmp_path, STARTER, m.audit_target(tmp_path, STARTER), force=False, dry=False
    )
    assert (tmp_path / ".harness/template-manifest.json").read_bytes() == before


@pytest.mark.parametrize("kind", ["outside", "inside", "dangling", "directory", "fifo"])
def test_migration_rejects_unsafe_ignore_before_writes(tmp_path, kind):
    import os

    target = tmp_path / "target"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("preserve me\n")
    ignore = target / ".gitignore"
    if kind == "directory":
        ignore.mkdir()
    elif kind == "fifo":
        os.mkfifo(ignore)
    else:
        destination = outside if kind == "outside" else target / "rules"
        if kind == "inside":
            destination.write_text("preserve me\n")
        ignore.symlink_to(destination)
    before = sorted(p.relative_to(target).as_posix() for p in target.rglob("*"))
    pf = m.preflight_checks(target, STARTER, force=False)
    assert any(".gitignore" in blocker for blocker in pf.blockers)
    with pytest.raises(ValueError, match=".gitignore"):
        m.run_migration(target, STARTER, m.audit_target(target, STARTER), False, False)
    assert sorted(p.relative_to(target).as_posix() for p in target.rglob("*")) == before
    assert outside.read_text() == "preserve me\n"


@pytest.mark.parametrize("stamp", ['{"template_version":"1.3.0"}', "{bad", "{}"])
def test_migration_rejects_conflicting_or_invalid_versions_before_writes(
    tmp_path, stamp
):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".harness").mkdir()
    (tmp_path / ".claude/template-version.json").write_text(stamp)
    (tmp_path / ".harness/TEMPLATE_VERSION").write_text("1.4.0\n")
    before = {
        p.relative_to(tmp_path): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    with pytest.raises(ValueError):
        m.run_migration(
            tmp_path, STARTER, m.audit_target(tmp_path, STARTER), False, False
        )
    assert {
        p.relative_to(tmp_path): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    } == before


def test_cli_refuses_symlink_before_creating_migration_branch(tmp_path):
    import subprocess

    target = tmp_path / "project"
    target.mkdir()
    outside = tmp_path / "shared-ignore"
    outside.write_text("preserve me\n")
    (target / ".gitignore").symlink_to(outside)
    for args in (
        ["init", "-q"],
        ["add", ".gitignore"],
        [
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.com",
            "commit",
            "-qm",
            "baseline",
        ],
    ):
        subprocess.run(
            ["git", "-C", str(target), *args], check=True, capture_output=True
        )
    before = subprocess.check_output(["git", "-C", str(target), "branch", "--list"])
    result = subprocess.run(
        [
            sys.executable,
            str(STARTER / ".harness/scripts/migrate_to_framework.py"),
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Symlink source path is unsupported: .gitignore" in result.stdout
    assert (
        subprocess.check_output(["git", "-C", str(target), "branch", "--list"])
        == before
    )
    assert not (target / ".harness").exists()
    assert outside.read_text() == "preserve me\n"
