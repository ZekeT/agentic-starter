"""Exercise the pinned release against application and agent-configuration fixtures."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".harness"))
from factory.graft import (
    application_roots,
    environment,
    install_skill,
    runtime,
    skill_text,
)

pytestmark = pytest.mark.integration


def configure(root, roots):
    (root / ".harness/template-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "project": {"navigation": {"application_roots": roots}},
            }
        )
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    assert (
        ROOT / ".harness/graft/node_modules/@nanonets/graft/package.json"
    ).exists(), "Run make graft-install before the pinned-release integration suite"
    for key in list(os.environ):
        if any(word in key for word in ("API_KEY", "TOKEN", "SECRET")):
            monkeypatch.delenv(key)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for name in ("src", "harness", ".harness/graft", ".claude"):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    (tmp_path / "src/service.py").write_text(
        "def normalize_user_id(value):\n    return value.strip()\n\n"
        "def handle(value):\n    return normalize_user_id(value)\n"
    )
    for name in ("harness/visible.py", ".harness/hidden.py"):
        (tmp_path / name).write_text("def tooling_only():\n    return 1\n")
    (tmp_path / ".harness/graft/package.json").write_bytes(
        (ROOT / ".harness/graft/package.json").read_bytes()
    )
    (tmp_path / ".harness/graft/node_modules").symlink_to(
        ROOT / ".harness/graft/node_modules", target_is_directory=True
    )
    (tmp_path / ".gitignore").write_text(
        "/graft/\n/.graft/\n/.harness/graft/node_modules/\n/.claude/skills/graft/\n"
    )
    (tmp_path / "CLAUDE.md").write_text("Keep project instructions.\n")
    (tmp_path / "AGENTS.md").write_text("Keep other agent instructions.\n")
    (tmp_path / ".claude/settings.json").write_text(
        '{"statusLine":{"type":"command","command":"existing"},'
        '"hooks":{"Stop":[{"hooks":[{"type":"command","command":"existing"}]}]}}\n'
    )
    configure(tmp_path, ["src"])
    return tmp_path


def invoke(repo, *args):
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "factory"),
            "--root",
            str(repo),
            "navigation",
            *args,
        ],
        capture_output=True,
        text=True,
    )


def snapshot(repo):
    return {
        p.relative_to(repo).as_posix(): p.read_bytes()
        for p in repo.rglob("*")
        if p.is_file() and not {".git", "node_modules"}.intersection(p.parts)
    }


def test_skill_preview_install_and_preservation(repo):
    before = snapshot(repo)
    assert install_skill(repo, apply=False) == 0
    assert snapshot(repo) == before
    assert install_skill(repo, apply=True) == 0
    after = snapshot(repo)
    assert set(after) - set(before) == {".claude/skills/graft/SKILL.md"}
    assert all(after[k] == value for k, value in before.items())
    node, package = runtime(repo)
    assert after[".claude/skills/graft/SKILL.md"].decode() == skill_text(node, package)
    assert install_skill(repo, apply=True) == 0
    assert snapshot(repo) == after
    (repo / ".claude/skills/graft/SKILL.md").write_text("customized")
    before = snapshot(repo)
    with pytest.raises(ValueError, match="Customized"):
        install_skill(repo, apply=True)
    assert snapshot(repo) == before


def test_structural_scope_retrieval_and_non_mutation(repo):
    result = invoke(repo, "build")
    assert result.returncode == 0, result.stderr
    wiring = (repo / "graft/.graph/wiring.json").read_text()
    assert "src/service.py" in wiring and "normalize_user_id" in wiring
    assert "tooling_only" not in wiring and "harness/" not in wiring
    before = snapshot(repo)
    for args, expected in [
        (("check",), "OK"),
        (("ask", "normalize_user_id", "--source"), "src/service.py"),
        (("callers", "normalize_user_id"), "handle"),
        (("skeleton", "src/service.py"), "normalize_user_id"),
        (("grep", "normalize_user_id"), "src/service.py"),
        (("map",), "service.py"),
    ]:
        result = invoke(repo, *args)
        assert result.returncode == 0, result.stderr
        assert expected in result.stdout
        assert snapshot(repo) == before
    ignored = subprocess.run(
        ["git", "-C", str(repo), "check-ignore", "graft/.graph/wiring.json"],
        capture_output=True,
    )
    assert ignored.returncode == 0


def test_install_appends_ignores_without_replacing_project_rules(repo):
    ignore = repo / ".gitignore"
    ignore.write_text("# project rules\nkeep-out/")
    before = snapshot(repo)
    install_skill(repo, apply=False)
    assert snapshot(repo) == before
    install_skill(repo, apply=True)
    assert ignore.read_text().startswith("# project rules\nkeep-out/\n")
    assert "/graft/\n" in ignore.read_text()
    assert "/.claude/skills/graft/\n" in ignore.read_text()


def test_missing_and_stale_graph(repo):
    result = invoke(repo, "check")
    assert result.returncode == 1 and "missing" in result.stderr
    assert invoke(repo, "build").returncode == 0
    source = repo / "src/service.py"
    old_stat = source.stat()
    source.write_text(source.read_text().replace("strip", "upper"))
    os.utime(source, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
    before = snapshot(repo)
    result = invoke(repo, "check")
    assert result.returncode != 0
    assert snapshot(repo) == before


def test_multiple_extractor_fingerprints_preserve_read_only_navigation(repo):
    assert invoke(repo, "build").returncode == 0
    fingerprint = next((repo / "graft/.cache").glob("fingerprint.*.json"))
    older = fingerprint.with_name("fingerprint.previous-release.json")
    older.write_bytes(fingerprint.read_bytes())
    assert invoke(repo, "build").returncode == 0
    assert older.exists()
    before = snapshot(repo)
    for args in (("check",), ("ask", "normalize_user_id", "--source")):
        result = invoke(repo, *args)
        assert result.returncode == 0, result.stderr
        assert snapshot(repo) == before


def test_application_scope_change_requires_explicit_build(repo):
    assert invoke(repo, "build").returncode == 0
    (repo / "app").mkdir()
    (repo / "app/main.py").write_text("def application_entry():\n    return 1\n")
    configure(repo, ["app"])
    # Upstream checks the last-built scope; preparation owns manifest changes.
    before = snapshot(repo)
    assert invoke(repo, "check").returncode == 0
    assert snapshot(repo) == before
    assert invoke(repo, "build").returncode == 0
    assert invoke(repo, "check").returncode == 0
    graph = (repo / "graft/.graph/wiring.json").read_text()
    assert "app/main.py" in graph
    assert "src/service.py" not in graph


def test_empty_scope_and_dependency_diagnostics(repo):
    configure(repo, [])
    before = snapshot(repo)
    for command in ("build", "check"):
        result = invoke(repo, command)
        assert result.returncode == 0
        assert "not applicable: no application sources configured" in result.stdout
    assert snapshot(repo) == before
    package = repo / ".harness/graft/package.json"
    package.write_text('{"dependencies":{"@nanonets/graft":"0.0.0"}}')
    result = invoke(repo, "check")
    assert result.returncode == 1 and "0.0.0 required" in result.stderr
    (repo / ".harness/graft/node_modules").unlink()
    result = invoke(repo, "check")
    assert result.returncode == 1 and "make graft-install" in result.stderr


def test_enrichment_drift_does_not_block_structural_gate(repo):
    assert invoke(repo, "build").returncode == 0
    wiring = repo / "graft/.graph/wiring.json"
    graph = json.loads(wiring.read_text())
    # Seed the output of optional enrichment without making model calls.
    for node in graph["nodes"]:
        node.update(summary="Prior fixture summary", summary_state="ready")
    wiring.write_text(json.dumps(graph))
    source = repo / "src/service.py"
    source.write_text(source.read_text().replace("strip", "upper"))
    before = snapshot(repo)
    result = invoke(repo, "check")
    assert result.returncode == 1 and "changed:" in result.stdout
    assert snapshot(repo) == before
    assert invoke(repo, "build").returncode == 0
    before = snapshot(repo)
    result = invoke(repo, "check")
    assert result.returncode == 0, result.stderr
    assert "OK (structural)" in result.stdout
    assert "stale summaries (non-blocking)" in result.stdout
    assert snapshot(repo) == before
    assert any(n.get("summary") for n in json.loads(wiring.read_text())["nodes"])


@pytest.mark.parametrize("change", ["added", "removed"])
def test_structural_file_drift_still_fails(repo, change):
    assert invoke(repo, "build").returncode == 0
    if change == "added":
        (repo / "src/new.py").write_text("def new_function():\n    return 1\n")
    else:
        (repo / "src/service.py").unlink()
    before = snapshot(repo)
    result = invoke(repo, "check")
    assert result.returncode == 1 and f"{change}:" in result.stdout
    assert snapshot(repo) == before


def test_stale_optional_deep_content_is_non_blocking(repo):
    assert invoke(repo, "build").returncode == 0
    (repo / "graft/manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "files": [{"path": "src/service.py", "hash": "old"}],
                "nodes": [],
            }
        )
    )
    before = snapshot(repo)
    result = invoke(repo, "check")
    assert result.returncode == 0, result.stderr
    assert "Optional deep content is stale (non-blocking)" in result.stdout
    assert snapshot(repo) == before


def test_upstream_check_execution_failure_is_not_accepted(repo):
    assert invoke(repo, "build").returncode == 0
    (repo / "graft/.graph/wiring.json").write_text('{"nodes": null}')
    before = snapshot(repo)
    result = invoke(repo, "check")
    assert result.returncode != 0
    assert snapshot(repo) == before


@pytest.mark.parametrize(
    "roots", [["."], [".harness"], ["harness"], ["../outside"], ["missing"], "src"]
)
def test_invalid_scope(repo, roots):
    configure(repo, roots)
    with pytest.raises(ValueError):
        application_roots(repo)


@pytest.mark.parametrize(
    "args",
    [
        ("map", "/tmp"),
        ("ask", "question", "/tmp"),
        ("build", "--only-dir", "harness"),
        ("blast", "--name"),
        ("init",),
        ("upgrade",),
    ],
)
def test_scope_and_mutation_bypasses_rejected(repo, args):
    before = snapshot(repo)
    assert invoke(repo, *args).returncode != 0
    assert snapshot(repo) == before


def test_runtime_minimum_and_environment_override(repo, monkeypatch):
    fake_bin = repo / "bin"
    fake_bin.mkdir()
    node = fake_bin / "node"
    node.write_text("#!/bin/sh\nprintf 'v20.19.0\\n'\n")
    node.chmod(0o755)
    with monkeypatch.context() as patch:
        patch.setenv("PATH", str(fake_bin))
        result = invoke(repo, "check")
        assert result.returncode == 1 and "Node.js 22.12+" in result.stderr
        node.unlink()
        result = invoke(repo, "check")
        assert result.returncode == 1 and "Node.js 22.12+" in result.stderr
    assert invoke(repo, "build").returncode == 0
    monkeypatch.setenv("GRAFT_DIR", str(repo / "other-graph"))
    monkeypatch.setenv("GRAFT_NO_REFRESH", "0")
    before = snapshot(repo)
    assert invoke(repo, "check").returncode == 0
    assert snapshot(repo) == before


def test_deep_provider_settings_are_explicit_only(monkeypatch):
    monkeypatch.setenv("GRAFT_API_KEY", "fixture-placeholder")
    monkeypatch.setenv("GRAFT_MODEL", "fixture-model")
    monkeypatch.setenv("GRAFT_DIR", "/outside")
    monkeypatch.setenv("DOTENV_KEY", "fixture-placeholder")
    assert "GRAFT_API_KEY" not in environment()
    assert environment(deep=True)["GRAFT_API_KEY"] == "fixture-placeholder"
    assert environment(deep=True)["GRAFT_MODEL"] == "fixture-model"
    assert "GRAFT_DIR" not in environment(deep=True)
    assert "DOTENV_KEY" not in environment(deep=True)


def test_dotenv_argument_override_rejected_before_upstream(repo):
    before = snapshot(repo)
    result = invoke(repo, "ask", "dotenv_config_path=/tmp/fixture-config")
    assert result.returncode == 1
    assert "dotenv CLI overrides are disabled" in result.stderr
    assert snapshot(repo) == before


@pytest.mark.parametrize("directory", ["harness", "factory", "vendored/harness"])
def test_nested_tooling_requires_narrower_roots(repo, directory):
    tooling = repo / "src" / directory
    tooling.mkdir(parents=True)
    (tooling / "tool.py").write_text("def nested_tooling_only():\n    return 1\n")
    before = snapshot(repo)
    result = invoke(repo, "build")
    assert result.returncode == 1
    assert "select narrower" in result.stderr
    assert snapshot(repo) == before
    app = repo / "src/application"
    app.mkdir()
    (app / "main.py").write_text("def application_only():\n    return 1\n")
    configure(repo, ["src/application"])
    assert invoke(repo, "build").returncode == 0
    graph = (repo / "graft/.graph/wiring.json").read_text()
    assert "application_only" in graph
    assert "nested_tooling_only" not in graph
