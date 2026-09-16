"""Prove dependency plans, pinned installs and customization protection offline."""

import shutil
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


@pytest.fixture
def dependency_repo(tmp_path, monkeypatch):
    (tmp_path / ".engineering").mkdir()
    shutil.copy2(ROOT / REGISTRY, tmp_path / REGISTRY)

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
