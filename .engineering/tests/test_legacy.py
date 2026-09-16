"""Migrate representative old installations and retain customization evidence."""

import json

import pytest
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
    assert not (target / "docs/migrations/openspec/in-progress.md").exists()
    assert (target / "openspec").exists()
    assert all(
        after[name] == raw
        for name, raw in before.items()
        if name.startswith("openspec/")
    )
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


def test_legacy_graphify_ignore_survives_outside_managed_region(installation):
    template, target = installation
    legacy(target)
    ignore = target / ".gitignore"
    raw = ignore.read_bytes().replace(
        b"# factory:integration:end", b"/graphify-out/\n# factory:integration:end"
    )
    ignore.write_bytes(raw)
    manifest_path = target / ".harness/template-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][".gitignore"]["sha256"] = digest(raw)
    manifest_path.write_bytes(encoded(manifest))
    commit(target)
    assert b"/graphify-out/" not in (template / ".gitignore").read_bytes()
    assert execute(lambda: plan(template, target), apply=True) == 0
    migrated = ignore.read_text()
    assert migrated.count("/graphify-out/") == 1
    assert migrated.index("/graphify-out/") > migrated.index(
        "# engineering:integration:end"
    )
    assert execute(lambda: plan(template, target), apply=True) == 0
    assert ignore.read_text() == migrated


def test_legacy_preserves_openspec_commands_markers_and_hooks(installation):
    template, target = installation
    legacy(target)
    command = ".claude/commands/opsx/propose.md"
    save(target, command, "OpenSpec command\n")
    markers = "<!-- OPENSPEC:START -->\nUse OpenSpec\n<!-- OPENSPEC:END -->\n"
    instructions = (
        (target / "CLAUDE.md")
        .read_text()
        .replace("Legacy instructions\n", "Legacy instructions\n" + markers)
    )
    save(target, "CLAUDE.md", instructions)
    hook = {"type": "command", "command": "openspec validate"}
    save(
        target,
        ".claude/settings.json",
        json.dumps({"hooks": {"Stop": [{"hooks": [hook]}]}}),
    )
    manifest_path = target / ".harness/template-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name in (command, "CLAUDE.md", ".claude/settings.json"):
        raw = (target / name).read_bytes()
        manifest["files"][name] = {"sha256": digest(raw), "ownership": {"mode": "file"}}
    manifest_path.write_bytes(encoded(manifest))
    commit(target)
    proposed = plan(template, target)
    assert any("/migrate-from-openspec" in note for note in proposed.notes)
    assert execute(lambda: plan(template, target), apply=True) == 0
    assert (target / command).read_text() == "OpenSpec command\n"
    assert markers in (target / "CLAUDE.md").read_text()
    settings = json.loads((target / ".claude/settings.json").read_text())
    assert hook in [
        item for group in settings["hooks"]["Stop"] for item in group["hooks"]
    ]


def test_legacy_refuses_to_discard_openspec_make_targets(installation):
    template, target = installation
    legacy(target)
    makefile = target / "Makefile"
    raw = makefile.read_bytes() + b"\nopenspec-check:\n\topenspec validate\n"
    makefile.write_bytes(raw)
    manifest_path = target / ".harness/template-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"]["Makefile"]["sha256"] = digest(raw)
    manifest_path.write_bytes(encoded(manifest))
    commit(target)
    before = snapshot(target)
    assert execute(lambda: plan(template, target), apply=True) == 1
    assert snapshot(target) == before


@pytest.mark.parametrize("name", ["CLAUDE.md", "AGENTS.md"])
def test_legacy_refuses_to_discard_unmarked_openspec_instructions(installation, name):
    template, target = installation
    legacy(target)
    raw = (
        b"<!-- harness:integration:begin -->\n"
        b"Use openspec validate before delivery\n"
        b"<!-- harness:integration:end -->\n"
    )
    save(target, name, raw.decode())
    manifest_path = target / ".harness/template-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][name] = {
        "sha256": digest(raw),
        "ownership": {"mode": "file"},
    }
    manifest_path.write_bytes(encoded(manifest))
    commit(target)
    before = snapshot(target)
    assert execute(lambda: plan(template, target), apply=True) == 1
    assert snapshot(target) == before
