"""Prove dependency plans, pinned installs and customization protection offline."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from engineering.deps import npm_stage, operate, status
from engineering.registry import REGISTRY, STATE, registry, state

from .test_migration import snapshot

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize(
    "custom",
    ['"dependencies":{"custom":"1.0.0"}', '"scripts":{"prepare":"echo custom"}'],
)
def test_custom_npm_package_refused_before_execution(tmp_path, monkeypatch, custom):
    package = tmp_path / ".engineering/graft/package.json"
    package.parent.mkdir(parents=True)
    package.write_text("{" + custom + "}")

    def fail(*args):
        raise AssertionError("npm executed before customization check")

    monkeypatch.setattr("engineering.deps.run", fail)
    before = package.read_bytes()
    with pytest.raises(ValueError, match="destination_modified"):
        npm_stage(
            tmp_path,
            tmp_path / "staging",
            {"source": "@nanonets/graft", "version": "0.18.0"},
        )
    assert package.read_bytes() == before


def select_navigation(root, provider):
    (root / ".engineering/config.toml").write_text(
        f'schema_version = 2\n[navigation]\nprovider = "{provider}"\n'
    )


def deps(root, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "engineering"), "--root", str(root), "deps", *args],
        capture_output=True,
        text=True,
    )


def graft_row(output):
    return next(line for line in output.splitlines() if line.startswith("graft "))


@pytest.fixture
def dependency_repo(tmp_path, monkeypatch):
    (tmp_path / ".engineering").mkdir()
    shutil.copy2(ROOT / REGISTRY, tmp_path / REGISTRY)
    select_navigation(tmp_path, "graft")

    def stage(directory, row, installer):
        return {
            f".claude/skills/{skill}/SKILL.md": (row["version"] + "\n" + skill).encode()
            for skill in row["skills"]
        }

    monkeypatch.setattr("engineering.deps.stage", stage)
    return tmp_path


def test_plans_are_offline_and_nonmutating(dependency_repo, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Network/install called from a plan")

    monkeypatch.setattr("engineering.deps.run", fail)
    monkeypatch.setattr("engineering.deps.stage", fail)
    before = snapshot(dependency_repo)
    assert status(dependency_repo) == 0
    for operation in ("install", "update", "plan"):
        assert operate(dependency_repo, operation, None, apply=False) == 0
    assert snapshot(dependency_repo) == before


def test_install_update_idempotency_and_optional_selection(dependency_repo):
    root = dependency_repo
    assert operate(root, "install", "matt-skills", apply=True) == 0
    after = snapshot(root)
    assert operate(root, "install", "matt-skills", apply=True) == 0
    assert snapshot(root) == after
    assert set(state(root)["dependencies"]) == {"matt-skills"}
    assert operate(root, "update", "matt-skills", ref="a" * 40, apply=True) == 0
    assert state(root)["dependencies"]["matt-skills"]["installed_version"] == "a" * 40
    assert registry(root)["dependency"][0]["version"] == "a" * 40


def test_modified_outputs_refuse_before_install(dependency_repo):
    root = dependency_repo
    operate(root, "install", "show-me", apply=True)
    (root / ".claude/skills/show-me/SKILL.md").write_text("user customization")
    before = snapshot(root)
    with pytest.raises(ValueError, match="destination_modified"):
        operate(root, "update", "show-me", ref="b" * 40, apply=True)
    assert snapshot(root) == before


def test_unknown_existing_skill_is_not_claimed(dependency_repo):
    root = dependency_repo
    path = root / ".claude/skills/show-me/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("unmanaged skill")
    before = snapshot(root)
    with pytest.raises(ValueError, match="destination_modified"):
        operate(root, "install", "show-me", apply=True)
    assert snapshot(root) == before


def test_staging_failure_never_advances_state(dependency_repo, monkeypatch):
    root = dependency_repo
    operate(root, "install", "show-me", apply=True)
    before = (root / STATE).read_bytes()

    def fail(*args):
        raise ValueError("fixture download failed")

    monkeypatch.setattr("engineering.deps.stage", fail)
    with pytest.raises(ValueError, match="download failed"):
        operate(root, "update", "show-me", ref="b" * 40, apply=True)
    assert (root / STATE).read_bytes() == before


@pytest.mark.parametrize("ref", ["main", "latest", "../outside", "abc123"])
def test_mutable_or_malformed_refs_rejected(dependency_repo, ref):
    with pytest.raises(ValueError, match="pin"):
        operate(dependency_repo, "update", "matt-skills", ref=ref, apply=False)


def test_graft_required_only_while_navigation_selects_it(dependency_repo):
    root = dependency_repo
    operate(root, "install", "matt-skills", apply=True)
    selected = deps(root, "status")
    assert selected.returncode == 0 and "MISSING" in graft_row(selected.stdout)
    plan = deps(root, "install")
    assert plan.returncode == 0 and "graft:" in plan.stdout
    select_navigation(root, "none")
    before = snapshot(root)
    disabled = deps(root, "status")
    assert disabled.returncode == 0
    assert "MISSING" not in graft_row(disabled.stdout)
    assert "navigation" in graft_row(disabled.stdout)
    plan = deps(root, "install")
    assert plan.returncode == 0 and "graft:" not in plan.stdout
    # Setup's required installation succeeds without Graft.
    applied = deps(root, "install", "--apply")
    assert applied.returncode == 0, applied.stderr
    assert "graft:" not in applied.stdout
    assert snapshot(root) == before
    refused = deps(root, "install", "graft")
    assert refused.returncode == 1 and '"graft"' in refused.stderr
    assert snapshot(root) == before


@pytest.mark.parametrize("capability", ["unknown", 1, ""])
def test_unknown_capability_rejected(dependency_repo, capability):
    root = dependency_repo
    path = root / REGISTRY
    text = path.read_text().replace(
        'source = "humanlayer/skills"\n',
        f'source = "humanlayer/skills"\ncapability = {json.dumps(capability)}\n',
    )
    path.write_text(text)
    result = deps(root, "status")
    assert result.returncode == 1 and "capability" in result.stderr


@pytest.mark.parametrize("breakage", ["ok", "modified", "missing", "pin changed"])
def test_unselected_recorded_graft_left_untouched(
    dependency_repo, monkeypatch, tmp_path_factory, breakage
):
    from .test_doctor import record_installed

    root = dependency_repo
    # Any attempted installation fails instead of reaching the network.
    stubs = tmp_path_factory.mktemp("stubs")
    for tool in ("npm", "npx", "node"):
        (stubs / tool).write_text("#!/bin/sh\nexit 1\n")
        (stubs / tool).chmod(0o755)
    monkeypatch.setenv("PATH", f"{stubs}:{__import__('os').environ['PATH']}")
    version = "0.17.0" if breakage == "pin changed" else "0.18.0"
    package = root / ".engineering/graft"
    package.mkdir()
    (package / "package.json").write_text(
        json.dumps({"dependencies": {"@nanonets/graft": version}})
    )
    (package / "package-lock.json").write_text("{}")
    record_installed(root, {"matt-skills", "graft"}, graft_version=version)
    if breakage == "modified":
        (root / ".claude/skills/graft/SKILL.md").write_text("local edit\n")
    elif breakage == "missing":
        (root / ".engineering/graft/node_modules/@nanonets/graft/package.json").unlink()
    select_navigation(root, "none")
    before = snapshot(root)
    reported = deps(root, "status")
    assert reported.returncode == 0, reported.stderr
    assert "NOT SELECTED (navigation)" in graft_row(reported.stdout)
    for operation in ("install", "update"):
        applied = deps(root, operation, "--apply")
        assert applied.returncode == 0, applied.stderr
        assert "graft:" not in applied.stdout
        assert "Already installed at desired pins." in applied.stdout
    assert snapshot(root) == before


def test_capability_dependency_must_be_a_provider_value(dependency_repo):
    root = dependency_repo
    path = root / REGISTRY
    path.write_text(
        path.read_text().replace(
            'source = "humanlayer/skills"\n',
            'source = "humanlayer/skills"\ncapability = "navigation"\n',
        )
    )
    result = deps(root, "status")
    assert result.returncode == 1 and "deps.capability" in result.stderr
    assert "show-me" in result.stderr


def test_invalid_provider_fails_before_partial_status(dependency_repo):
    select_navigation(dependency_repo, "other")
    result = deps(dependency_repo, "status")
    assert result.returncode == 1 and "navigation.provider" in result.stderr
    assert result.stdout == ""


def test_other_npm_dependency_is_not_judged_by_graft_content(tmp_path):
    from engineering.registry import installed_status

    row = {"id": "other", "kind": "npm", "source": "other", "version": "1.0.0"}
    row["required"] = True
    record = {"managed": True, "installed_version": "1.0.0", "outputs": {}}
    assert installed_status(tmp_path, row, {"other": record}) == ("1.0.0", "OK")
