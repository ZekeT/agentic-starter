"""Toggle optional navigation through generation, dependency, update and doctor commands."""

import json
import re
import sys
from pathlib import Path

import pytest

from .template_toolchain import toolchain
from .test_doctor import doctor, navigate, record_installed
from .test_installation import adopt, engineering, installation
from .test_migration import commit, save, snapshot
from .test_template import build, contents, run

__all__ = ["installation"]

ROOT = Path(__file__).parents[2]
CONFIG = ".engineering/config.toml"
LAUNCHER = ".engineering/bin/graft"
PINS = (".engineering/graft/package.json", ".engineering/graft/package-lock.json")
SKILL = ".claude/skills/graft/SKILL.md"
MARKER = "engineering:navigation:begin"


def select(root, provider, roots=None):
    path = root / CONFIG
    text = re.sub(
        r'(?m)^provider = "(graft|none)"$',
        f'provider = "{provider}"',
        path.read_text(),
        count=1,
    )
    if roots is not None:
        text = re.sub(
            r"(?m)^application_roots = .*$",
            f"application_roots = {json.dumps(roots)}",
            text,
        )
    path.write_text(text)


def navigation_content(root):
    present = [name for name in (LAUNCHER, *PINS, SKILL) if (root / name).exists()]
    if MARKER in (root / "CLAUDE.md").read_text():
        present.append("CLAUDE.md")
    return present


def test_generated_project_enables_and_disables_navigation(tmp_path):
    root = build(tmp_path / "project")
    env = toolchain(tmp_path / "tools")

    def call(*args, cwd=root):
        return run(*args, cwd=cwd, env=env)

    def ok(*args, cwd=root):
        result = call(*args, cwd=cwd)
        assert result.returncode == 0, result.stdout + result.stderr
        return result

    # A new consumer project starts with navigation disabled and nothing Graft-related.
    assert 'provider = "none"' in (root / CONFIG).read_text()
    assert navigation_content(root) == []
    policy = (root / "CLAUDE.md").read_text()
    assert ".engineering/bin/graft" not in policy
    assert "search and read" in policy
    manifest = json.loads((root / ".engineering/manifest.json").read_text())
    assert not {LAUNCHER, *PINS} & manifest["files"].keys()
    for name in ("git init -b main", "git config user.name Fixture"):
        ok(*name.split())
    ok("git", "config", "user.email", "fixture@example.invalid")
    ok("make", "setup")
    calls = Path(env["TEMPLATE_CALLS"]).read_text()
    assert '"npm"' not in calls and navigation_content(root) == []
    assert "navigation disabled" in ok("./engineering", "doctor").stdout
    refused = call("./engineering", "navigation", "map")
    assert refused.returncode == 1 and "navigation disabled" in refused.stderr
    save(root, "src/app.py", "VALUE = 1\n")
    ok("git", "add", ".")
    ok("git", "commit", "-m", "Initialize application")
    generated_policy = (root / "CLAUDE.md").read_bytes()

    # Enabling previews, then installs the package, launcher, skill, pins and guidance.
    select(root, "graft", ["src"])
    before = contents(root)
    preview = ok("./engineering", "deps", "install")
    assert "graft: missing" in preview.stdout
    assert contents(root) == before
    ok("./engineering", "deps", "install", "--apply")
    assert sorted(navigation_content(root)) == sorted(
        [LAUNCHER, *PINS, SKILL, "CLAUDE.md"]
    )
    # The first install uses the reviewed lock, never a fresh resolution.
    npm = [json.loads(line) for line in Path(env["TEMPLATE_CALLS"]).open()]
    npm = [call[:2] for call in npm if call[0] == "npm"]
    assert npm == [["npm", "ci"]]
    assert (root / PINS[1]).read_bytes() == (ROOT / PINS[1]).read_bytes()
    assert (root / LAUNCHER).stat().st_mode & 0o111
    assert (root / SKILL).read_text() == "Fixture Graft skill\n"
    policy = (root / "CLAUDE.md").read_text()
    assert policy.startswith(generated_policy.decode())
    assert ".engineering/bin/graft" in policy.split(MARKER, 1)[1]
    ok("./engineering", "doctor")
    status = ok("./engineering", "deps", "status").stdout
    assert re.search(r"(?m)^graft .* OK$", status)
    # Locally modified guidance is reported rather than silently used.
    installed = (root / "CLAUDE.md").read_text()
    (root / "CLAUDE.md").write_text(installed.replace("Graft navigation", "Graft"))
    modified = call("./engineering", "doctor")
    assert modified.returncode == 1 and "graft: MODIFIED" in modified.stdout
    (root / "CLAUDE.md").write_text(installed)
    save(root, "graft/.graph/wiring.json", '{"nodes": []}\n')
    ok("git", "add", ".")
    ok("git", "commit", "-m", "Enable navigation")

    # Disabling leaves leftover content visible until an update removes it.
    select(root, "none")
    ok("git", "commit", "-am", "Disable navigation")
    leftover = call("./engineering", "doctor")
    assert leftover.returncode == 1
    assert "ERROR [navigation]" in leftover.stdout and "update" in leftover.stdout
    before = contents(root)
    # Updates come from a starter checkout.
    update = (sys.executable, str(ROOT / "engineering"), "update", str(root))
    preview = ok(*update)
    for name in (LAUNCHER, *PINS, SKILL, "CLAUDE.md"):
        assert re.search(rf"(?m)^\w+ {re.escape(name)}: .*navigation", preview.stdout)
    assert contents(root) == before
    ok(*update, "--apply")
    assert navigation_content(root) == []
    assert (root / "CLAUDE.md").read_bytes() == generated_policy
    assert (root / "graft/.graph/wiring.json").exists()
    assert 'application_roots = ["src"]' in (root / CONFIG).read_text()
    assert "navigation disabled" in ok("./engineering", "doctor").stdout
    status = ok("./engineering", "deps", "status").stdout
    assert re.search(r"(?m)^graft .* missing +NOT SELECTED", status)


def disabled_adoption(template, target, capsys):
    adopt(template, target)
    navigate(target, "graft", ["src"])
    record_installed(target, {"matt-skills", "graft"})
    commit(target)
    navigate(target, "none", ["src"])
    commit(target)


def test_disabling_refuses_customized_navigation_content(installation, capsys):
    template, target = installation
    disabled_adoption(template, target, capsys)
    policy = target / "CLAUDE.md"
    end = "<!-- engineering:navigation:end -->"
    policy.write_text(policy.read_text().replace(end, "Local note.\n" + end))
    commit(target)
    before = snapshot(target)
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 1
    assert re.search(r"(?m)^CONFLICT CLAUDE.md: .*navigation", output)
    assert snapshot(target) == before


def shipped_launcher(template, target, local=None):
    """Install the launcher as earlier releases did, as a whole-file managed scope."""
    from engineering.installation import STATE_PATH
    from engineering.ownership import digest, encoded, json_object

    adopt(template, target)
    navigate(target, "graft", ["src"])
    raw = (ROOT / LAUNCHER).read_bytes()
    save(target, LAUNCHER, (local or raw).decode())
    (target / LAUNCHER).chmod(0o755)
    state = json_object((target / STATE_PATH).read_bytes())
    state["entries"][LAUNCHER] = {
        "ownership": {"mode": "file"},
        "upstream": digest(raw),
    }
    (target / STATE_PATH).write_bytes(encoded(state))
    manifest_path = target / ".engineering/manifest.json"
    manifest = json_object(manifest_path.read_bytes())
    manifest["files"][LAUNCHER] = {
        "ownership": {"mode": "file"},
        "sha256": digest(raw),
        "owned_sha256": digest(raw),
        "previous": [],
        "executable": True,
    }
    manifest_path.write_bytes(encoded(manifest))
    commit(target)
    return raw


def test_update_keeps_installed_launcher_while_navigation_is_selected(
    installation, capsys
):
    from engineering.installation import STATE_PATH
    from engineering.ownership import json_object

    template, target = installation
    raw = shipped_launcher(template, target)
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 0, output
    assert re.search(rf"(?m)^PRESERVE {re.escape(LAUNCHER)}: .*graft", output)
    assert (target / LAUNCHER).read_bytes() == raw
    entries = json_object((target / STATE_PATH).read_bytes())["entries"]
    assert LAUNCHER not in entries


def test_update_reports_a_customized_launcher_during_handover(installation, capsys):
    template, target = installation
    local = b'#!/bin/sh\n# Local wrapper.\nexec ./engineering navigation "$@"\n'
    shipped_launcher(template, target, local)
    before = snapshot(target)
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 1
    assert re.search(rf"(?m)^CONFLICT {re.escape(LAUNCHER)}: .*customized", output)
    assert snapshot(target) == before


def test_disabled_navigation_command_refuses(installation):
    template, target = installation
    adopt(template, target)
    navigate(target, "none", ["src"])
    for args in (["map"], ["check"], ["build"], ["install-skill"]):
        result = run(
            sys.executable,
            str(ROOT / "engineering"),
            "--root",
            str(target),
            "navigation",
            *args,
        )
        assert result.returncode == 1
        assert "navigation disabled" in result.stderr
        assert "Traceback" not in result.stderr


@pytest.mark.parametrize("value", ["5", '"graft"', "[1]"])
def test_malformed_capability_section_is_a_configuration_error(installation, value):
    template, target = installation
    adopt(template, target)
    path = target / CONFIG
    text = re.sub(r"(?ms)^\[navigation\]\n.*?(?=^\[)", "", path.read_text())
    path.write_text(f"navigation = {value}\n" + text)
    result = doctor(target)
    assert result.returncode == 1
    assert "ERROR [configuration]" in result.stdout and "navigation" in result.stdout
    assert "Traceback" not in result.stdout + result.stderr


def test_capabilities_added_later_are_validated(installation, capsys, monkeypatch):
    from engineering import settings

    template, target = installation
    adopt(template, target)
    monkeypatch.setitem(settings.CAPABILITIES, "review", ("none", "tiered"))
    path = target / CONFIG
    path.write_text("review = 5\n" + path.read_text())
    status, output = engineering(capsys, target, "doctor")
    assert status == 1 and "ERROR [configuration]" in output and "review" in output
    path.write_text(
        path.read_text().replace("review = 5\n", "") + '[review]\nprovider = "x"\n'
    )
    status, output = engineering(capsys, target, "doctor")
    assert status == 1 and "review.provider" in output
    path.write_text(path.read_text().replace('provider = "x"', 'provider = "tiered"'))
    assert "ERROR [configuration]" not in engineering(capsys, target, "doctor")[1]


def test_verification_rejects_graft_check_while_navigation_is_disabled(tmp_path):
    from .integration.test_verification import change_plan, cli, git, record_role

    root = tmp_path
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Fixture")
    save(root, ".gitignore", ".engineering/state/verification/\n")
    save(root, "Makefile", "check:\n\t@true\n")
    save(root, "src/app.py", "VALUE = 1\n")
    save(
        root,
        CONFIG,
        'schema_version = 1\n[navigation]\nprovider = "none"\n'
        'application_roots = ["src"]\n',
    )
    record_role(root, "consumer")
    # Verification classifies ownership from the installation manifest (ticket 03).
    save(root, ".engineering/manifest.json", json.dumps({"files": {}}))
    git(root, "add", ".")
    git(root, "commit", "-m", "baseline")
    save(root, "src/app.py", "VALUE = 2\n")
    save(
        root,
        ".engineering/state/verification/plan.json",
        json.dumps(
            {
                "base": "main",
                "requirement": "Change the fixture value",
                "paths": ["src/app.py"],
                "checks": [["make", "check"], [".engineering/bin/graft", "check"]],
                "tools": [[sys.executable, "--version"]],
                "inputs": [],
                "tier": "ordinary",
                "tier_reason": "Fixture value has no security impact",
            }
        ),
    )
    arguments = ["prepare", "--change", "example", "--plan"]
    arguments.append(".engineering/state/verification/plan.json")
    result = cli(root, *arguments, status=1)
    assert "navigation disabled" in result["error"]
    change_plan(root, checks=[["make", "check"]])
    assert cli(root, *arguments)["status"] == "INCOMPLETE"


def test_navigation_content_from_an_earlier_release_is_reinstalled(installation):
    from engineering.ownership import digest

    template, target = installation
    adopt(template, target)
    navigate(target, "graft", ["src"])
    record_installed(target, {"matt-skills", "graft"})
    # The launcher recorded by an earlier release differs from today's content.
    older = '#!/bin/sh\nexec ./engineering navigation "$@"\n'
    save(target, LAUNCHER, older)
    path = target / ".engineering/state/dependencies.json"
    evidence = json.loads(path.read_text())
    evidence["dependencies"]["graft"]["outputs"][LAUNCHER] = digest(older.encode())
    path.write_text(json.dumps(evidence))
    status = run(
        sys.executable,
        str(ROOT / "engineering"),
        "--root",
        str(target),
        "deps",
        "status",
    )
    assert re.search(r"(?m)^graft .* OUTDATED$", status.stdout), status.stdout
    result = doctor(target)
    assert result.returncode == 1 and "graft: OUTDATED" in result.stdout


def test_disabling_composes_with_an_upstream_policy_change(installation, capsys):
    from .test_installation import refresh

    template, target = installation
    disabled_adoption(template, target, capsys)
    # One update both removes navigation guidance and changes the integration section.
    end = "<!-- engineering:integration:end -->"
    policy = template / "CLAUDE.md"
    policy.write_text(policy.read_text().replace(end, "New upstream rule.\n" + end, 1))
    refresh(template)
    status, output = engineering(capsys, template, "update", str(target), "--apply")
    assert status == 0, output
    text = (target / "CLAUDE.md").read_text()
    assert "New upstream rule." in text
    assert MARKER not in text
    assert "Healthy" in engineering(capsys, target, "doctor")[1]


def test_apply_refuses_two_content_actions_for_one_path(installation):
    from engineering.apply import Action, Plan, apply_plan

    template, target = installation
    plan = Plan(template, target, "update", None)
    plan.actions = [
        Action("CLAUDE.md", "MERGE", "first", b"one\n"),
        Action("CLAUDE.md", "MERGE", "second", b"two\n"),
    ]
    before = snapshot(target)
    with pytest.raises(ValueError, match="CLAUDE.md"):
        apply_plan(plan)
    assert snapshot(target) == before


def test_shipped_navigation_lock_is_the_reviewed_lock():
    from engineering import graft

    assert (ROOT / graft.PINNED_LOCK).read_bytes() == (ROOT / PINS[1]).read_bytes()
