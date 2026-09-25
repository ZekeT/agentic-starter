"""Assemble the consumer journey; scripted attestations are not model review."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from ..template_toolchain import toolchain
from ..test_template import build
from .test_publication import STATE
from .test_publication import hosting as hosting
from .test_verification import git

pytestmark = pytest.mark.integration


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = build(tmp_path / "application")
    for key, value in toolchain(tmp_path / "tools").items():
        monkeypatch.setenv(key, value)
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Journey fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    command(root, "make", "setup")
    git(root, "add", ".")
    git(root, "commit", "-m", "Initialize application")
    git(root, "switch", "-c", "feature")
    (root / STATE).mkdir(parents=True)
    return root


def command(root, *args, status=0):
    result = subprocess.run(args, cwd=root, capture_output=True, text=True)
    assert result.returncode == status, result.stdout + result.stderr
    return result.stdout


def engineering(root, family, operation, *args, status=0):
    return json.loads(
        command(
            root,
            "./engineering",
            family,
            operation,
            "--change",
            "journey",
            *args,
            status=status,
        )
    )


def prepare(root):
    return engineering(root, "verify", "prepare", "--plan", f"{STATE}/plan.json")


def scripted_verification(root):
    """Test record consumption only; the live trial supplies actual reviewers."""
    prepared = prepare(root)
    token = prepared["snapshot"]
    engineering(root, "verify", "check", "--snapshot", token)
    for role in ("maintainability", "behavioral"):
        report = {
            "snapshot": token,
            "role": role,
            "reviewer": f"scripted-journey-{role}-fixture",
            "independent": True,
            "verdict": "PASS",
            "summary": "Authored test attestation, not actual independent review.",
            "findings": [],
            "coverage_gaps": ["No model judgment or live hosting exercised."],
        }
        (root / STATE / "report.json").write_text(json.dumps(report))
        engineering(root, "verify", "record", "--report", f"{STATE}/report.json")
    return prepared


def test_generated_application_correction_and_failed_push_reuse(repo, hosting):
    manifest = (repo / ".engineering/manifest.json").read_bytes()
    baseline = (repo / ".engineering/state/install.json").read_bytes()
    for name in (
        ".engineering/engineering/migrate",
        ".claude/skills/migrate-from-openspec",
        ".engineering/migrations",
    ):
        assert not (repo / name).exists()
    source = repo / "src"
    source.mkdir()
    (source / "__init__.py").touch()
    app = source / "greeting.py"
    app.write_text(
        '"""Print a named greeting."""\n\nimport sys\n\n'
        'print(f"Hello, {sys.argv[1]}!")\n'
    )
    test = repo / "tests/test_greeting.py"
    test.write_text(
        "import subprocess\nimport sys\n\n\n"
        "def test_greeting():\n"
        '    result = subprocess.run([sys.executable, "-m", "src.greeting", "Ada"],\n'
        "                            capture_output=True, text=True, check=True)\n"
        '    assert result.stdout == "Hello, Ada!\\n"\n'
    )
    # Count the actual gate in the isolated checkout, without replacing its recipe.
    makefile = repo / "Makefile"
    makefile.write_text(
        makefile.read_text().replace(
            "check:\n", f"check:\n\t@echo check >> {STATE}/check-calls\n"
        )
    )
    command(repo, "make", "fmt")
    git(repo, "add", "src", "tests/test_greeting.py", "Makefile")
    git(repo, "commit", "-m", "Implement greeting")
    implementation = git(repo, "rev-parse", "HEAD")
    tracked = set(git(repo, "ls-files").splitlines())
    dependencies = json.loads(
        (repo / ".engineering/state/dependencies.json").read_text()
    )
    inputs = {
        name
        for dep in dependencies["dependencies"].values()
        for name in dep["outputs"]
        if name not in tracked
    }
    inputs.update(
        (
            ".engineering/state/install.json",
            ".engineering/graft/node_modules/@nanonets/graft/package.json",
        )
    )
    plan = {
        "base": "main",
        "requirement": "Greeting command; later scripted correction trims whitespace.",
        "paths": [
            "src/__init__.py",
            "src/greeting.py",
            "tests/test_greeting.py",
            "Makefile",
        ],
        "checks": [["make", "check"]],
        "tools": [[sys.executable, "--version"]],
        "inputs": sorted(inputs - tracked),
        "security_required": False,
        "security_reason": "Disposable greeting and local fake hosting fixture.",
    }
    (repo / STATE / "plan.json").write_text(json.dumps(plan))
    readme = repo / "README.md"
    original_readme = readme.read_bytes()
    readme.write_bytes(original_readme + b"\nOwner staged work\n")
    git(repo, "add", "README.md")
    staged = git(repo, "diff", "--cached", "--binary")
    readme.write_bytes(readme.read_bytes() + b"Owner working work\n")
    working = readme.read_bytes()
    first = prepare(repo)
    assert first["status"] == "INCOMPLETE"
    assert (repo / first["checkout"] / "README.md").read_bytes() == original_readme
    scripted_verification(repo)
    assert command(repo, sys.executable, "-m", "src.greeting", "Ada") == "Hello, Ada!\n"

    # Scripted counterpart of a human-directed fix; no human approval is claimed.
    app.write_text(app.read_text().replace("sys.argv[1]", "sys.argv[1].strip()"))
    test.write_text(test.read_text().replace('"Ada"', '"  Ada  "'))
    command(repo, "make", "fmt")
    assert engineering(repo, "verify", "status", status=1)["status"] == "STALE"
    fixed = scripted_verification(repo)
    assert fixed["snapshot"] != first["snapshot"]
    previous = json.loads((repo / fixed["previous_evidence"]).read_text())
    assert previous["snapshot"] == first["snapshot"]
    assert (
        command(repo, sys.executable, "-m", "src.greeting", "  Ada  ")
        == "Hello, Ada!\n"
    )
    assert git(repo, "rev-parse", "HEAD") == implementation
    acceptance = {
        "snapshot": fixed["snapshot"],
        "summary": "Scripted fixture presentation for corrected greeting.",
        "blockers": [],
        "branch": "feature",
        "remote": "origin",
        "remote_url": str(hosting[0]),
        "base": "main",
        "provider": hosting[1],
        "title": "feat: greet a trimmed name",
    }
    (repo / STATE / "acceptance.json").write_text(json.dumps(acceptance))
    engineering(repo, "publish", "review", "--plan", f"{STATE}/acceptance.json")
    evidence = (repo / STATE / "journey.json").read_bytes()
    hook = hosting[0] / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    failed = engineering(repo, "publish", "run", "--authorize", "pr", status=1)
    assert failed["completed"] == ["preflight", "commit"]
    assert failed["failed"] == "push"
    accepted_head = git(repo, "rev-parse", "HEAD")
    assert git(repo, "rev-parse", "HEAD^") == implementation
    # Restore only the deliberately failing fixture hook in the disposable remote.
    hook.unlink()
    receipt = repo / STATE / "created.json"
    created_at = None
    for _ in range(2):
        result = engineering(repo, "publish", "run")
        assert result["status"] == "PUBLISHED"
        assert result["url"] == "https://hosting.invalid/project/pulls/1"
        if created_at is None:
            created_at = receipt.stat().st_mtime_ns
        else:
            assert receipt.stat().st_mtime_ns == created_at
    assert git(repo, "rev-parse", "HEAD") == accepted_head
    assert git(hosting[0], "rev-parse", "feature") == accepted_head
    assert (repo / STATE / "journey.json").read_bytes() == evidence
    for prepared in (first, fixed):
        calls = repo / prepared["checkout"] / STATE / "check-calls"
        assert calls.read_text() == "check\n"
    assert git(repo, "diff", "--cached", "--binary") == staged
    assert readme.read_bytes() == working
    assert (
        git(hosting[0], "show", "feature:README.md") == original_readme.decode().strip()
    )
    assert (repo / ".engineering/manifest.json").read_bytes() == manifest
    assert (repo / ".engineering/state/install.json").read_bytes() == baseline
