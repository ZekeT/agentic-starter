"""Exercise adopted project preservation and three-way update safety end to end."""

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from engineering.adoption import plan_installation
from engineering.apply import apply_plan
from engineering.distribution import content, payload_path
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
            dst.write_bytes(
                content(ROOT, name) if name != MANIFEST_PATH else src.read_bytes()
            )
            dst.chmod(payload_path(ROOT, name).stat().st_mode)
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
    save(template, ".engineering/config.toml", "schema_version = 3\n")
    refresh(template)
    before = snapshot(target)
    with pytest.raises(ValueError, match="config.schema"):
        plan_installation(template, target, "update")
    assert snapshot(target) == before


def engineering_process(template, *args):
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "engineering"),
            *args,
            "--template",
            template,
        ],
        capture_output=True,
        text=True,
    )


def test_update_records_missing_installation_role(installation):
    template, target = installation
    applied = engineering_process(template, "adopt", str(target), "--apply")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    state = target / STATE_PATH
    assert json.loads(state.read_text())["role"] == "consumer"
    commit(target)
    # An installation from before roles existed.
    data = json.loads(state.read_text())
    del data["role"]
    state.write_bytes(encoded(data))
    commit(target)
    before = snapshot(target)
    preview = engineering_process(template, "update", str(target))
    assert preview.returncode == 0, preview.stdout + preview.stderr
    assert "installation role" in preview.stdout and "consumer" in preview.stdout
    assert snapshot(target) == before
    applied = engineering_process(template, "update", str(target), "--apply")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert json.loads(state.read_text())["role"] == "consumer"


CONFIG = ".engineering/config.toml"


def engineering(capsys, template, *args):
    """Run the ./engineering command line from a distribution checkout."""
    from engineering.cli import main

    status = main(["--root", str(template), *args])
    output = capsys.readouterr()
    return status, output.out + output.err


def customize(root, **values):
    text = (root / CONFIG).read_text()
    for key, value in values.items():
        text, count = re.subn(rf"(?m)^{key} = .*$", f"{key} = {value}", text)
        assert count == 1, key
    save(root, CONFIG, text)


def test_configuration_is_project_owned_and_survives_updates(installation, capsys):
    template, target = installation
    status, output = engineering(capsys, template, "adopt", str(target), "--apply")
    assert status == 0, output
    commit(target)
    installed = json_object((target / MANIFEST_PATH).read_bytes())
    assert installed["files"][CONFIG]["ownership"] == {"mode": "preserve"}
    assert CONFIG not in json_object((target / STATE_PATH).read_bytes())["entries"]
    customize(target, warn_file_lines=250)
    commit(target)
    customize(template, warn_file_lines=280, max_file_lines=600)
    refresh(template)
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 0, output
    assert "CONFLICT" not in output
    config = (target / CONFIG).read_text()
    assert "warn_file_lines = 250" in config and "max_file_lines = 500" in config


def test_installed_managed_configuration_moves_to_project_ownership(
    installation, capsys
):
    template, target = installation
    adopt(template, target)
    # Earlier releases recorded the configuration as whole-file managed.
    raw = (target / CONFIG).read_bytes()
    manifest = json_object((target / MANIFEST_PATH).read_bytes())
    manifest["files"][CONFIG].update(
        ownership={"mode": "file"}, sha256=digest(raw), owned_sha256=digest(raw)
    )
    state = json_object((target / STATE_PATH).read_bytes())
    state["entries"][CONFIG] = {"ownership": {"mode": "file"}, "upstream": digest(raw)}
    (target / MANIFEST_PATH).write_bytes(encoded(manifest))
    (target / STATE_PATH).write_bytes(encoded(state))
    customize(target, warn_file_lines=250)
    commit(target)
    customize(template, warn_file_lines=280)
    refresh(template)
    before = snapshot(target)
    status, output = engineering(capsys, template, "update", str(target))
    assert status == 0, output
    assert f"{CONFIG}: Now project-owned" in output
    assert snapshot(target) == before
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 0, output
    assert "warn_file_lines = 250" in (target / CONFIG).read_text()
    installed = json_object((target / MANIFEST_PATH).read_bytes())
    assert installed["files"][CONFIG]["ownership"] == {"mode": "preserve"}
    assert CONFIG not in json_object((target / STATE_PATH).read_bytes())["entries"]


def test_configuration_schema_change_is_migrated_in_the_update(
    installation, capsys, monkeypatch
):
    from engineering import settings

    template, target = installation
    adopt(template, target)
    customize(target, warn_file_lines=250)
    commit(target)
    # Simulate a release whose configuration schema moved to version 3.
    monkeypatch.setattr(settings, "SCHEMA_VERSION", 3)
    monkeypatch.setitem(
        settings.MIGRATIONS,
        2,
        lambda text: text.replace("schema_version = 2", "schema_version = 3", 1),
    )
    customize(template, schema_version=3)
    refresh(template)
    before = snapshot(target)
    status, output = engineering(capsys, template, "update", str(target))
    assert status == 0, output
    assert f"MIGRATE {CONFIG}" in output and "2 → 3" in output
    assert snapshot(target) == before
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 0, output
    config = (target / CONFIG).read_text()
    assert "schema_version = 3" in config and "warn_file_lines = 250" in config


def test_review_settings_arrive_only_with_the_approved_update(installation, capsys):
    template, target = installation
    adopt(template, target)
    # A project configured before review settings existed, with its own values.
    config = (target / CONFIG).read_text()
    config = config.split("\n[review]")[0].replace(
        "schema_version = 2", "schema_version = 1  # before review settings"
    )
    save(target, CONFIG, config)
    customize(target, warn_file_lines=250)
    commit(target)
    before = snapshot(target)
    status, output = engineering(capsys, template, "update", str(target))
    assert status == 0, output
    assert f"MIGRATE {CONFIG}" in output and "schema_version 1 → 2" in output
    assert snapshot(target) == before
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 0, output
    text = (target / CONFIG).read_text()
    assert "schema_version = 2  # before review settings" in text
    migrated = tomllib.loads(text)
    assert migrated["schema_version"] == 2
    assert migrated["review"] == {
        "documentation": ["README.md", "docs/**/*.md"],
        "sensitive": [],
    }
    assert migrated["maintainability"]["warn_file_lines"] == 250
    assert migrated["tracker"] == tomllib.loads(config)["tracker"]


def test_missing_schema_migration_blames_the_starter(installation, capsys, monkeypatch):
    from engineering import settings

    template, target = installation
    adopt(template, target)
    # Simulate a release that moved the schema but shipped no migration step.
    monkeypatch.setattr(settings, "SCHEMA_VERSION", 3)
    customize(template, schema_version=3)
    refresh(template)
    before = snapshot(target)
    status, output = engineering(capsys, template, "update", str(target))
    assert status == 1
    assert "no migration from version 2" in output
    assert "update the starter or report the missing migration" in output
    assert "repair project configuration" not in output
    assert snapshot(target) == before


def test_invalid_configuration_fails_update_and_doctor(installation, capsys):
    template, target = installation
    adopt(template, target)
    customize(target, warn_file_lines=900)
    commit(target)
    before = snapshot(target)
    for mode in ("--plan", "--apply"):
        status, output = engineering(capsys, template, "update", str(target), mode)
        assert status == 1
        assert f"update: {CONFIG}" in output and "warn_file_lines" in output
        assert snapshot(target) == before
    status, output = engineering(capsys, target, "doctor")
    assert status == 1
    assert f"ERROR [configuration] {CONFIG}" in output


def test_managed_implementation_edit_still_conflicts(installation, capsys):
    template, target = installation
    adopt(template, target)
    save(target, "REVIEW.md", "Local managed edit\n")
    commit(target)
    save(template, "REVIEW.md", "Upstream managed change\n")
    refresh(template)
    before = snapshot(target)
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 1
    assert "CONFLICT REVIEW.md" in output
    assert snapshot(target) == before


def test_configuration_seeds_from_maintainer_template_copy(installation, capsys):
    template, target = installation
    # The maintainer checkout's own configuration is its project configuration.
    customize(template, warn_file_lines=260)
    shipped = (ROOT / ".engineering/template/config.toml").read_text()
    save(template, ".engineering/template/config.toml", shipped)
    save(
        template,
        ".engineering/template/files.json",
        json.dumps(
            {
                "schema_version": 1,
                "managed": {CONFIG: ".engineering/template/config.toml"},
                "application": {},
            }
        ),
    )
    status, output = engineering(capsys, template, "adopt", str(target), "--apply")
    assert status == 0, output
    assert (target / CONFIG).read_text() == shipped
    assert (
        tomllib.loads((template / CONFIG).read_text())["maintainability"][
            "warn_file_lines"
        ]
        == 260
    )
