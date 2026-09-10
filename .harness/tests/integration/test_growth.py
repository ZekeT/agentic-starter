"""Exercise code-line policy against real Git histories and configuration."""

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))
from factory.config import Config, initialize_manifest, load_config
from factory.growth import check_growth, classify
from factory.source import count_python

pytestmark = pytest.mark.integration


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    git(tmp_path, "config", "user.name", "Fixture")
    (tmp_path / "old.py").write_text("x = 1\n" * 900)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "baseline")
    return tmp_path


@pytest.mark.parametrize(
    "size,old,new,status",
    [
        (300, 0, True, "PASS"),
        (301, 0, True, "WARN"),
        (500, 0, True, "WARN"),
        (501, 0, True, "FAIL"),
        (749, 600, False, "WARN"),
        (750, 600, False, "FAIL"),
        (900, 900, False, "WARN"),
        (900, None, False, "WARN"),
    ],
)
def test_boundaries(size, old, new, status):
    assert classify(size, old, Config(), new=new) == status


def test_counting():
    assert count_python(b'"doc";\n').code == 0
    assert count_python(b'"doc"; x = 1\n').code == 1
    assert count_python(b'"""module\ndocs"""\n# comment\n\nx = 1 # inline\n').code == 1
    assert count_python(b'def f(): "doc"; return 1\n').code == 1
    assert count_python(b'x = """data\nmore data\nend"""\n').code == 3
    assert count_python('def café(): "doc"; return 1\n'.encode()).code == 1
    with pytest.raises(SyntaxError):
        count_python(b"def broken(\n")


def test_unrelated_and_untracked(repo):
    assert check_growth(repo, Config(), "main")[0] == []
    (repo / "new.py").write_text("x = 1\n" * 900)
    findings, _ = check_growth(repo, Config(), "main")
    assert len(findings) == 1 and findings[0].status == "FAIL"
    assert findings[0].growth == 900


def test_growth_staged_and_unstaged(repo):
    (repo / "old.py").write_text("x = 1\n" * 1049)
    git(repo, "add", "old.py")
    assert check_growth(repo, Config(), "main")[0][0].status == "WARN"
    (repo / "old.py").write_text("x = 1\n" * 1050)
    assert check_growth(repo, Config(), "main")[0][0].status == "FAIL"


def test_rename_preserves_baseline(repo):
    git(repo, "mv", "old.py", "renamed.py")
    result = check_growth(repo, Config(), "main")[0][0]
    assert result.previous == 900 and result.growth == 0 and result.status == "WARN"


def test_missing_base_and_size_only(repo):
    with pytest.raises(ValueError, match="merge base"):
        check_growth(repo, Config(), "missing")
    assert check_growth(repo, Config(), all_files=True)[0][0].status == "WARN"


def config_file(repo, values):
    (repo / ".harness").mkdir(exist_ok=True)
    (repo / ".harness/template-manifest.json").write_text(
        json.dumps({"schema_version": 1, "project": {"maintainability": values}})
    )


@pytest.mark.parametrize(
    "values",
    [
        {"max_file_lines": True},
        {"warn_file_lines": 500},
        {"substantial_growth_lines": 0},
        {"typo": 1},
        {"exceptions": [{"path": "missing.py", "reason": "generated"}]},
        {"exceptions": [{"path": "old.py", "reason": ""}]},
        {"exceptions": [{"path": "*.py", "reason": "all"}]},
        {
            "exceptions": [
                {"path": "old.py", "reason": "one"},
                {"path": "old.py", "reason": "two"},
            ]
        },
    ],
)
def test_bad_configuration(repo, values):
    config_file(repo, values)
    with pytest.raises(ValueError):
        load_config(repo)


def test_exception_and_overrides(repo):
    (repo / "generated.py").write_text("x = 1\n" * 1500)
    config_file(
        repo,
        {
            "warn_file_lines": 250,
            "exceptions": [{"path": "generated.py", "reason": "generated schema"}],
        },
    )
    config = load_config(repo)
    assert config.warn_file_lines == 250
    result = check_growth(repo, config, "main")[0][0]
    assert result.status == "EXEMPT" and result.reason == "generated schema"


def test_symlink_rejected(repo, tmp_path):
    (repo / "link.py").symlink_to(repo / "old.py")
    with pytest.raises(ValueError, match="Symlink"):
        check_growth(repo, Config(), "main")


def test_initialize_preserves_legacy_metadata_and_project(repo):
    config_file(repo, {"warn_file_lines": 200})
    path = repo / ".harness/template-manifest.json"
    data = json.loads(path.read_text())
    del data["schema_version"]
    data["files"] = {"legacy.py": {"sha256": "legacy"}}
    path.write_text(json.dumps(data))
    initialize_manifest(repo)
    assert load_config(repo).warn_file_lines == 200
    assert json.loads(path.read_text())["files"] == data["files"]


def test_manifest_regeneration_preserves_project():
    sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))
    from generate_template_manifest import build_manifest

    project = {"maintainability": {"warn_file_lines": 222}}
    result = build_manifest({"project": project})
    assert result["project"] == project
    assert result["defaults"]["maintainability"]["max_file_lines"] == 500


def test_cli_failure_and_disabled_policy(repo):
    launcher = Path(__file__).parents[3] / "factory"
    config_file(repo, {})
    (repo / "new.py").write_text("x = 1\n" * 501)
    command = [
        sys.executable,
        str(launcher),
        "--root",
        str(repo),
        "maintainability",
        "--base",
        "main",
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 1 and "new.py" in proc.stdout and "501" in proc.stdout
    config_file(repo, {"enabled": False})
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 0 and "disabled" in proc.stdout


def test_cli_verbose_reports_passing_file(repo):
    config_file(repo, {})
    (repo / "small.py").write_text("x = 1\n")
    launcher = Path(__file__).parents[3] / "factory"
    proc = subprocess.run(
        [
            sys.executable,
            str(launcher),
            "--root",
            str(repo),
            "maintainability",
            "--base",
            "main",
            "--verbose",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "PASS small.py: 0 → 1 code lines (growth 1)" in proc.stdout


def test_merge_base_not_moving_tip(repo):
    git(repo, "switch", "-c", "feature")
    (repo / "old.py").write_text("x = 1\n" * 1050)
    git(repo, "add", ".")
    git(repo, "commit", "-m", "grow")
    git(repo, "switch", "main")
    (repo / "old.py").write_text("x = 1\n" * 1049)
    git(repo, "add", ".")
    git(repo, "commit", "-m", "move main")
    git(repo, "switch", "feature")
    finding = check_growth(repo, Config(), "main")[0][0]
    assert (
        finding.previous == 900 and finding.growth == 150 and finding.status == "FAIL"
    )


@pytest.mark.parametrize(
    "entry",
    [
        "factory",
        ".harness/scripts/migrate_to_framework.py",
        ".claude/skills/setup-update/scripts/setup_update.py",
    ],
)
def test_unsupported_interpreter_leaves_target_untouched(tmp_path, monkeypatch, entry):
    root = Path(__file__).parents[3]
    sentinel = tmp_path / "project.txt"
    sentinel.write_bytes(b"preserve project\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [str(root / entry), str(tmp_path)])
    monkeypatch.setattr(sys, "version_info", (3, 11, 0))
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(root / entry), run_name="__main__")
    assert stopped.value.code != 0
    assert list(tmp_path.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"preserve project\n"
