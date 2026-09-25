"""Exercise documented existing-project onboarding through public commands."""

import subprocess
import sys
from pathlib import Path

import pytest

from ..template_toolchain import toolchain
from ..test_legacy import legacy
from ..test_migration import commit, git, save, snapshot

ROOT = Path(__file__).parents[3]
pytestmark = pytest.mark.integration


@pytest.mark.parametrize("route", ["adopt", "legacy-starter"])
def test_existing_project_onboarding_preserves_native_work_and_openspec(
    tmp_path, route
):
    target = tmp_path / "project"
    target.mkdir()
    git(target, "init", "-b", "main")
    git(target, "config", "user.name", "Onboarding fixture")
    git(target, "config", "user.email", "fixture@example.invalid")
    save(target, "README.md", "Existing application\n")
    commit(target)
    if route == "legacy-starter":
        legacy(target)
    native = f"check:\n\t{sys.executable} -m unittest discover -s tests -v\n"
    # Customize outside the recognized legacy region so native checks survive.
    save(
        target,
        "Makefile",
        native
        + (
            "# factory:integration:begin\nfactory-check:\n\t@echo old-check\n"
            "# factory:integration:end\n"
            if route == "legacy-starter"
            else ""
        ),
    )
    save(target, "package.json", '{"name":"existing-app","private":true}\n')
    save(target, ".gitlab-ci.yml", "test:\n  script: make check\n")
    save(
        target,
        "tests/test_native.py",
        "import unittest\n\n\nclass Native(unittest.TestCase):\n    def test_total(self):\n        self.assertEqual(sum([2, 3]), 5)\n",
    )
    save(
        target,
        "openspec/specs/accounts/spec.md",
        "# Accounts\nKeep source for review.\n",
    )
    save(target, ".claude/commands/opsx/propose.md", "Existing OpenSpec command\n")
    commit(target)
    before = snapshot(target)
    env = toolchain(tmp_path / "tools")

    def run(*args, cwd=target):
        return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)

    def ok(*args, cwd=target):
        result = run(*args, cwd=cwd)
        assert result.returncode == 0, result.stdout + result.stderr
        return result

    operation = (
        ["adopt", str(target)]
        if route == "adopt"
        else ["migrate", "legacy-starter", "--target", str(target)]
    )
    command = [sys.executable, str(ROOT / "engineering"), *operation]
    preview = ok(*command)
    assert snapshot(target) == before
    assert "OpenSpec" in preview.stdout or "openspec" in preview.stdout
    ok(*command, "--apply")
    for name, content in before.items():
        if name.startswith(
            ("openspec/", "tests/", ".claude/commands/opsx/")
        ) or name in {"package.json", ".gitlab-ci.yml", "README.md"}:
            assert (target / name).read_bytes() == content
    assert (target / "Makefile").read_text().startswith(native)
    assert not (target / "pyproject.toml").exists()
    ok("./engineering", "deps", "install", "--apply")
    ok("./engineering", "doctor")
    commit(target)
    assert "Ran 1 test" in ok("make", "check").stderr
    ok("make", "engineering-check")
    if route == "legacy-starter":
        stable = snapshot(target)
        ok(*command, "--apply")
        assert snapshot(target) == stable
    # Native gate remains meaningful after onboarding, rather than echo-only.
    save(
        target, "tests/test_native.py", "raise RuntimeError('native gate still runs')\n"
    )
    failed = run("make", "check")
    assert failed.returncode != 0 and "native gate still runs" in failed.stderr
