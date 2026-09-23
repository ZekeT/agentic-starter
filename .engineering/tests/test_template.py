"""Exercise consumer distribution through its public build and setup commands."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .template_toolchain import toolchain

ROOT = Path(__file__).parents[2]
BUILD = ROOT / ".engineering/scripts/build_template.py"


def run(*args, cwd=ROOT, **kwargs):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, **kwargs)


def build(destination):
    result = run(sys.executable, str(BUILD), str(destination))
    assert result.returncode == 0, result.stdout + result.stderr
    return destination


def contents(root):
    return {
        p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
        for p in root.rglob("*")
        if p.is_file()
    }


def test_reproducible_consumer_payload(tmp_path):
    first = build(tmp_path / "first")
    second = build(tmp_path / "second")
    assert contents(first) == contents(second)
    files = contents(first)
    for name in (
        "README.md",
        "Makefile",
        "pyproject.toml",
        "uv.lock",
        ".engineering/manifest.json",
        ".engineering/engineering/migrate/openspec.py",
        ".claude/skills/migrate-from-openspec/SKILL.md",
        ".engineering/migrations/baselines/v2-manifest.json",
    ):
        assert name in files
    for prefix in (
        ".git/",
        ".scratch/",
        ".engineering/tests/",
        ".engineering/evals/",
        ".engineering/state/",
        ".engineering/template/",
        "docs/migrations/",
        "docs/context/",
        "node_modules/",
        ".agent/",
    ):
        assert not any(name.startswith(prefix) for name in files), prefix
    assert ".engineering/scripts/generate_template_manifest.py" not in files
    assert ".engineering/scripts/build_template.py" not in files
    assert "engineering-evals" not in (first / "Makefile").read_text()
    assert "your-repository-url" not in (first / "README.md").read_text()
    manifest = json.loads((first / ".engineering/manifest.json").read_text())
    assert set(manifest["files"]) <= files.keys()
    assert files["engineering"][1] & 0o111


def cli(root, *args):
    return run(sys.executable, str(root / "engineering"), *args, cwd=root)


def test_initialize_missing_state_and_preserve_customization(tmp_path):
    root = build(tmp_path / "project")
    state = root / ".engineering/state/install.json"
    result = cli(root, "init-installation")
    assert result.returncode == 0, result.stdout + result.stderr
    original = state.read_bytes()
    data = json.loads(original)
    assert data["entries"]["Makefile"]["ownership"]["mode"] == "section"
    (root / "REVIEW.md").write_text("Local review policy\n")
    result = cli(root, "init-installation")
    assert result.returncode == 0, result.stdout + result.stderr
    assert state.read_bytes() == original
    assert (root / "REVIEW.md").read_text() == "Local review policy\n"
    state.write_text('{"schema_version": 99}')
    result = cli(root, "init-installation")
    assert result.returncode != 0 and "schema" in result.stderr
    assert state.read_text() == '{"schema_version": 99}'


def test_modified_distribution_cannot_become_an_initial_baseline(tmp_path):
    root = build(tmp_path / "project")
    (root / "REVIEW.md").write_text("Unknown distribution\n")
    result = cli(root, "init-installation")
    assert result.returncode != 0 and "hash mismatch" in result.stderr
    assert not (root / ".engineering/state/install.json").exists()


def test_generated_project_setup_doctor_and_normal_gates(tmp_path):
    root = build(tmp_path / "project")
    env = toolchain(tmp_path / "tools")

    def command(*args):
        result = run(*args, cwd=root, env=env)
        assert result.returncode == 0, result.stdout + result.stderr
        return result

    command("git", "init", "-b", "main")
    command("git", "config", "user.name", "Template fixture")
    command("git", "config", "user.email", "fixture@example.invalid")
    command("make", "setup")
    state = (root / ".engineering/state/install.json").read_bytes()
    command("./engineering", "doctor")
    command("git", "add", ".")
    command("git", "commit", "-m", "Initialize application")
    command("make", "check")
    command("make", "engineering-check")
    command("make", "fmt")
    (root / "src").mkdir()
    (root / "src/__init__.py").touch()
    (root / "src/greeting.py").write_text(
        '"""Greet an application user."""\n\n\n'
        "def greet(name: str) -> str:\n"
        '    """Return a personalized greeting."""\n'
        '    return f"Hello, {name}!"\n'
    )
    (root / "tests/test_greeting.py").write_text(
        "from src.greeting import greet\n\n\n"
        'def test_greeting():\n    assert greet("Ada") == "Hello, Ada!"\n'
    )
    command("make", "check")
    command("make", "setup")
    assert (root / ".engineering/state/install.json").read_bytes() == state
    (root / ".scratch").mkdir()
    (root / ".scratch/ticket.md").write_text("Application work\n")
    assert run("git", "check-ignore", ".scratch/ticket.md", cwd=root).returncode == 1
    calls = [
        json.loads(line)
        for line in Path(env["TEMPLATE_CALLS"]).read_text().splitlines()
    ]
    assert any(call[:2] == ["npx", "--yes"] for call in calls)
    assert any(call[:2] == ["npm", "ci"] for call in calls)
    assert not any(
        "manifest" in arg or "engineering-evals" in arg
        for call in calls
        for arg in call
    )


def test_setup_refuses_invalid_baseline_before_network_install(tmp_path):
    root = build(tmp_path / "project")
    env = toolchain(tmp_path / "tools")
    state = root / ".engineering/state/install.json"
    state.parent.mkdir()
    state.write_text('{"schema_version": 99}')
    result = run("make", "setup", cwd=root, env=env)
    assert result.returncode != 0 and "schema" in result.stderr
    assert state.read_text() == '{"schema_version": 99}'
    calls = Path(env["TEMPLATE_CALLS"]).read_text()
    assert '"sync"' not in calls and '"npm"' not in calls and '"npx"' not in calls


def test_payload_migration_command_works_without_maintainer_checkout(tmp_path):
    root = build(tmp_path / "project")
    target = tmp_path / "brownfield"
    (target / "openspec/specs/accounts").mkdir(parents=True)
    (target / "openspec/config.yaml").write_text("schema: spec-driven\n")
    source = target / "openspec/specs/accounts/spec.md"
    source.write_text("# Accounts\nUsers can sign in.\n")
    for args in (
        ("init", "-b", "main"),
        ("config", "user.name", "Fixture"),
        ("config", "user.email", "fixture@example.invalid"),
        ("add", "."),
        ("commit", "-m", "Original project"),
    ):
        assert run("git", *args, cwd=target).returncode == 0
    result = cli(root, "migrate", "openspec-project", "--target", str(target), "--plan")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (target / ".engineering").exists()
    result = cli(
        root, "migrate", "openspec-project", "--target", str(target), "--apply"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (target / ".engineering/migration-work/openspec/inventory.json").is_file()
    assert source.read_text() == "# Accounts\nUsers can sign in.\n"


def test_inclusion_list_accounts_for_runtime_without_collecting_new_files():
    data = json.loads((ROOT / ".engineering/template/files.json").read_text())
    runtime = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / ".engineering/engineering").rglob("*.py")
    }
    assert set(data["managed"]) & runtime == runtime - {
        ".engineering/engineering/eval_config.py"
    }


@pytest.mark.parametrize("origin", ["../outside", "linked.md", "missing.md", ".env"])
def test_invalid_selected_source_refuses_before_creating_output(tmp_path, origin):
    source = tmp_path / "source"
    scripts = source / ".engineering/scripts"
    scripts.mkdir(parents=True)
    for name in ("build_template.py", "generate_template_manifest.py"):
        shutil.copy2(ROOT / ".engineering/scripts" / name, scripts / name)
    shutil.copytree(
        ROOT / ".engineering/engineering", source / ".engineering/engineering"
    )
    config = source / ".engineering/template/files.json"
    config.parent.mkdir()
    config.write_text(
        json.dumps(
            {"schema_version": 1, "managed": {"REVIEW.md": origin}, "application": {}}
        )
    )
    outside = tmp_path / "outside"
    outside.write_text("Do not change\n")
    (source / "linked.md").symlink_to(outside)
    destination = tmp_path / "output"
    result = run(sys.executable, str(scripts / "build_template.py"), str(destination))
    assert result.returncode != 0
    assert not destination.exists()
    assert outside.read_text() == "Do not change\n"


@pytest.mark.parametrize("kind", ["directory", "file", "symlink"])
def test_build_refuses_existing_destinations(tmp_path, kind):
    target = tmp_path / "output"
    original = tmp_path / "original"
    original.write_text("Preserve this\n")
    if kind == "directory":
        target.mkdir()
        (target / "local").write_text("Local project\n")
    elif kind == "file":
        target.write_text("Local file\n")
    else:
        target.symlink_to(original)
    before = contents(tmp_path)
    result = run(sys.executable, str(BUILD), str(target))
    assert result.returncode != 0
    assert contents(tmp_path) == before
