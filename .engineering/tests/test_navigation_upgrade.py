"""Upgrade navigation through the public update preview and approval boundary."""

import json
import re
import tomllib

import pytest

from .test_doctor import doctor, record_installed
from .test_installation import adopt, engineering_process, installation
from .test_migration import commit, save, snapshot
from .test_navigation import CONFIG, LAUNCHER, select

__all__ = ["installation"]


@pytest.mark.parametrize("legacy_registry", [False, True])
def test_unused_graft_changes_only_with_approved_update(installation, legacy_registry):
    template, target = installation
    adopt(template, target)
    select(target, "graft", ["src"])
    if legacy_registry:
        path = target / ".engineering/dependencies.toml"
        path.write_text(path.read_text().replace('capability = "navigation"\n', ""))
    before_registry = tomllib.loads(
        (target / ".engineering/dependencies.toml").read_text()
    )
    before_config = (target / CONFIG).read_text()
    commit(target)
    before = snapshot(target)
    # Declining the preview means not supplying --apply; repeated previews are inert.
    for _ in range(2):
        result = engineering_process(template, "update", str(target))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "graft → none" in result.stdout
        assert 'provider = "graft"' in result.stdout
        assert "engineering deps install graft --apply" in result.stdout
        assert snapshot(target) == before
    result = engineering_process(template, "update", str(target), "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    config = tomllib.loads((target / CONFIG).read_text())
    expected = tomllib.loads(before_config)
    expected["navigation"]["provider"] = "none"
    assert config == expected
    next_registry = tomllib.loads(
        (target / ".engineering/dependencies.toml").read_text()
    )
    if legacy_registry:
        graft = next(
            row for row in before_registry["dependency"] if row["id"] == "graft"
        )
        graft["capability"] = "navigation"
    assert next_registry == before_registry
    result = doctor(target)
    assert "graft: MISSING" not in result.stdout
    commit(target)
    before = snapshot(target)
    result = engineering_process(template, "update", str(target), "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert snapshot(target) == before


@pytest.mark.parametrize("evidence", ["index", "installation"])
def test_update_keeps_used_graft(installation, evidence):
    template, target = installation
    adopt(template, target)
    select(target, "graft", ["src"])
    save(target, "src/app.py", "VALUE = 1\n")
    if evidence == "index":
        save(target, "graft/.graph/wiring.json", '{"nodes": []}\n')
    else:
        record_installed(target, {"matt-skills", "graft"})
    commit(target)
    before = snapshot(target)
    config = (target / CONFIG).read_bytes()
    result = engineering_process(template, "update", str(target))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Keep navigation provider graft" in result.stdout
    assert "graft → none" not in result.stdout
    assert snapshot(target) == before
    result = engineering_process(template, "update", str(target), "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (target / CONFIG).read_bytes() == config
    if evidence == "index":
        assert (target / "graft/.graph/wiring.json").read_bytes() == before[
            "graft/.graph/wiring.json"
        ]


def test_old_graft_record_reports_upgrade_instead_of_missing(installation):
    template, target = installation
    adopt(template, target)
    select(target, "graft", ["src"])
    save(target, "src/app.py", "VALUE = 1\n")
    record_installed(target, {"matt-skills", "graft"})
    path = target / ".engineering/state/dependencies.json"
    state = json.loads(path.read_text())
    for name in (LAUNCHER, "CLAUDE.md"):
        del state["dependencies"]["graft"]["outputs"][name]
    path.write_text(json.dumps(state))
    (target / LAUNCHER).unlink()
    policy = target / "CLAUDE.md"
    policy.write_text(
        policy.read_text().split("<!-- engineering:navigation:begin -->")[0]
    )
    commit(target)
    before = snapshot(target)
    result = engineering_process(template, "update", str(target))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "graft: UPGRADE REQUIRED" in result.stdout
    assert "engineering deps install graft --apply" in result.stdout
    assert snapshot(target) == before
    result = engineering_process(template, "update", str(target), "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    result = doctor(target)
    assert result.returncode == 1
    assert "graft: UPGRADE REQUIRED" in result.stdout
    assert "graft: MISSING" not in result.stdout
    assert "engineering deps install graft --apply" in result.stdout


def test_navigation_and_schema_migrations_preserve_project_text(installation):
    template, target = installation
    adopt(template, target)
    select(target, "graft", ["src"])
    path = target / CONFIG
    text = re.sub(r"(?ms)^\[review\].*", "", path.read_text())
    text = text.replace("schema_version = 2", "schema_version = 1 # old schema")
    text = text.replace('provider = "graft"', "provider = 'graft' # navigation choice")
    path.write_text(text)
    commit(target)
    before = snapshot(target)
    preview = engineering_process(template, "update", str(target))
    assert preview.returncode == 0, preview.stdout + preview.stderr
    assert "schema_version 1 → 2" in preview.stdout
    assert "graft → none" in preview.stdout
    assert snapshot(target) == before
    result = engineering_process(template, "update", str(target), "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    text = path.read_text()
    assert 'provider = "none" # navigation choice' in text
    assert "schema_version = 2 # old schema" in text
    config = tomllib.loads(text)
    assert config["navigation"]["application_roots"] == ["src"]
    assert config["review"]["documentation"] == ["README.md", "docs/**/*.md"]


@pytest.mark.parametrize(
    "navigation",
    [
        'navigation = {provider = "graft", application_roots = []}\n',
        'navigation.provider = "graft"\n',
        "",
    ],
)
def test_upgrade_accepts_navigation_table_forms_and_implicit_default(
    installation, navigation
):
    template, target = installation
    adopt(template, target)
    path = target / CONFIG
    text = re.sub(r"(?ms)^\[navigation\]\n.*?(?=^\[)", "", path.read_text())
    path.write_text(navigation + text)
    commit(target)
    result = engineering_process(template, "update", str(target), "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    assert tomllib.loads(path.read_text())["navigation"]["provider"] == "none"
