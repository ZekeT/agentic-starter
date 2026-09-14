"""Bound full doctor execution when shared installation inputs are special files."""

import os
import subprocess
import sys

import pytest

from . import test_doctor

ROOT = test_doctor.ROOT
installation = test_doctor.installation

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "name,category",
    [
        (".harness/template-manifest.json", "manifest"),
        (".harness/TEMPLATE_VERSION", "manifest"),
        (".claude/template-version.json", "manifest"),
        (".claude/settings.json", "hooks"),
        ("openspec/config.yaml", "openspec"),
        (".harness/graft/package.json", "navigation"),
        (".harness/evals/cases/001-fixture.yaml", "evals"),
    ],
)
@pytest.mark.parametrize("kind", ["fifo", "directory", "symlink"])
def test_cli_rejects_nonregular_inputs_without_hanging(
    installation, name, category, kind
):
    """All checks must finish after an earlier category rejects a shared input."""
    path = installation / name
    if path.exists():
        path.unlink()
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(installation / "missing-target")
    result = subprocess.run(
        [sys.executable, str(ROOT / "factory"), "--root", str(installation), "doctor"],
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert f"ERROR {category}" in result.stdout
    assert "Freshness not assessed" in result.stdout
    assert "Traceback" not in result.stderr
