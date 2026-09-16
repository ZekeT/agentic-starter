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
