"""Keep installation diagnosis offline, read-only, and strict about protections."""

import json
from pathlib import Path

import pytest
from engineering.doctor import diagnose
from engineering.doctor_wiring import check_hooks
from engineering.eval_config import parse_fields

from .test_installation import adopt, installation
from .test_migration import save, snapshot

__all__ = ["installation"]


def errors(root):
    return {f.code for f in diagnose(root) if f.severity == "ERROR"}


def test_offline_readonly_does_not_execute_project_or_graft(installation, monkeypatch):
    template, target = installation
    adopt(template, target)
    save(target, "graft/.graph/wiring.json", "invalid graph bytes")
    save(
        target,
        ".claude/hooks/pre_tool_dangerous.py",
        "raise RuntimeError('must not execute')",
    )
    before = snapshot(target)
    import subprocess

    original = subprocess.run

    def bounded(command, *args, **kwargs):
        assert Path(command[0]).name in {"git", "node"}
        if Path(command[0]).name == "git":
            assert "check-ignore" in command
        else:
            assert command[1:] == ["--version"]
            assert set(kwargs["env"]) == {"PATH"}
        return original(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", bounded)
    assert errors(target) == {"dependency"}
    assert snapshot(target) == before


@pytest.mark.parametrize(
    "name,category",
    [
        ("REVIEW.md", "structure"),
        (".claude/agents/verifier.md", "structure"),
        (".engineering/state/install.json", "metadata"),
        (".engineering/config.toml", "configuration"),
        (".claude/hooks/pre_tool_env_guard.py", "hooks"),
    ],
)
def test_missing_parts_report_categories(installation, name, category):
    template, target = installation
    adopt(template, target)
    (target / name).unlink()
    assert category in errors(target)


@pytest.mark.parametrize(
    "mutation", ["disabled", "async", "matcher", "event", "literal-path"]
)
def test_inactive_protections_rejected(installation, mutation):
    template, target = installation
    adopt(template, target)
    path = target / ".claude/settings.json"
    data = json.loads(path.read_text())
    group = data["hooks"]["PreToolUse"][0]
    if mutation == "disabled":
        data["disableAllHooks"] = True
    elif mutation == "async":
        group["hooks"][0]["async"] = True
    elif mutation == "matcher":
        group["matcher"] = "Read"
    elif mutation == "event":
        data["hooks"]["Stop"] = data["hooks"].pop("PreToolUse")
    else:
        group["hooks"][0]["command"] = (
            "python3 '$CLAUDE_PROJECT_DIR/.claude/hooks/pre_tool_dangerous.py'"
        )
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        check_hooks(target)


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_special_inputs_refused_without_read(installation, kind):
    import os

    template, target = installation
    adopt(template, target)
    path = target / "REVIEW.md"
    path.unlink()
    if kind == "symlink":
        path.symlink_to(template / "REVIEW.md")
    else:
        os.mkfifo(path)
    assert "structure" in errors(target)


@pytest.mark.parametrize("schema", [0, 2, True, "1"])
def test_unsupported_dependency_schema_fails_cleanly(installation, schema):
    template, target = installation
    adopt(template, target)
    save(
        target,
        ".engineering/state/dependencies.json",
        json.dumps({"schema_version": schema, "dependencies": {}}),
    )
    assert "dependency" in errors(target)


@pytest.mark.parametrize("style", ["|", ">"])
def test_eval_parser_retains_supported_block_styles(style):
    data = parse_fields(
        f"id: fixture\nkind: static\nwhy: exercise parsing\nshell: {style}\n  echo fixture\n",
        "fixture",
    )
    assert "echo fixture" in data["shell"]


def test_eval_parser_refuses_duplicate_fields():
    with pytest.raises(ValueError):
        parse_fields("id: one\nid: two\nkind: static\nshell: echo hello\n", "fixture")


ENGINEERING = Path(__file__).parents[2] / "engineering"


def navigate(target, provider, roots):
    """Select a navigation provider and application roots in project policy."""
    import re

    path = target / ".engineering/config.toml"
    text = re.sub(
        r'(?m)^provider = "graft"$',
        f'provider = "{provider}"',
        path.read_text(),
        count=1,
    )
    text = re.sub(
        r"(?m)^application_roots = .*$",
        f"application_roots = {json.dumps(roots)}",
        text,
    )
    path.write_text(text)
    for name in roots:
        save(target, f"{name}/app.py", "VALUE = 1\n")


def record_installed(target, names, graft_version="0.18.0"):
    """Write installation evidence as if pinned dependencies had been installed."""
    from engineering.ownership import digest
    from engineering.registry import registry

    evidence = {}
    for row in registry(target)["dependency"]:
        if row["id"] not in names:
            continue
        version = row["version"] if row["kind"] == "skills" else graft_version
        if row["kind"] == "skills":
            outputs = [f".claude/skills/{skill}/SKILL.md" for skill in row["skills"]]
            for name in outputs:
                save(target, name, f"{version} fixture skill\n")
        else:
            outputs = [
                ".engineering/graft/package.json",
                ".engineering/graft/package-lock.json",
                ".claude/skills/graft/SKILL.md",
            ]
            save(target, outputs[-1], "graft fixture skill\n")
            save(
                target,
                ".engineering/graft/node_modules/@nanonets/graft/package.json",
                json.dumps({"version": version}),
            )
        evidence[row["id"]] = {
            "managed": True,
            "installed_version": version,
            "installed_from": row["source"],
            "outputs": {n: digest((target / n).read_bytes()) for n in outputs},
        }
    save(
        target,
        ".engineering/state/dependencies.json",
        json.dumps({"schema_version": 1, "dependencies": evidence}),
    )


def doctor(target):
    import subprocess
    import sys

    return subprocess.run(
        [sys.executable, str(ENGINEERING), "--root", str(target), "doctor"],
        capture_output=True,
        text=True,
    )


def findings(result, severity, code):
    return [
        line
        for line in result.stdout.splitlines()
        if line.startswith(f"{severity} [{code}]")
    ]


def test_disabled_navigation_passes_without_graft(installation):
    template, target = installation
    adopt(template, target)
    navigate(target, "none", ["src"])
    record_installed(target, {"matt-skills"})
    # Pins are not checked while navigation is disabled.
    save(target, ".engineering/graft/package.json", '{"dependencies":{}}\n')
    result = doctor(target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert findings(result, "INFO", "navigation")
    assert "disabled" in result.stdout
    assert "graft" not in {
        line.split("]")[1].split(":")[0].strip()
        for line in result.stdout.splitlines()
        if line.startswith(("ERROR", "WARN"))
    }


def test_ready_navigation_passes(installation):
    template, target = installation
    adopt(template, target)
    navigate(target, "graft", ["src"])
    record_installed(target, {"matt-skills", "graft"})
    result = doctor(target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not findings(result, "WARN", "navigation")
    assert not findings(result, "ERROR", "navigation")
    assert not findings(result, "ERROR", "dependency")


def test_enabled_navigation_without_roots_warns_without_failing(installation):
    template, target = installation
    adopt(template, target)
    navigate(target, "graft", [])
    record_installed(target, {"matt-skills", "graft"})
    result = doctor(target)
    assert result.returncode == 0, result.stdout + result.stderr
    [warning] = findings(result, "WARN", "navigation")
    next_step = result.stdout.split(warning, 1)[1]
    assert "application_roots" in next_step and '"none"' in next_step


@pytest.mark.parametrize("breakage", ["missing", "stale", "mispinned"])
def test_enabled_but_broken_navigation_fails_with_disable_option(
    installation, breakage
):
    template, target = installation
    adopt(template, target)
    navigate(target, "graft", ["src"])
    if breakage == "missing":
        record_installed(target, {"matt-skills"})
    elif breakage == "stale":
        record_installed(target, {"matt-skills", "graft"}, graft_version="0.17.0")
    else:
        record_installed(target, {"matt-skills", "graft"})
        save(
            target,
            ".engineering/graft/package.json",
            '{"dependencies":{"@nanonets/graft":"0.0.0"}}\n',
        )
    result = doctor(target)
    assert result.returncode == 1, result.stdout + result.stderr
    failures = [
        line
        for line in result.stdout.splitlines()
        if line.startswith(("ERROR [navigation]", "ERROR [dependency] graft"))
    ]
    assert failures
    lines = result.stdout.splitlines()
    fixes = [lines[lines.index(line) + 1] for line in failures]
    assert all('provider = "none"' in fix for fix in fixes)


@pytest.mark.parametrize("breakage", ["modified", "missing", "pin changed"])
def test_disabled_navigation_ignores_recorded_graft(installation, breakage):
    template, target = installation
    adopt(template, target)
    navigate(target, "none", ["src"])
    version = "0.17.0" if breakage == "pin changed" else "0.18.0"
    record_installed(target, {"matt-skills", "graft"}, graft_version=version)
    if breakage == "modified":
        save(target, ".claude/skills/graft/SKILL.md", "local edit\n")
    elif breakage == "missing":
        (
            target / ".engineering/graft/node_modules/@nanonets/graft/package.json"
        ).unlink()
    result = doctor(target)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not [
        line
        for line in result.stdout.splitlines()
        if line.startswith(("ERROR", "WARN")) and "graft" in line
    ]
    assert findings(result, "INFO", "navigation")


def test_invalid_provider_is_one_configuration_error(installation):
    template, target = installation
    adopt(template, target)
    navigate(target, "other", ["src"])
    record_installed(target, {"matt-skills", "graft"})
    result = doctor(target)
    assert result.returncode == 1
    errors = [line for line in result.stdout.splitlines() if line.startswith("ERROR")]
    assert len(errors) == 1 and errors[0].startswith("ERROR [configuration]")
    assert "navigation.provider" in errors[0]
    assert "deps install --apply" not in result.stdout
