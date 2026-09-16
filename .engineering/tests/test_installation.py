"""Exercise adopted project preservation and three-way update safety end to end."""

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from engineering.adoption import plan_installation
from engineering.apply import apply_plan
from engineering.installation import MANIFEST_PATH, STATE_PATH
from engineering.ownership import digest, encoded, json_object, owned_content

from .test_migration import commit, git, save, snapshot

ROOT = Path(__file__).parents[2]


def refresh(template):
    path = template / MANIFEST_PATH
    data = json_object(path.read_bytes())
    for name, entry in list(data["files"].items()):
        target = template / name
        if not target.exists():
            del data["files"][name]
            continue
        raw = target.read_bytes()
        entry["sha256"] = digest(raw)
        entry["owned_sha256"] = digest(owned_content(raw, name, entry["ownership"]))
    path.write_bytes(encoded(data))


@pytest.fixture
def installation(tmp_path):
    template = tmp_path / "template"
    manifest = json_object((ROOT / MANIFEST_PATH).read_bytes())
    for name in [MANIFEST_PATH, *manifest["files"]]:
        src, dst = ROOT / name, template / name
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    target = tmp_path / "target"
    target.mkdir()
    git(target, "init", "-b", "main")
    git(target, "config", "user.name", "Fixture")
    git(target, "config", "user.email", "fixture@example.invalid")
    save(target, "Makefile", "check:\n\t@echo native check\n")
    save(target, "package.json", '{"scripts":{"test":"native tests"}}\n')
    save(target, "CLAUDE.md", "# Native project rules\n")
    save(target, ".gitlab-ci.yml", "# native CI\n")
    commit(target)
    return template, target


def adopt(template, target):
    plan = plan_installation(template, target)
    assert not plan.conflicts
    assert apply_plan(plan) == 0
    commit(target)


def test_adoption_plan_and_native_boundaries(installation):
    template, target = installation
    before = snapshot(target)
    plan = plan_installation(template, target)
    assert snapshot(target) == before
    assert apply_plan(plan) == 0
    assert (target / "Makefile").read_bytes().startswith(before["Makefile"])
    assert (target / "CLAUDE.md").read_bytes().startswith(before["CLAUDE.md"])
    assert (target / "package.json").read_bytes() == before["package.json"]
    assert (target / ".gitlab-ci.yml").read_bytes() == before[".gitlab-ci.yml"]
    assert not (target / "pyproject.toml").exists()


def test_pristine_update_and_local_only_preservation(installation):
    template, target = installation
    adopt(template, target)
    save(
        template,
        "REVIEW.md",
        (template / "REVIEW.md").read_text() + "\nNew upstream rule\n",
    )
    refresh(template)
    assert apply_plan(plan_installation(template, target, "update")) == 0
    assert (target / "REVIEW.md").read_bytes() == (template / "REVIEW.md").read_bytes()
    commit(target)
    save(target, "REVIEW.md", "Customized review policy\n")
    commit(target)
    before = snapshot(target)
    assert apply_plan(plan_installation(template, target, "update")) == 0
    assert snapshot(target) == before


def test_both_changed_conflicts_without_advancing_baselines(installation):
    template, target = installation
    adopt(template, target)
    save(target, "REVIEW.md", "Local changed\n")
    commit(target)
    save(template, "REVIEW.md", "Upstream changed\n")
    refresh(template)
    before = snapshot(target)
    plan = plan_installation(template, target, "update")
    assert plan.conflicts
    assert not any(a.path in {STATE_PATH, MANIFEST_PATH} for a in plan.actions)
    with pytest.raises(ValueError, match="conflicts"):
        apply_plan(plan)
    assert snapshot(target) == before


@pytest.mark.parametrize("customized", [False, True])
def test_removed_upstream_file(installation, customized):
    template, target = installation
    adopt(template, target)
    name = ".engineering/docs/coding-standards.md"
    if customized:
        save(target, name, "Local customization\n")
        commit(target)
    (template / name).unlink()
    refresh(template)
    plan = plan_installation(template, target, "update")
    assert bool(plan.conflicts) == customized
    if not customized:
        assert apply_plan(plan) == 0
        assert not (target / name).exists()


def test_shared_regions_and_settings_preserve_custom_content(installation):
    template, target = installation
    save(
        target,
        ".claude/settings.json",
        '{"permissions":{"allow":["project"]},"hooks":{"Stop":[{"hooks":[{"type":"command","command":"project-hook"}]}]}}',
    )
    commit(target)
    adopt(template, target)
    settings = json_object((target / ".claude/settings.json").read_bytes())
    assert settings["permissions"] == {"allow": ["project"]}
    assert settings["hooks"]["Stop"][0]["hooks"][0]["command"] == "project-hook"
    save(
        template,
        "CLAUDE.md",
        (template / "CLAUDE.md")
        .read_text()
        .replace("# Project agent instructions", "# Updated agent instructions"),
    )
    refresh(template)
    assert apply_plan(plan_installation(template, target, "update")) == 0
    assert (target / "CLAUDE.md").read_text().startswith("# Native project rules\n")


def test_system_update_does_not_update_dependency_pins(installation):
    template, target = installation
    adopt(template, target)
    path = ".engineering/dependencies.toml"
    before = (target / path).read_bytes()
    save(
        template,
        path,
        (template / path)
        .read_text()
        .replace('version = "0.18.0"', 'version = "0.19.0"'),
    )
    refresh(template)
    assert apply_plan(plan_installation(template, target, "update")) == 0
    assert (target / path).read_bytes() == before


def test_dirty_and_stale_inputs_refuse(installation):
    template, target = installation
    plan = plan_installation(template, target)
    save(target, "user.md", "unsaved work\n")
    with pytest.raises(ValueError, match="Dirty"):
        apply_plan(plan)
    commit(target)
    with pytest.raises(ValueError, match="changed"):
        apply_plan(plan)


def test_new_upstream_file_and_unknown_config_schema(installation):
    template, target = installation
    adopt(template, target)
    name = ".engineering/docs/new-policy.md"
    save(template, name, "New upstream policy\n")
    data = json_object((template / MANIFEST_PATH).read_bytes())
    raw = (template / name).read_bytes()
    data["files"][name] = {
        "ownership": {"mode": "file"},
        "sha256": digest(raw),
        "owned_sha256": digest(raw),
        "previous": [],
    }
    (template / MANIFEST_PATH).write_bytes(encoded(data))
    assert apply_plan(plan_installation(template, target, "update")) == 0
    assert (target / name).read_bytes() == raw
    commit(target)
    save(template, ".engineering/config.toml", "schema_version = 2\n")
    refresh(template)
    before = snapshot(target)
    with pytest.raises(ValueError, match="config.schema"):
        plan_installation(template, target, "update")
    assert snapshot(target) == before
