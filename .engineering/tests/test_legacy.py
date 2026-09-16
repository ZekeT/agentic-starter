"""Migrate representative old installations and retain customization evidence."""

import json

from engineering.migrate.common import execute
from engineering.migrate.legacy import old_region, plan
from engineering.ownership import digest, encoded

from .test_installation import ROOT, installation
from .test_migration import commit, save, snapshot

# Reuse the realistic distribution/target fixture across migration and update tests.
__all__ = ["installation"]


def legacy(target):
    data = json.loads((ROOT / ".engineering/tests/fixtures/legacy-v2.json").read_text())
    for name in (".claude/hooks/pre_tool_env_guard.py", ".claude/agents/verifier.md"):
        data[name] = (ROOT / name).read_text()
    data["REVIEW.md"] = "Previous managed review policy\n"
    files = {}
    for name, content in data.items():
        save(target, name, content)
        if name.startswith("openspec/"):
            continue
        scope = old_region(content.encode(), name)
        files[name] = {
            "sha256": digest(content.encode()),
            "previous": [],
            "owned_sha256": digest(scope or content.encode()),
            "ownership": {"mode": "section", "marker": "integration"}
            if scope
            else {"mode": "file"},
        }
    manifest = {
        "schema_version": 1,
        "ownership_version": 1,
        "template_version": "2.0.0",
        "files": files,
        "project": {
            "navigation": {"application_roots": []},
            "maintainability": {"warn_file_lines": 250},
        },
    }
    save(target, ".harness/template-manifest.json", encoded(manifest).decode())
    commit(target)


def test_legacy_plan_apply_and_rerun(installation):
    template, target = installation
    legacy(target)
    before = snapshot(target)
    assert execute(lambda: plan(template, target), apply=False) == 0
    assert snapshot(target) == before
    assert execute(lambda: plan(template, target), apply=True) == 0
    after = snapshot(target)
    assert "factory" not in after and "FACTORY.md" not in after
    assert "HARNESS.md" not in after and "engineering" in after
    assert "warn_file_lines = 250" in (target / ".engineering/config.toml").read_text()
    assert (target / "docs/migrations/openspec/in-progress.md").exists()
    assert not (target / "openspec").exists()
    assert execute(lambda: plan(template, target), apply=True) == 0
    assert snapshot(target) == after


def test_custom_old_docs_are_preserved_for_reconciliation(installation):
    template, target = installation
    legacy(target)
    save(target, "HARNESS.md", "Custom company policy\n")
    commit(target)
    assert execute(lambda: plan(template, target), apply=True) == 0
    assert (
        target / ".engineering/migrations/legacy-docs/HARNESS.md"
    ).read_text() == "Custom company policy\n"
    assert (
        "HARNESS.md"
        in (target / ".engineering/migrations/legacy-doc-customizations.md").read_text()
    )


def test_custom_legacy_code_conflicts_before_writes(installation):
    template, target = installation
    legacy(target)
    save(target, ".harness/scripts/tool.py", "print('local override')\n")
    commit(target)
    before = snapshot(target)
    assert execute(lambda: plan(template, target), apply=True) == 1
    assert snapshot(target) == before


def test_custom_shared_scope_conflicts_and_outside_region_survives(installation):
    template, target = installation
    legacy(target)
    save(target, "CLAUDE.md", "Company rule\n" + (target / "CLAUDE.md").read_text())
    commit(target)
    assert execute(lambda: plan(template, target), apply=True) == 0
    assert (target / "CLAUDE.md").read_text().startswith("Company rule\n")


def test_global_and_unknown_local_files_untouched(installation, tmp_path):
    template, target = installation
    legacy(target)
    global_skill = tmp_path / "home/.claude/plugins/superpowers/SKILL.md"
    global_skill.parent.mkdir(parents=True)
    global_skill.write_text("global skill untouched")
    save(target, ".harness/custom.txt", "local unknown file")
    commit(target)
    assert execute(lambda: plan(template, target), apply=True) == 0
    assert global_skill.read_text() == "global skill untouched"
    assert (target / ".harness/custom.txt").read_text() == "local unknown file"
