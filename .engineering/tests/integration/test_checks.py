"""Exercise quiet checks, read-only formatting gates and feature documentation."""

from __future__ import annotations

import os
import shutil
import subprocess
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
            str(ROOT / ".engineering/scripts/lib/run_quiet.sh"),
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
    assert not list(tmp_path.glob("engineering-check.*"))


def test_quiet_verbose_keeps_success_output(tmp_path: Path) -> None:
    proc = run(
        [
            "bash",
            "-c",
            '. "$1"; run_quiet lint printf detail',
            "test",
            str(ROOT / ".engineering/scripts/lib/run_quiet.sh"),
        ],
        tmp_path,
        env=dict(os.environ, VERBOSE="1"),
    )
    assert proc.returncode == 0
    assert "✓ lint\ndetail" == proc.stdout


def check_fixture(tmp_path: Path) -> dict[str, str]:
    """Copy the public check entry point with a deterministic fake toolchain."""
    shutil.copytree(ROOT / ".engineering/scripts", tmp_path / ".engineering/scripts")
    shutil.copy2(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "tests").mkdir()
    (tmp_path / "src").mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub(
        bin_dir / "uv",
        """printf '%s\n' "$*" >> "$CHECK_CALLS"
case "$*" in
  *"engineering doctor"*) echo doctor-detail; echo doctor-stderr >&2; exit "${DOCTOR_STATUS:-0}" ;;
  *"engineering maintainability"*) echo growth-detail; echo growth-stderr >&2; exit "${GROWTH_STATUS:-0}" ;;
  *--fix*|*"ruff format src"*) echo "mutating command" >&2; exit 97 ;;
  *pytest*) echo test-output; exit "${PYTEST_STATUS:-0}" ;;
  *ruff*) echo format-or-lint-output; exit "${RUFF_STATUS:-0}" ;;
esac
""",
    )
    stub(tmp_path / "engineering", 'exec uv "engineering $*"')
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
            "✓ doctor",
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


def test_feature_docs_gate_is_stateless_and_respects_source_root(
    tmp_path: Path,
) -> None:
    src = tmp_path / "custom source"
    feature = src / "accounts"
    feature.mkdir(parents=True)
    (feature / "__init__.py").touch()
    cmd = [
        "python3",
        str(ROOT / ".engineering/scripts/check_feature_docs.py"),
        str(src),
    ]
    assert run(cmd, tmp_path).returncode == 0
    (feature / "logic.py").write_text("x = 1\n")
    first = run(cmd, tmp_path)
    second = run(cmd, tmp_path)
    assert first.returncode == second.returncode == 1
    assert first.stderr == second.stderr and "accounts/CLAUDE.md" in first.stderr
    assert set(p.name for p in feature.iterdir()) == {"__init__.py", "logic.py"}
    (feature / "CLAUDE.md").write_text("Purpose: accounts.\n")
    assert run(cmd, tmp_path).returncode == 0


def test_doctor_failure_stops_gate_with_complete_output(tmp_path: Path) -> None:
    env = check_fixture(tmp_path)
    env["DOCTOR_STATUS"] = "1"
    proc = run(["make", "check"], tmp_path, env=env)
    assert proc.returncode != 0
    assert "✗ doctor" in proc.stderr
    assert "doctor-detail" in proc.stderr and "doctor-stderr" in proc.stderr
    assert "engineering maintainability" not in (tmp_path / "calls").read_text()
