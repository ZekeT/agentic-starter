"""Tests for scripts/migrate_to_framework.py."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

# Add scripts/ to path so we can import without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import migrate_to_framework as m  # noqa: E402

# ── fixtures ──────────────────────────────────────────────────────────────────


def make_empty_project(tmp_path: Path) -> Path:
    """Create a bare project directory with no files."""
    return tmp_path


def make_python_project(tmp_path: Path) -> Path:
    """Create a minimal Python project with pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\nrequires-python = ">=3.11"\n'
    )
    return tmp_path


def make_python_project_with_tools(tmp_path: Path) -> Path:
    """Create a Python project that already has [tool.black]."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test"\n\n[tool.black]\nline-length = 100\n'
    )
    return tmp_path


def make_js_project(tmp_path: Path) -> Path:
    """Create a minimal JS project."""
    (tmp_path / "package.json").write_text('{"name": "test"}')
    return tmp_path


def make_git_project(tmp_path: Path) -> Path:
    """Create a project with a .git directory."""
    (tmp_path / ".git").mkdir()
    return tmp_path


STARTER = m.STARTER_DIR


# ── validation tests ──────────────────────────────────────────────────────────


def test_validate_target_nonexistent(tmp_path: Path) -> None:
    """Non-existent path should raise SystemExit."""
    with pytest.raises(SystemExit):
        m.validate_target(tmp_path / "does-not-exist")


def test_validate_target_file(tmp_path: Path) -> None:
    """A file path (not directory) should raise SystemExit."""
    f = tmp_path / "file.txt"
    f.touch()
    with pytest.raises(SystemExit):
        m.validate_target(f)


def test_validate_target_valid(tmp_path: Path) -> None:
    """A valid directory should not raise."""
    m.validate_target(tmp_path)  # no exception


def test_is_inside_starter_true() -> None:
    """Starter itself should be detected as inside starter."""
    assert m.is_inside_starter(STARTER, STARTER) is True


def test_is_inside_starter_subdir() -> None:
    """Subdirectory of starter should be detected as inside starter."""
    assert m.is_inside_starter(STARTER / "scripts", STARTER) is True


def test_is_inside_starter_false(tmp_path: Path) -> None:
    """An unrelated path should not be detected as inside starter."""
    assert m.is_inside_starter(tmp_path, STARTER) is False


# ── audit tests ───────────────────────────────────────────────────────────────


def test_detect_git_repo_true(tmp_path: Path) -> None:
    """Should return True when .git exists."""
    (tmp_path / ".git").mkdir()
    assert m.detect_git_repo(tmp_path) is True


def test_detect_git_repo_false(tmp_path: Path) -> None:
    """Should return False when .git is absent."""
    assert m.detect_git_repo(tmp_path) is False


def test_detect_tech_stacks_python(tmp_path: Path) -> None:
    """pyproject.toml should trigger python detection."""
    (tmp_path / "pyproject.toml").write_text("")
    assert m.detect_tech_stacks(tmp_path) == ["python"]


def test_detect_tech_stacks_javascript(tmp_path: Path) -> None:
    """package.json should trigger javascript detection."""
    (tmp_path / "package.json").write_text("{}")
    assert m.detect_tech_stacks(tmp_path) == ["javascript"]


def test_detect_tech_stacks_multi(tmp_path: Path) -> None:
    """Both files present should return both stacks."""
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "package.json").write_text("{}")
    stacks = m.detect_tech_stacks(tmp_path)
    assert "python" in stacks
    assert "javascript" in stacks


def test_detect_tech_stacks_empty(tmp_path: Path) -> None:
    """Empty project should return empty list."""
    assert m.detect_tech_stacks(tmp_path) == []


def test_audit_target_empty(tmp_path: Path) -> None:
    """Audit of empty project should list all files and dirs as missing."""
    audit = m.audit_target(tmp_path, STARTER)
    assert audit.is_git_repo is False
    assert audit.tech_stacks == []
    assert audit.has_claude_setup is False
    assert len(audit.files_to_copy) == len(m.FILES_TO_COPY)
    assert audit.files_to_skip == []
    assert len(audit.missing_dirs) == len(m.DIRS_TO_CREATE)
    assert set(audit.skill_dirs_to_copy) == set(m.SKILL_DIRS_TO_COPY)
    assert audit.skill_dirs_to_skip == []


def test_audit_target_existing_skill_dir(tmp_path: Path) -> None:
    """A skill directory already present should appear in skill_dirs_to_skip."""
    dst = tmp_path / ".claude" / "skills" / "graphify"
    dst.mkdir(parents=True)
    audit = m.audit_target(tmp_path, STARTER)
    assert "graphify" in audit.skill_dirs_to_skip
    assert "graphify" not in audit.skill_dirs_to_copy


def test_audit_target_existing_file(tmp_path: Path) -> None:
    """A file already present should appear in files_to_skip."""
    dst = tmp_path / ".claude" / "settings.json"
    dst.parent.mkdir(parents=True)
    dst.write_text("{}")
    audit = m.audit_target(tmp_path, STARTER)
    assert ".claude/settings.json" in audit.files_to_skip
    assert ".claude/settings.json" not in audit.files_to_copy


# ── directory creation ────────────────────────────────────────────────────────


def test_create_missing_dirs_dry(tmp_path: Path) -> None:
    """Dry run should return dirs without creating them."""
    audit = m.audit_target(tmp_path, STARTER)
    created = m.create_missing_dirs(tmp_path, audit, dry=True)
    assert len(created) == len(m.DIRS_TO_CREATE)
    assert not (tmp_path / "stories" / "draft").exists()


def test_create_missing_dirs_creates(tmp_path: Path) -> None:
    """Real run should create all missing directories."""
    audit = m.audit_target(tmp_path, STARTER)
    m.create_missing_dirs(tmp_path, audit, dry=False)
    for d in m.DIRS_TO_CREATE:
        assert (tmp_path / d).is_dir(), f"Missing: {d}"


def test_create_missing_dirs_gitkeep(tmp_path: Path) -> None:
    """Kanban leaf directories should receive .gitkeep files."""
    audit = m.audit_target(tmp_path, STARTER)
    m.create_missing_dirs(tmp_path, audit, dry=False)
    for d in m._GITKEEP_DIRS:
        assert (tmp_path / d / ".gitkeep").exists(), f"Missing .gitkeep in {d}"


def test_create_missing_dirs_idempotent(tmp_path: Path) -> None:
    """Running twice should not raise and should return empty list second time."""
    audit = m.audit_target(tmp_path, STARTER)
    m.create_missing_dirs(tmp_path, audit, dry=False)
    audit2 = m.audit_target(tmp_path, STARTER)
    created2 = m.create_missing_dirs(tmp_path, audit2, dry=False)
    assert created2 == []


# ── file copying ──────────────────────────────────────────────────────────────


def test_copy_framework_files_copies_all(tmp_path: Path) -> None:
    """All FILES_TO_COPY should be present after a real copy."""
    copied, skipped = m.copy_framework_files(tmp_path, STARTER, force=False, dry=False)
    assert skipped == []
    for dst_rel in m.FILES_TO_COPY.values():
        assert (tmp_path / dst_rel).exists(), f"Missing: {dst_rel}"


def test_copy_framework_files_dry(tmp_path: Path) -> None:
    """Dry run should not create any files."""
    copied, _ = m.copy_framework_files(tmp_path, STARTER, force=False, dry=True)
    assert len(copied) == len(m.FILES_TO_COPY)
    assert not (tmp_path / ".claude").exists()


def test_copy_framework_files_skip_existing(tmp_path: Path) -> None:
    """Existing files should be skipped without --force."""
    dst = tmp_path / ".claude" / "settings.json"
    dst.parent.mkdir(parents=True)
    dst.write_text('{"original": true}')
    _, skipped = m.copy_framework_files(tmp_path, STARTER, force=False, dry=False)
    assert ".claude/settings.json" in skipped
    assert json.loads(dst.read_text()).get("original") is True


def test_copy_framework_files_force_overwrites(tmp_path: Path) -> None:
    """--force should overwrite existing files."""
    dst = tmp_path / ".claude" / "settings.json"
    dst.parent.mkdir(parents=True)
    dst.write_text('{"original": true}')
    copied, skipped = m.copy_framework_files(tmp_path, STARTER, force=True, dry=False)
    assert ".claude/settings.json" in copied
    assert ".claude/settings.json" not in skipped
    assert "original" not in dst.read_text()


# ── skill directory copying ─────────────────────────────────────────────────


def test_copy_skill_dirs_copies_all(tmp_path: Path) -> None:
    """All SKILL_DIRS_TO_COPY should exist under .claude/skills/ after copy."""
    copied, skipped = m.copy_skill_dirs(tmp_path, STARTER, force=False, dry=False)
    assert skipped == []
    assert set(copied) == set(m.SKILL_DIRS_TO_COPY)
    for name in m.SKILL_DIRS_TO_COPY:
        skill_dir = tmp_path / ".claude" / "skills" / name / "SKILL.md"
        assert skill_dir.exists(), f"Missing: {skill_dir}"


def test_copy_skill_dirs_dry_run_writes_nothing(tmp_path: Path) -> None:
    """Dry run should not create any skill directories."""
    copied, _ = m.copy_skill_dirs(tmp_path, STARTER, force=False, dry=True)
    assert set(copied) == set(m.SKILL_DIRS_TO_COPY)
    assert not (tmp_path / ".claude" / "skills").exists()


def test_copy_skill_dirs_skip_existing(tmp_path: Path) -> None:
    """An existing skill directory should be skipped without --force."""
    dst = tmp_path / ".claude" / "skills" / "graphify"
    dst.mkdir(parents=True)
    (dst / "SKILL.md").write_text("custom content")
    _, skipped = m.copy_skill_dirs(tmp_path, STARTER, force=False, dry=False)
    assert "graphify" in skipped
    assert (dst / "SKILL.md").read_text() == "custom content"


def test_copy_skill_dirs_force_overwrites(tmp_path: Path) -> None:
    """--force should overwrite an existing skill directory."""
    dst = tmp_path / ".claude" / "skills" / "graphify"
    dst.mkdir(parents=True)
    (dst / "SKILL.md").write_text("custom content")
    copied, skipped = m.copy_skill_dirs(tmp_path, STARTER, force=True, dry=False)
    assert "graphify" in copied
    assert "graphify" not in skipped
    assert (dst / "SKILL.md").read_text() != "custom content"


def test_copy_skill_dirs_excludes_junk_files(tmp_path: Path) -> None:
    """Copied skill dirs should never contain __pycache__ or .DS_Store."""
    m.copy_skill_dirs(tmp_path, STARTER, force=False, dry=False)
    skills_dir = tmp_path / ".claude" / "skills"
    junk = [
        p
        for p in skills_dir.rglob("*")
        if p.name == "__pycache__" or p.name == ".DS_Store"
    ]
    assert junk == []


def test_hooks_are_executable(tmp_path: Path) -> None:
    """Python hook files should have the executable bit set after copying."""
    m.copy_framework_files(tmp_path, STARTER, force=False, dry=False)
    for src_rel, dst_rel in m.FILES_TO_COPY.items():
        if dst_rel.endswith(".py") and "hooks" in dst_rel:
            mode = (tmp_path / dst_rel).stat().st_mode
            assert mode & 0o111, f"Not executable: {dst_rel}"


# ── pyproject.toml merging ────────────────────────────────────────────────────


def test_read_pyproject_tool_keys_detects_sections(tmp_path: Path) -> None:
    """Should detect existing [tool.*] keys."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'x'\n\n[tool.black]\nline-length = 88\n"
    )
    keys = m.read_pyproject_tool_keys(tmp_path / "pyproject.toml")
    assert "tool.black" in keys
    assert "tool.mypy" not in keys


def test_build_missing_toml_text_omits_existing(tmp_path: Path) -> None:
    """Should not include sections already present."""
    existing = {"tool.black", "tool.isort"}
    text = m.build_missing_toml_text(existing)
    assert "[tool.black]" not in text
    assert "[tool.mypy]" in text


def test_build_missing_toml_text_all_missing() -> None:
    """Should include all sections when nothing is present."""
    text = m.build_missing_toml_text(set())
    assert "[tool.black]" in text
    assert "[tool.isort]" in text
    assert "[tool.mypy]" in text
    assert "[tool.interrogate]" in text
    assert "[tool.pytest.ini_options]" in text


def test_patch_pyproject_appends_missing_sections(tmp_path: Path) -> None:
    """Missing tool sections should be appended to pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    sections, _ = m.patch_pyproject(tmp_path, dry=False)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "[tool.black]" in content
    assert "[tool.mypy]" in content
    assert len(sections) > 0


def test_patch_pyproject_skips_existing_sections(tmp_path: Path) -> None:
    """Sections already present should not be duplicated."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'x'\n\n[tool.black]\nline-length = 100\n"
    )
    _, _ = m.patch_pyproject(tmp_path, dry=False)
    content = (tmp_path / "pyproject.toml").read_text()
    assert content.count("[tool.black]") == 1


def test_patch_pyproject_creates_if_missing(tmp_path: Path) -> None:
    """Should create pyproject.toml from starter template if absent."""
    sections, _ = m.patch_pyproject(tmp_path, dry=False)
    assert (tmp_path / "pyproject.toml").exists()


def test_patch_pyproject_reports_missing_deps(tmp_path: Path) -> None:
    """Should report deps not in [project.optional-dependencies].dev."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'x'\n\n"
        "[project.optional-dependencies]\ndev = ['pytest>=8.0.0']\n"
    )
    _, missing = m.patch_pyproject(tmp_path, dry=False)
    assert any("black" in dep for dep in missing)
    # pytest itself is present; pytest-cov is not — assert pytest>= not in missing
    assert not any(dep.startswith("pytest>=") for dep in missing)


# ── Makefile merging ──────────────────────────────────────────────────────────


def test_makefile_has_marker_true(tmp_path: Path) -> None:
    """Should return True when marker is in the Makefile."""
    mf = tmp_path / "Makefile"
    mf.write_text(f"all:\n\techo hi\n\n{m.MAKEFILE_MARKER}\n")
    assert m.makefile_has_marker(mf) is True


def test_makefile_has_marker_false(tmp_path: Path) -> None:
    """Should return False when marker is absent."""
    mf = tmp_path / "Makefile"
    mf.write_text("all:\n\techo hi\n")
    assert m.makefile_has_marker(mf) is False


def test_get_existing_makefile_targets(tmp_path: Path) -> None:
    """Should detect target names in the Makefile."""
    mf = tmp_path / "Makefile"
    mf.write_text("check:\n\trun-tests\n\nbuild:\n\tcompile\n")
    targets = m.get_existing_makefile_targets(mf)
    assert "check" in targets
    assert "build" in targets


def test_patch_makefile_appends_missing(tmp_path: Path) -> None:
    """Missing targets should be appended under the marker."""
    mf = tmp_path / "Makefile"
    mf.write_text("all:\n\techo hi\n")
    m.patch_makefile(tmp_path, dry=False)
    content = mf.read_text()
    assert m.MAKEFILE_MARKER in content
    assert "configure:" in content


def test_patch_makefile_idempotent(tmp_path: Path) -> None:
    """Running patch_makefile twice should not add the marker twice."""
    mf = tmp_path / "Makefile"
    mf.write_text("all:\n\techo hi\n")
    m.patch_makefile(tmp_path, dry=False)
    m.patch_makefile(tmp_path, dry=False)
    content = mf.read_text()
    assert content.count(m.MAKEFILE_MARKER) == 1


def test_patch_makefile_skips_existing_targets(tmp_path: Path) -> None:
    """Targets already in the Makefile should not be duplicated."""
    mf = tmp_path / "Makefile"
    mf.write_text("check:\n\tmy-check\n")
    m.patch_makefile(tmp_path, dry=False)
    content = mf.read_text()
    assert content.count("check:") == 1


def test_patch_makefile_creates_if_missing(tmp_path: Path) -> None:
    """Should copy starter Makefile if none exists in target."""
    m.patch_makefile(tmp_path, dry=False)
    assert (tmp_path / "Makefile").exists()


# ── CLAUDE.md generation ──────────────────────────────────────────────────────


def test_generate_claude_md_contains_todo(tmp_path: Path) -> None:
    """Generated CLAUDE.md should contain TODO markers."""
    content = m.generate_claude_md_content("My Project", [])
    assert "TODO" in content


def test_generate_claude_md_python_includes_block(tmp_path: Path) -> None:
    """Python stack should add Python-specific coding block."""
    content = m.generate_claude_md_content("My Project", ["python"])
    assert "mypy" in content or "black" in content


def test_generate_claude_md_no_unresolved_format_keys(tmp_path: Path) -> None:
    """Template should not contain unresolved {placeholder} after formatting."""
    content = m.generate_claude_md_content("Test", ["python", "javascript"])
    # Find unresolved single-brace format keys (not double-brace escapes)
    unresolved = re.findall(r"(?<!\{)\{(?!\{)([^}]+)\}(?!\})", content)
    assert unresolved == [], f"Unresolved format keys: {unresolved}"


def test_create_claude_md_creates_file(tmp_path: Path) -> None:
    """Should create CLAUDE.md when it does not exist."""
    result = m.create_claude_md(tmp_path, [], dry=False)
    assert result is True
    assert (tmp_path / "CLAUDE.md").exists()


def test_create_claude_md_skips_existing(tmp_path: Path) -> None:
    """Should not overwrite existing CLAUDE.md."""
    (tmp_path / "CLAUDE.md").write_text("# My Custom Brain\n")
    result = m.create_claude_md(tmp_path, [], dry=False)
    assert result is False
    assert (tmp_path / "CLAUDE.md").read_text() == "# My Custom Brain\n"


def test_create_claude_md_not_overwritten_by_force(tmp_path: Path) -> None:
    """CLAUDE.md must never be overwritten even indirectly via copy_framework_files."""
    (tmp_path / "CLAUDE.md").write_text("# Custom\n")
    # copy_framework_files does not include CLAUDE.md — verify it is absent
    assert "CLAUDE.md" not in m.FILES_TO_COPY.values()


# ── .env.template ─────────────────────────────────────────────────────────────


def test_create_env_template_creates(tmp_path: Path) -> None:
    """Should copy .env.template from starter when absent."""
    result = m.create_env_template(tmp_path, STARTER, dry=False)
    assert result is True
    assert (tmp_path / ".env.template").exists()


def test_create_env_template_skips_existing(tmp_path: Path) -> None:
    """Should skip when .env.template already exists."""
    (tmp_path / ".env.template").write_text("CUSTOM=1\n")
    result = m.create_env_template(tmp_path, STARTER, dry=False)
    assert result is False
    assert (tmp_path / ".env.template").read_text() == "CUSTOM=1\n"


# ── migration report ──────────────────────────────────────────────────────────


def test_save_migration_report(tmp_path: Path) -> None:
    """Should write valid JSON to .claude/migration-report.json."""
    (tmp_path / ".claude").mkdir()
    report = m.MigrationReport(
        timestamp="2024-01-01T00:00:00",
        starter_version="v1.0",
        target=str(tmp_path),
        tech_stacks=["python"],
        copied=[".claude/settings.json"],
    )
    m.save_migration_report(tmp_path, report)
    report_path = tmp_path / ".claude" / "migration-report.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert data["tech_stacks"] == ["python"]
    assert data["copied"] == [".claude/settings.json"]


# ── full integration ──────────────────────────────────────────────────────────


def test_full_migration_empty_project(tmp_path: Path) -> None:
    """Full migration of an empty project should create all expected files."""
    audit = m.audit_target(tmp_path, STARTER)
    m.run_migration(tmp_path, STARTER, audit, force=False, dry=False)

    for dst_rel in m.FILES_TO_COPY.values():
        assert (tmp_path / dst_rel).exists(), f"Missing: {dst_rel}"

    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".env.template").exists()
    assert (tmp_path / ".claude" / "migration-report.json").exists()


def test_full_migration_dry_creates_nothing(tmp_path: Path) -> None:
    """Dry migration should create zero files."""
    audit = m.audit_target(tmp_path, STARTER)
    m.run_migration(tmp_path, STARTER, audit, force=False, dry=True)
    assert list(tmp_path.iterdir()) == []


def test_full_migration_non_python_skips_pyproject(tmp_path: Path) -> None:
    """Non-Python project should not receive pyproject patches."""
    (tmp_path / "package.json").write_text('{"name":"x"}')
    audit = m.audit_target(tmp_path, STARTER)
    report = m.run_migration(tmp_path, STARTER, audit, force=False, dry=False)
    assert report.pyproject_sections_added == []


def test_full_migration_python_patches_pyproject(tmp_path: Path) -> None:
    """Python project should receive missing [tool.*] sections."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    audit = m.audit_target(tmp_path, STARTER)
    report = m.run_migration(tmp_path, STARTER, audit, force=False, dry=False)
    assert len(report.pyproject_sections_added) > 0
    content = (tmp_path / "pyproject.toml").read_text()
    assert "[tool.black]" in content


def test_full_migration_report_saved(tmp_path: Path) -> None:
    """Migration report JSON should be saved and contain expected keys."""
    audit = m.audit_target(tmp_path, STARTER)
    m.run_migration(tmp_path, STARTER, audit, force=False, dry=False)
    data = json.loads((tmp_path / ".claude" / "migration-report.json").read_text())
    for key in ("timestamp", "target", "tech_stacks", "copied", "skipped"):
        assert key in data, f"Missing key in report: {key}"
