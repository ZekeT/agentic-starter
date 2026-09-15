"""Prove the bounded adoption/update checkpoint before widening migration coverage."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT / ".harness"))
from factory.adoption import plan_installation  # noqa: E402
from factory.apply import apply_plan  # noqa: E402
from factory.doctor import diagnose  # noqa: E402
from factory.ownership import digest, encoded, owned_content  # noqa: E402

pytestmark = pytest.mark.integration


def write(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode() if isinstance(content, str) else content)
    return path


def commit(root):
    for args in (
        ("add", "."),
        (
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.com",
            "commit",
            "-qm",
            "checkpoint",
            "--allow-empty",
        ),
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def snapshot(root):
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


@pytest.fixture
def checkpoint(tmp_path):
    template, target = tmp_path / "template", tmp_path / "project"
    template.mkdir()
    target.mkdir()
    manifest = json.loads((ROOT / ".harness/template-manifest.json").read_text())
    files = manifest["files"]
    for path in (ROOT / ".harness/factory").glob("*.py"):
        files.setdefault(str(path.relative_to(ROOT)), {})
    for name, entry in files.items():
        if name == ".env.template" or name.startswith(("docs/", ".github/")):
            entry["ownership"] = {"mode": "preserve"}
            continue
        content = (ROOT / name).read_bytes()
        if name in {"CLAUDE.md", "Makefile", ".gitignore"}:
            entry["ownership"] = {"mode": "section", "marker": "integration"}
            if name == "Makefile":
                content = b"evals:\n\tpython3 .harness/evals/run_evals.py\nfactory-check:\n\tuv run --no-project --isolated --python 3.12 python factory doctor\ncheck: factory-check\n"
            prefix, suffix = (
                (
                    b"<!-- factory:integration:begin -->\n",
                    b"<!-- factory:integration:end -->\n",
                )
                if name.endswith(".md")
                else (b"# factory:integration:begin\n", b"# factory:integration:end\n")
            )
            if prefix not in content:
                content = prefix + content + suffix
        else:
            entry["ownership"] = {
                "mode": "hooks" if name == ".claude/settings.json" else "file"
            }
        destination = write(template, name, content)
        entry["executable"] = bool((ROOT / name).stat().st_mode & 0o111)
        if entry["executable"]:
            destination.chmod(0o755)
        entry["sha256"] = digest(content)
        entry["owned_sha256"] = digest(owned_content(content, name, entry["ownership"]))
    manifest["ownership_version"] = 1
    write(template, ".harness/template-manifest.json", encoded(manifest))
    write(
        target,
        "pyproject.toml",
        '[project]\nname="example"\nrequires-python=">=3.11"\n',
    )
    write(
        target, "Makefile", "# project build\ncheck:\n\t@echo canonical-project-check\n"
    )
    write(target, "CLAUDE.md", b"Project instructions\r\nPreserve exact bytes.\r\n")
    write(target, "AGENTS.md", "Project-specific agent guidance\n")
    write(
        target,
        ".gitignore",
        "custom-output/\n.harness/graft/node_modules/\n.claude/skills/graft/\n",
    )
    write(target, ".github/workflows/project.yml", "# project CI stays untouched\n")
    write(target, "openspec/config.yaml", "schema: spec-driven\n")
    write(
        target,
        ".claude/settings.json",
        json.dumps(
            {
                "statusLine": {"command": "project-status"},
                "permissions": {"allow": ["Read"]},
                "hooks": {
                    "Stop": [
                        {"hooks": [{"type": "command", "command": "project-hook"}]}
                    ]
                },
            }
        ),
    )
    # Explicit external setup precedes adoption. Doctor structurally inspects
    # these fixture prerequisites; it must never execute the fake Graft CLI.
    write(
        target,
        ".harness/graft/node_modules/@nanonets/graft/package.json",
        '{"version":"0.18.0"}',
    )
    write(
        target,
        ".harness/graft/node_modules/@nanonets/graft/dist/cli.js",
        "throw Error('must not execute');",
    )
    write(target, ".claude/skills/graft/SKILL.md", "Upstream-owned fixture skill\n")
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    commit(target)
    return template, target


def test_adopt_update_repeat_preserves_project_and_passes_doctor(checkpoint):
    template, target = checkpoint
    before = snapshot(target)
    plan = plan_installation(template, target)
    assert not plan.conflicts
    assert snapshot(target) == before
    assert apply_plan(plan) == 0
    assert not [f for f in diagnose(target) if f.severity == "ERROR"]
    for name in ("pyproject.toml", "AGENTS.md", ".github/workflows/project.yml"):
        assert (target / name).read_bytes() == before[name]
    for name in ("CLAUDE.md", "Makefile", ".gitignore"):
        assert (target / name).read_bytes().startswith(before[name])
    settings = json.loads((target / ".claude/settings.json").read_text())
    assert settings["statusLine"]["command"] == "project-status"
    assert settings["permissions"] == {"allow": ["Read"]}
    assert settings["hooks"]["Stop"][0]["hooks"][0]["command"] == "project-hook"
    commit(target)
    path = template / "CLAUDE.md"
    path.write_bytes(
        path.read_bytes().replace(
            b"<!-- factory:integration:end -->",
            b"Updated upstream guidance\n<!-- factory:integration:end -->",
        )
    )
    manifest = json.loads((template / ".harness/template-manifest.json").read_text())
    manifest["files"]["CLAUDE.md"]["sha256"] = digest(path.read_bytes())
    manifest["files"]["CLAUDE.md"]["owned_sha256"] = digest(
        owned_content(
            path.read_bytes(), "CLAUDE.md", manifest["files"]["CLAUDE.md"]["ownership"]
        )
    )
    write(template, ".harness/template-manifest.json", encoded(manifest))
    update = plan_installation(template, target, "update")
    assert not update.conflicts
    assert apply_plan(update) == 0
    assert (target / "CLAUDE.md").read_bytes().startswith(before["CLAUDE.md"])
    commit(target)
    repeat = plan_installation(template, target, "update")
    assert not repeat.conflicts
    assert not [a for a in repeat.actions if a.content is not None]
    stable = snapshot(target)
    assert apply_plan(repeat) == 0
    assert snapshot(target) == stable


def test_conflicts_prevent_every_write(checkpoint):
    template, target = checkpoint
    write(target, "factory", "custom project executable")
    commit(target)
    before = snapshot(target)
    plan = plan_installation(template, target)
    assert plan.conflicts
    with pytest.raises(ValueError, match="Unresolved conflicts"):
        apply_plan(plan)
    assert snapshot(target) == before


def test_actual_distribution_adopt_update_roundtrip(checkpoint):
    """Use production manifest/regions, not the simplified fixture template."""
    _, target = checkpoint
    before = snapshot(target)
    plan = plan_installation(ROOT, target)
    assert not plan.conflicts
    assert apply_plan(plan) == 0
    for name in ("CLAUDE.md", "Makefile", ".gitignore"):
        assert (target / name).read_bytes().startswith(before[name])
    commit(target)
    repeat = plan_installation(ROOT, target, "update")
    assert not repeat.conflicts
    assert not [a for a in repeat.actions if a.content is not None]
    assert apply_plan(repeat) == 0
