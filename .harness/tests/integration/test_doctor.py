"""Exercise installation diagnosis against independent filesystem fixtures."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT / ".harness"))
from factory.doctor import diagnose, run  # noqa: E402
from factory.doctor_wiring import COMMANDS, HOOKS  # noqa: E402

pytestmark = pytest.mark.integration


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


@pytest.fixture
def installation(tmp_path):
    for name in (
        "openspec/specs",
        "openspec/changes",
        "docs/decisions",
        ".claude/agents",
    ):
        (tmp_path / name).mkdir(parents=True)
    for name in (
        "CLAUDE.md",
        "HARNESS.md",
        "FACTORY.md",
        "REVIEW.md",
        "Makefile",
        ".harness/factory/cli.py",
        ".harness/factory/doctor.py",
        ".harness/scripts/cmd_check.sh",
        ".harness/scripts/lib/run_quiet.sh",
        ".harness/evals/run_evals.py",
    ):
        write(tmp_path, name, "fixture content\n")
    write(tmp_path, "Makefile", "check:\n\t@exit 99\nevals:\n\t@exit 99\n")
    for name in ("factory", ".harness/bin/graft", ".claude/statusline.sh"):
        write(tmp_path, name, (ROOT / name).read_text()).chmod(0o755)
    write(tmp_path, ".gitignore", (ROOT / ".gitignore").read_text())
    write(
        tmp_path, ".claude/settings.json", (ROOT / ".claude/settings.json").read_text()
    )
    for name in HOOKS:
        write(tmp_path, f".claude/hooks/{name}", "raise RuntimeError('must not run')\n")
    for name in COMMANDS:
        script = f".harness/scripts/cmd_{name.replace('-', '_')}.sh"
        write(tmp_path, script, "exit 99\n")
        write(tmp_path, f".claude/commands/{name}.md", f"!`bash {script}`\n")
    write(tmp_path, "openspec/config.yaml", "schema: spec-driven\n")
    write(
        tmp_path,
        ".harness/evals/cases/001-fixture.yaml",
        "id: fixture\nkind: static\nwhy: fixture\nshell: |\n  exit 99\n",
    )
    write(
        tmp_path,
        ".harness/template-manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "template_version": "1.5.0",
                "defaults": {},
                "project": {},
                "files": {"factory": {"sha256": "a" * 64, "previous": []}},
            }
        ),
    )
    for name in ("package.json", "package-lock.json"):
        write(
            tmp_path,
            f".harness/graft/{name}",
            (ROOT / f".harness/graft/{name}").read_text(),
        )
    write(
        tmp_path,
        ".harness/graft/node_modules/@nanonets/graft/package.json",
        '{"version":"0.18.0"}',
    )
    write(
        tmp_path,
        ".harness/graft/node_modules/@nanonets/graft/dist/cli.js",
        "throw Error('must not run');",
    )
    write(
        tmp_path,
        ".claude/skills/graft/SKILL.md",
        "---\nname: graft\ndescription: Fixture\n---\n",
    )
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def errors(root):
    return {d.code: d for d in diagnose(root) if d.severity == "ERROR"}


def manifest(root, **values):
    path = root / ".harness/template-manifest.json"
    data = json.loads(path.read_text())
    data.update(values)
    path.write_text(json.dumps(data))


def snapshot(root):
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode)
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }


def test_healthy_installation_is_readonly_and_does_not_execute_project(
    installation, monkeypatch
):
    before = snapshot(installation)
    actual = subprocess.run
    calls = []

    def bounded(args, **kwargs):
        calls.append(args)
        assert Path(args[0]).name == "git" or args[1:] == ["--version"]
        return actual(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", bounded)
    assert run(installation) == 0
    assert snapshot(installation) == before
    assert len(calls) == 2


@pytest.mark.parametrize(
    "name,category",
    [
        (".claude/commands/review.md", "commands"),
        (".claude/hooks/pre_tool_env_guard.py", "hooks"),
        (".harness/scripts/cmd_review.sh", "commands"),
        ("openspec/specs", "structure"),
        (".harness/graft/node_modules/@nanonets/graft/package.json", "navigation"),
        (".claude/skills/graft/SKILL.md", "navigation"),
        (".harness/evals/cases/001-fixture.yaml", "evals"),
    ],
)
def test_missing_installation_parts(installation, name, category):
    path = installation / name
    path.rmdir() if path.is_dir() else path.unlink()
    finding = errors(installation)[category]
    assert finding.path and finding.remediation


@pytest.mark.parametrize(
    "values",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"template_version": "unknown"},
        {"files": []},
        {"files": {}},
        {"files": {"../outside": {}}},
        {"files": {".env": {}}},
        {"files": {"factory": {"sha256": "bad"}}},
        {"files": {"factory": {"sha256": "a" * 64, "previous": [4]}}},
        {"project": {"maintainability": {"enabled": "yes"}}},
        {
            "project": {
                "maintainability": {"exceptions": [{"path": "factory", "reason": ""}]}
            }
        },
        {
            "project": {
                "maintainability": {
                    "exceptions": [{"path": "absent", "reason": "generated"}]
                }
            }
        },
    ],
)
def test_invalid_metadata_and_config(installation, values):
    manifest(installation, **values)
    assert "manifest" in errors(installation)


@pytest.mark.parametrize(
    "name,content,category",
    [
        (".harness/template-manifest.json", "{bad", "manifest"),
        (".harness/TEMPLATE_VERSION", "1.4.0", "manifest"),
        (".claude/settings.json", "[]", "hooks"),
        ("openspec/config.yaml", "context: no schema\n", "openspec"),
        (".harness/graft/package.json", "{}", "navigation"),
        (
            ".harness/graft/node_modules/@nanonets/graft/package.json",
            '{"version":"0.19.0"}',
            "navigation",
        ),
        (".harness/bin/graft", "#!/bin/sh\nexit 0\n", "navigation"),
        (".gitignore", ".env\n", "git-protections"),
        (
            ".harness/evals/cases/001-fixture.yaml",
            "id: broken\nkind: unknown\n",
            "evals",
        ),
    ],
)
def test_broken_configuration(installation, name, content, category):
    write(installation, name, content)
    assert category in errors(installation)


@pytest.mark.parametrize(
    "mutation", ["disabled", "wrong-event", "wrong-matcher", "comment-only", "async"]
)
def test_inactive_protection_is_rejected(installation, mutation):
    path = installation / ".claude/settings.json"
    data = json.loads(path.read_text())
    if mutation == "disabled":
        data["disableAllHooks"] = True
    elif mutation == "wrong-event":
        data["hooks"]["PostToolUse"] = data["hooks"].pop("PreToolUse")
    elif mutation == "wrong-matcher":
        data["hooks"]["PreToolUse"][0]["matcher"] = "Read"
    elif mutation == "comment-only":
        data["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
            "# " + data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        )
    else:
        data["hooks"]["PreToolUse"][0]["hooks"][0]["async"] = True
    path.write_text(json.dumps(data))
    assert "hooks" in errors(installation)


@pytest.mark.parametrize(
    "name", ["factory", ".harness/bin/graft", ".claude/statusline.sh"]
)
def test_executable_bits(installation, name):
    (installation / name).chmod(0o644)
    assert errors(installation)


def test_customization_and_missing_baselines_are_accepted(installation):
    write(installation, "CLAUDE.md", "Project-specific instructions")
    write(installation, "generated.py", "data = 42\n")
    manifest(
        installation,
        project={
            "maintainability": {
                "max_file_lines": 700,
                "exceptions": [{"path": "generated.py", "reason": "Generated schema"}],
            }
        },
    )
    assert not errors(installation)


def test_graph_bytes_are_never_opened_or_refreshed(installation, monkeypatch):
    write(installation, "src/app.py", "value=1\n")
    manifest(installation, project={"navigation": {"application_roots": ["src"]}})
    write(installation, "graft/.graph/wiring.json", "stale or malformed cache")
    original = Path.open

    def guarded(path, *args, **kwargs):
        assert "graft/.graph" not in str(path)
        assert not path.name.startswith(".env")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    findings = diagnose(installation)
    assert not [f for f in findings if f.severity == "ERROR"]
    assert any(
        f.code == "navigation-freshness" and "not assessed" in f.explanation
        for f in findings
    )


def test_symlink_and_special_file_are_rejected_without_reading(installation):
    path = installation / ".claude/settings.json"
    path.unlink()
    path.symlink_to(installation / ".env")
    assert "hooks" in errors(installation)
    path.unlink()
    os.mkfifo(path)
    assert "hooks" in errors(installation)


def test_node_preloads_are_not_inherited(installation, monkeypatch):
    monkeypatch.setenv("NODE_OPTIONS", "--require=/does-not-exist")
    assert not errors(installation)


def test_old_and_missing_node(installation, monkeypatch):
    node = write(installation, "old-node", "#!/bin/sh\necho v22.11.0\n")
    node.chmod(0o755)
    monkeypatch.setattr(shutil, "which", lambda name: str(node))
    assert "navigation" in errors(installation)
    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert "navigation" in errors(installation)


def test_cli_root_and_exit_status(installation):
    args = [
        sys.executable,
        str(ROOT / "factory"),
        "--root",
        str(installation),
        "doctor",
    ]
    good = subprocess.run(args, cwd="/", capture_output=True, text=True)
    assert good.returncode == 0, good.stderr + good.stdout
    (installation / ".claude/hooks/pre_tool_dangerous.py").unlink()
    bad = subprocess.run(args, cwd="/", capture_output=True, text=True)
    assert bad.returncode == 1 and "hooks" in bad.stdout and "Restore" in bad.stdout
    invalid = subprocess.run([*args, "--unknown"], capture_output=True, text=True)
    assert invalid.returncode == 2


@pytest.mark.parametrize(
    "name, content, category",
    [
        ("Makefile", "all:\n\t@true\n", "commands"),
        (".claude/template-version.json", '{"template_version":"1.4.0"}', "manifest"),
        (
            ".harness/evals/cases/002-duplicate.yaml",
            "id: fixture\nkind: static\nwhy: duplicate\nshell: |\n  true\n",
            "evals",
        ),
        (
            ".harness/evals/cases/001-fixture.yaml",
            "id: fixture\nkind: static\nwhy: empty\nshell: |\n",
            "evals",
        ),
    ],
)
def test_additional_wiring_failures(installation, name, content, category):
    write(installation, name, content)
    assert category in errors(installation)


def test_missing_graph_is_deferred(installation):
    write(installation, "src/app.py", "value = 1\n")
    manifest(installation, project={"navigation": {"application_roots": ["src"]}})
    assert not errors(installation)


def test_git_ignores_negation_and_environment_isolation(installation, monkeypatch):
    monkeypatch.setenv("GIT_DIR", "/nonexistent")
    assert not errors(installation)
    path = installation / ".gitignore"
    path.write_text(path.read_text() + "\n!.env.local\n")
    assert "git-protections" in errors(installation)


def test_starter_is_an_ordinary_healthy_installation():
    assert not errors(ROOT)


@pytest.mark.parametrize(
    "schema",
    [
        "",
        " ",
        "# choose later",
        '""',
        "''",
        '"   "',
        "'   '",
        "null",
        "Null",
        "NULL",
        "~",
        "true",
        "false",
        "123",
        "[]",
        "{}",
        "|",
        ">",
        "*alias",
        "&anchor spec-driven",
        '"spec-driven',
        "spec-driven'",
        "spec-driven # comment\nschema: other",
    ],
)
def test_empty_or_unsupported_openspec_schema(installation, schema):
    write(installation, "openspec/config.yaml", f"schema: {schema}\ncontext: hello\n")
    finding = errors(installation)["openspec"]
    assert "schema" in finding.explanation and finding.remediation


@pytest.mark.parametrize(
    "schema",
    [
        "spec-driven",
        "custom_schema.v2",
        '"spec-driven"',
        "'spec-driven'",
        "spec-driven # comment",
        '"spec-driven" # comment',
        "'spec-driven' # comment",
    ],
)
def test_supported_openspec_schema_forms(installation, schema):
    write(
        installation,
        "openspec/config.yaml",
        f"schema: {schema}\ncontext: |\n  schema: ignored\n",
    )
    assert "openspec" not in errors(installation)


@pytest.mark.parametrize("tool", ["node", "git"])
def test_project_tool_shims_are_not_executed(installation, monkeypatch, tool):
    executable = write(installation, f"bin/{tool}", "#!/bin/sh\nexit 99\n")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{installation / 'bin'}:{os.environ['PATH']}")
    finding = errors(installation)[
        "navigation" if tool == "node" else "git-protections"
    ]
    assert "outside the inspected project" in finding.explanation


@pytest.mark.parametrize(
    "path,valid",
    [
        ('"$CLAUDE_PROJECT_DIR"/.claude/hooks/{name}', True),
        ('"$CLAUDE_PROJECT_DIR/.claude/hooks/{name}"', True),
        ("'$CLAUDE_PROJECT_DIR'/.claude/hooks/{name}", False),
        ("'$CLAUDE_PROJECT_DIR/.claude/hooks/{name}'", False),
        (r'"\$CLAUDE_PROJECT_DIR"/.claude/hooks/{name}', False),
    ],
)
def test_hook_path_expansion(installation, path, valid):
    settings = installation / ".claude/settings.json"
    data = json.loads(settings.read_text())
    for groups in data["hooks"].values():
        for group in groups:
            for hook in group["hooks"]:
                name = hook["command"].rsplit("/", 1)[1]
                hook["command"] = "python3 " + path.format(name=name)
    settings.write_text(json.dumps(data))
    assert ("hooks" not in errors(installation)) == valid


@pytest.mark.parametrize("kind,body", [("static", "shell"), ("prompt", "prompt")])
@pytest.mark.parametrize("style", ["|", ">"])
@pytest.mark.parametrize("content,valid", [("  true\n", True), ("", False)])
def test_eval_block_styles(installation, kind, body, style, content, valid):
    write(
        installation,
        ".harness/evals/cases/001-fixture.yaml",
        f"id: fixture\nkind: {kind}\nwhy: fixture\n{body}: {style}\n{content}",
    )
    assert ("evals" not in errors(installation)) == valid


@pytest.mark.parametrize("kind,body", [("static", "shell"), ("prompt", "prompt")])
@pytest.mark.parametrize("content,valid", [("true", True), ("", False), ("   ", False)])
def test_eval_inline_bodies(installation, kind, body, content, valid):
    write(
        installation,
        ".harness/evals/cases/001-fixture.yaml",
        f"id: fixture\nkind: {kind}\n{body}: {content}\nwhy: fixture\n",
    )
    assert ("evals" not in errors(installation)) == valid


@pytest.mark.parametrize("field", ["id", "kind", "why", "shell"])
@pytest.mark.parametrize("style", ["|", ">"])
@pytest.mark.parametrize("empty", [False, True])
def test_doctor_and_eval_runner_agree_on_block_fields(
    installation, field, style, empty
):
    import runpy

    values = {
        "id": "fixture",
        "kind": "static",
        "why": "guards behavior",
        "shell": "true",
    }
    values[field] = style + "\n" + ("  \n" if empty else "  " + values[field] + "\n")
    path = write(
        installation,
        ".harness/evals/cases/001-fixture.yaml",
        "\n".join(f"{key}: {value}" for key, value in values.items()),
    )
    parse_case = runpy.run_path(str(ROOT / ".harness/evals/run_evals.py"))["parse_case"]
    if empty:
        with pytest.raises(ValueError):
            parse_case(path)
    else:
        assert parse_case(path).id == "fixture"
    assert ("evals" in errors(installation)) == empty


@pytest.mark.parametrize("suffix", ["why: duplicate\n", "kind: prompt\n"])
def test_doctor_and_runner_reject_duplicate_fields(installation, suffix):
    import runpy

    path = installation / ".harness/evals/cases/001-fixture.yaml"
    path.write_text(path.read_text() + suffix)
    parse_case = runpy.run_path(str(ROOT / ".harness/evals/run_evals.py"))["parse_case"]
    with pytest.raises(ValueError, match="duplicate field"):
        parse_case(path)
    assert "evals" in errors(installation)


@pytest.mark.parametrize(
    "content,valid",
    [
        ("```bash\nbash {script} $ARGUMENTS\n```\n", True),
        ("```bash\nbash {script} # or: --base main\n```\n", True),
        ('```sh\nbash "{script}"\n```\n', True),
        ("!`bash {script}`\n", True),
        ("!`bash '{script}' $ARGUMENTS`\n", True),
        ("<!-- old preamble -->\n!`bash {script}`\n", True),
        ("Run {script} before review.\n", False),
        ("<!-- {script} -->\n", False),
        ("<!--\n```bash\nbash {script}\n```\n-->\n", False),
        ("<!-- !`bash {script}` -->\n", False),
        ("<!--\n!`bash {script}`\n", False),
        ("```bash\n# bash {script}\n```\n", False),
        ("```bash\necho {script}\n```\n", False),
        ("```text\nbash {script}\n```\n", False),
        ("```text\n!`bash {script}`\n```\n", False),
        ("`bash {script}`\n", False),
        ("```bash\nbash {script}.disabled\n```\n", False),
        ("```bash\nfalse && bash {script}\n```\n", False),
        ("```bash\nbash {script} || true\n```\n", False),
        ("```bash\ncat <<'EOF'\nbash {script}\nEOF\n```\n", False),
    ],
)
def test_command_preamble_forms(installation, content, valid):
    script = ".harness/scripts/cmd_review.sh"
    write(installation, ".claude/commands/review.md", content.format(script=script))
    findings = errors(installation)
    assert ("commands" not in findings) == valid
    if not valid:
        assert script in findings["commands"].explanation
