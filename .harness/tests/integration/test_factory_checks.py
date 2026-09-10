"""Exercise quiet checks, read-only formatting gates and legacy group claims."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]
pytestmark = pytest.mark.integration


def run(
    args: list[str], cwd: Path, **kwargs: object
) -> subprocess.CompletedProcess[str]:
    """Run a fixture command without changing the real checkout."""
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, **kwargs)


def stub(path: Path, body: str) -> None:
    """Create a fixture executable."""
    path.write_text("#!/usr/bin/env bash\n" + body)
    path.chmod(0o755)


@pytest.mark.parametrize("status", [0, 7])
def test_quiet_output_and_status(tmp_path: Path, status: int) -> None:
    script = tmp_path / "command"
    stub(script, f"echo first\necho last >&2\nexit {status}\n")
    env = dict(os.environ, TMPDIR=str(tmp_path), VERBOSE="0")
    proc = run(
        [
            "bash",
            "-c",
            '. "$1"; run_quiet tests "$2"',
            "test",
            str(ROOT / ".harness/scripts/lib/run_quiet.sh"),
            str(script),
        ],
        tmp_path,
        env=env,
    )
    assert proc.returncode == status
    if status:
        assert "✗ tests" in proc.stderr
        assert "first" in proc.stderr and "last" in proc.stderr
    else:
        assert proc.stdout == "✓ tests\n" and not proc.stderr
    assert not list(tmp_path.glob("factory-check.*"))


def test_quiet_verbose_keeps_success_output(tmp_path: Path) -> None:
    proc = run(
        [
            "bash",
            "-c",
            '. "$1"; run_quiet lint printf detail',
            "test",
            str(ROOT / ".harness/scripts/lib/run_quiet.sh"),
        ],
        tmp_path,
        env=dict(os.environ, VERBOSE="1"),
    )
    assert proc.returncode == 0
    assert "✓ lint\ndetail" == proc.stdout


def check_fixture(tmp_path: Path) -> dict[str, str]:
    """Copy the public check entry point with a deterministic fake toolchain."""
    shutil.copytree(ROOT / ".harness/scripts", tmp_path / ".harness/scripts")
    shutil.copy2(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "tests").mkdir()
    (tmp_path / "src").mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub(
        bin_dir / "uv",
        """printf '%s\n' "$*" >> "$CHECK_CALLS"
case "$*" in
  *"factory maintainability"*) echo growth-detail; echo growth-stderr >&2; exit "${GROWTH_STATUS:-0}" ;;
  *--fix*|*"ruff format src"*) echo "mutating command" >&2; exit 97 ;;
  *pytest*) echo test-output; exit "${PYTEST_STATUS:-0}" ;;
  *ruff*) echo format-or-lint-output; exit "${RUFF_STATUS:-0}" ;;
esac
""",
    )
    return dict(
        os.environ,
        PATH=f"{bin_dir}:{os.environ['PATH']}",
        CHECK_CALLS=str(tmp_path / "calls"),
        VERBOSE="0",
    )


@pytest.mark.parametrize("status, expected", [(0, 0), (5, 0), (1, 2), (2, 2)])
def test_make_check_preserves_test_failures(
    tmp_path: Path, status: int, expected: int
) -> None:
    env = check_fixture(tmp_path)
    env["PYTEST_STATUS"] = str(status)
    proc = run(["make", "check"], tmp_path, env=env)
    assert proc.returncode == expected
    if expected:
        assert "✗ tests" in proc.stderr and "test-output" in proc.stderr
    else:
        assert proc.stdout.splitlines() == [
            "✓ format",
            "✓ lint",
            "✓ types",
            "✓ tests",
            "✓ maintainability",
            "✓ feature-docs",
        ]
    calls = (tmp_path / "calls").read_text()
    assert "--fix" not in calls and "ruff format --check" in calls


def test_format_failure_stops_before_tests_without_fixing(tmp_path: Path) -> None:
    env = check_fixture(tmp_path)
    env["RUFF_STATUS"] = "1"
    source = tmp_path / "src/example.py"
    source.write_text("x=  1\n")
    proc = run(["make", "check"], tmp_path, env=env)
    assert proc.returncode != 0 and "✗ format" in proc.stderr
    assert source.read_text() == "x=  1\n"
    assert "pytest" not in (tmp_path / "calls").read_text()


def test_growth_failure_retains_output_and_stops_gate(tmp_path: Path) -> None:
    env = check_fixture(tmp_path)
    env["GROWTH_STATUS"] = "8"
    proc = run(["make", "check"], tmp_path, env=env)
    assert proc.returncode != 0
    assert "✗ maintainability" in proc.stderr
    assert "growth-detail" in proc.stderr and "growth-stderr" in proc.stderr
    assert "✓ feature-docs" not in proc.stdout


def test_migrated_python311_project_uses_separate_factory_runtime(
    tmp_path: Path,
) -> None:
    python311 = shutil.which("python3.11")
    uv = shutil.which("uv")
    if not python311 or not uv:
        pytest.skip("Requires Python 3.11 and uv for the legacy environment fixture")
    env = check_fixture(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    original = (
        '[project]\nname="legacy"\nversion="0.1"\nrequires-python=">=3.11,<3.12"\n'
    )
    pyproject.write_text(original)
    run([python311, "-m", "venv", "--without-pip", ".venv"], tmp_path, check=True)
    config = tmp_path / ".venv/pyvenv.cfg"
    original_config = config.read_bytes()
    sys.path.insert(0, str(ROOT / ".harness/scripts"))
    from migrate_to_framework import copy_framework_files, patch_pyproject
    from factory.config import initialize_manifest

    copy_framework_files(tmp_path, ROOT, False, False)
    patch_pyproject(tmp_path, False)
    initialize_manifest(tmp_path)
    migrated_project = pyproject.read_bytes()
    assert pyproject.read_text().startswith(original)
    run(["git", "init", "-b", "main"], tmp_path, check=True)
    run(["git", "add", ".harness", "factory"], tmp_path, check=True)
    run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "baseline",
        ],
        tmp_path,
        check=True,
    )
    # Stub project checks, but execute the actual factory command through real uv.
    env.update(
        REAL_UV=uv,
        UV_CACHE_DIR=str(tmp_path / "uv-cache"),
        UV_PYTHON_DOWNLOADS="never",
        HARNESS_BASE_BRANCH="main",
        VIRTUAL_ENV=str(tmp_path / ".venv"),
    )
    stub(
        tmp_path / "bin/uv",
        """case "$*" in
  *"factory maintainability"*) exec "$REAL_UV" "$@" ;;
esac
""",
    )
    proc = run(["make", "check"], tmp_path, env=env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "✓ maintainability" in proc.stdout
    assert config.read_bytes() == original_config
    assert pyproject.read_bytes() == migrated_project
    assert not (tmp_path / "uv.lock").exists()


def test_feature_docs_gate_is_stateless_and_respects_source_root(
    tmp_path: Path,
) -> None:
    src = tmp_path / "custom source"
    feature = src / "accounts"
    feature.mkdir(parents=True)
    (feature / "__init__.py").touch()
    cmd = ["python3", str(ROOT / ".harness/scripts/check_feature_docs.py"), str(src)]
    assert run(cmd, tmp_path).returncode == 0
    (feature / "logic.py").write_text("x = 1\n")
    first = run(cmd, tmp_path)
    second = run(cmd, tmp_path)
    assert first.returncode == second.returncode == 1
    assert first.stderr == second.stderr and "accounts/CLAUDE.md" in first.stderr
    assert set(p.name for p in feature.iterdir()) == {"__init__.py", "logic.py"}
    (feature / "CLAUDE.md").write_text("Purpose: accounts.\n")
    assert run(cmd, tmp_path).returncode == 0


def claim_fixture(tmp_path: Path, deep: bool = False) -> dict[str, str]:
    """Prepare a local repo with legacy tasks and no external services."""
    shutil.copytree(ROOT / ".harness/scripts", tmp_path / ".harness/scripts")
    run(["git", "init", "-b", "main"], tmp_path, check=True)
    run(
        ["git", "config", "user.email", "fixture@example.invalid"], tmp_path, check=True
    )
    run(["git", "config", "user.name", "Fixture"], tmp_path, check=True)
    run(["git", "commit", "--allow-empty", "-m", "fixture"], tmp_path, check=True)
    change = tmp_path / "openspec/changes/example"
    change.mkdir(parents=True)
    (change / "tasks.md").write_text(
        "## 1. Flow\n- [ ] 1.1 Implement flow\n\n## 2. Other\n- [ ] 2.1 OTHER_GROUP_BODY\n"
    )
    (change / "proposal.md").write_text("UNRELATED_PROPOSAL_BODY")
    (change / "design.md").write_text("UNRELATED_DESIGN_BODY")
    if deep:
        (change / "intent.md").write_text("Workflow: DEEP\nReason: migration\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub(bin_dir / "openspec", "exit 0\n")
    stub(bin_dir / "gh", "exit 1\n")
    return dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}")


def test_legacy_group_claim_is_lazy_and_branch_is_mutex(tmp_path: Path) -> None:
    env = claim_fixture(tmp_path)
    args = ["bash", ".harness/scripts/cmd_dev_change.sh", "example", "1"]
    proc = run(args, tmp_path, env=env)
    assert proc.returncode == 0, proc.stderr
    assert "1.1 Implement flow" in proc.stdout
    for unwanted in (
        "OTHER_GROUP_BODY",
        "UNRELATED_PROPOSAL_BODY",
        "UNRELATED_DESIGN_BODY",
    ):
        assert unwanted not in proc.stdout
    assert (
        run(["git", "branch", "--show-current"], tmp_path).stdout.strip()
        == "feat/example-g1"
    )
    repeat = run(args, tmp_path, env=env)
    assert repeat.returncode != 0 and "already claimed" in repeat.stderr


def test_deep_claim_needs_program_design(tmp_path: Path) -> None:
    env = claim_fixture(tmp_path, deep=True)
    args = ["bash", ".harness/scripts/cmd_dev_change.sh", "example", "1"]
    proc = run(args, tmp_path, env=env)
    assert proc.returncode != 0 and "/shape-change example" in proc.stderr
    assert run(["git", "branch", "--show-current"], tmp_path).stdout.strip() == "main"
    (tmp_path / "openspec/changes/example/program-design.md").write_text(
        "# Accepted design\n"
    )
    assert run(args, tmp_path, env=env).returncode == 0


def test_shipping_gate_fails_with_complete_output(tmp_path: Path) -> None:
    env = claim_fixture(tmp_path)
    run(["git", "switch", "-c", "fix/example"], tmp_path, check=True)
    (tmp_path / "Makefile").write_text(
        "check:\n\t@seq 1 40\n\t@echo final-failure >&2\n\t@exit 9\n"
    )
    proc = run(["bash", ".harness/scripts/cmd_commit_push_pr.sh"], tmp_path, env=env)
    assert proc.returncode != 0
    assert "\n1\n2\n" in proc.stdout and "\n40\n" in proc.stdout
    assert "final-failure" in proc.stderr
