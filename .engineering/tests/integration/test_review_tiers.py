"""Review tiers: declared tier, starter-rule floor and reviewer roles via the CLI."""

import json
import os
import subprocess
import sys
import tomllib

import pytest

from .test_verification import (
    TOOLING,
    change_plan,
    cli,
    complete,
    git,
    prepare,
    report,
)
from .test_verification import repo as repo
from .test_verification_requirements import (
    CHECK,
    HEALTH,
    SUITES,
    consumers,
    edit,
    maintainer_checkout,
    set_threshold,
)
from .test_verification_requirements import prepare as prepare_paths
from .test_verification_requirements import pristine as pristine
from .test_verification_requirements import project as project

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "changes,message",
    [
        (
            {"security_required": False, "security_reason": "Not sensitive"},
            "replaced by tier and tier_reason",
        ),
        ({"tier": None}, "tier"),
        ({"tier": "trivial"}, "documentation, ordinary, sensitive"),
        ({"tier_reason": " "}, "tier_reason"),
    ],
)
def test_plan_requires_a_review_tier_with_reason(repo, changes, message):
    path = repo / ".engineering/state/verification/plan.json"
    plan = {**json.loads(path.read_text()), **changes}
    if changes.get("tier", "") is None or "security_required" in changes:
        plan.pop("tier")
        plan.pop("tier_reason")
    path.write_text(json.dumps(plan))
    result = prepare(repo, status=1)
    assert result["status"] == "INCOMPLETE" and message in result["error"]


def test_declared_tier_below_floor_names_paths_and_rules(repo):
    (repo / "Makefile").write_text("check:\n\t@test -s app.txt\n\n")
    change_plan(repo, paths=["app.txt", "Makefile"])
    error = prepare(repo, status=1)["error"]
    assert "below the tier floor sensitive" in error
    assert "Makefile" in error and "build recipe" in error
    assert "app.txt" not in error
    # A mixed change takes the highest path floor; declaring it is accepted.
    change_plan(repo, tier="sensitive")
    result = prepare(repo)
    assert result["floor"] == "sensitive" and result["required_roles"][-1] == "security"


def test_raised_tier_requires_its_roles_and_reports_them(repo):
    change_plan(repo, tier="sensitive", tier_reason="Raised: parses credentials")
    token = prepare(repo)["snapshot"]
    cli(repo, "check", "--change", "example", "--snapshot", token)
    report(repo, token, "behavioral")
    result = cli(repo, "status", "--change", "example", status=1)
    assert result["tier"] == "sensitive"
    assert result["tier_reason"] == "Raised: parses credentials"
    assert result["floor"] == "ordinary"
    assert result["required_roles"] == ["maintainability", "behavioral", "security"]
    assert result["missing_roles"] == ["maintainability", "security"]
    assert result["shared_reviewers"] == {}


def test_documentation_tier_needs_project_review_settings(repo):
    # Without project configuration no path is documentation.
    change_plan(repo, tier="documentation")
    error = prepare(repo, status=1)["error"]
    assert "below the tier floor ordinary" in error and "app.txt" in error


CONFIG = ".engineering/config.toml"


def settings_text(documentation=(), sensitive=(), extra=""):
    return (
        'schema_version = 2\n[navigation]\nprovider = "none"\n[review]\n'
        f"documentation = {json.dumps(list(documentation))}\n"
        f"sensitive = {json.dumps(list(sensitive))}\n{extra}"
    )


def commit_base_settings(repo, text):
    """Commit review settings to the comparison base, keeping feature edits."""
    git(repo, "checkout", "--quiet", "main")
    (repo / CONFIG).write_text(text)
    git(repo, "add", CONFIG)
    git(repo, "commit", "--quiet", "-m", "review settings")
    git(repo, "checkout", "--quiet", "feature")
    git(repo, "merge", "--quiet", "--ff-only", "main")


def prepare_edits(repo, names, tier="sensitive"):
    """Replace the fixture change with edits to names; return prepare's result."""
    (repo / "app.txt").write_text("before\n")
    for name in names:
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text("changed\n")
    change_plan(repo, paths=names, tier=tier)
    return prepare(repo, status=0 if tier == "sensitive" else 1)


def recorded_paths(repo):
    record = repo / ".engineering/state/verification/example.json"
    return json.loads(record.read_text())["requirements"]["paths"]


def test_documentation_only_change_passes_with_one_behavioral_report(repo):
    commit_base_settings(repo, settings_text(["README.md", "docs/**"]))
    (repo / "app.txt").write_text("before\n")
    (repo / "docs").mkdir()
    (repo / "docs/guide.md").write_text("Run make check.\n")
    change_plan(repo, paths=["docs/guide.md"], tier="documentation")
    result = prepare(repo)
    assert result["floor"] == "documentation"
    assert result["required_roles"] == ["behavioral"]
    token = result["snapshot"]
    cli(repo, "check", "--change", "example", "--snapshot", token)
    report(repo, token, "behavioral")
    result = cli(repo, "status", "--change", "example")
    assert result["status"] == "PASS" and result["missing_roles"] == []


@pytest.mark.parametrize(
    "name,floor,rule",
    [
        ("README.md", "documentation", "project documentation setting"),
        ("docs/context/product.md", "documentation", "project documentation setting"),
        ("docs/adr/0003-choice.md", "documentation", "project documentation setting"),
        ("docs/agents/domain.md", "ordinary", "agent policy"),
        ("notes.md", "ordinary", "no documentation rule"),
    ],
)
def test_documentation_settings_classify_domain_docs_not_agent_policy(
    repo, name, floor, rule
):
    commit_base_settings(repo, settings_text(["README.md", "docs/**"]))
    prepare_edits(repo, [name])
    assert recorded_paths(repo)[floor] == {name: rule}


def test_project_sensitive_additions_raise_the_floor(repo):
    commit_base_settings(repo, settings_text(["docs/**"], ["src/auth/**"]))
    error = prepare_edits(repo, ["src/auth/login.py"], tier="ordinary")["error"]
    assert "below the tier floor sensitive" in error
    assert "src/auth/login.py (project sensitive setting)" in error


def test_project_settings_cannot_weaken_starter_rules(repo):
    commit_base_settings(repo, settings_text(["**"]))
    prepare_edits(repo, ["Makefile", "CLAUDE.md", "guide.md"])
    paths = recorded_paths(repo)
    assert paths["sensitive"] == {"Makefile": "build recipe"}
    assert paths["ordinary"] == {"CLAUDE.md": "agent policy"}
    assert paths["documentation"] == {"guide.md": "project documentation setting"}


def test_editing_review_settings_uses_the_stricter_of_base_and_proposed(repo):
    commit_base_settings(repo, settings_text(["docs/**"], ["billing/**"]))
    names = ["docs/guide.md", "src/app.py", "billing/rates.py", "api/keys.py"]
    prepare_edits(repo, names)
    # The proposed settings drop billing and document src; they add api.
    (repo / CONFIG).write_text(settings_text(["src/**"], ["api/**"]))
    change_plan(repo, paths=[CONFIG, *names])
    prepare(repo)
    assert recorded_paths(repo) == {
        "sensitive": {
            "api/keys.py": "project sensitive setting",
            "billing/rates.py": "project sensitive setting",
        },
        "ordinary": {
            CONFIG: "review settings",
            "docs/guide.md": "no documentation rule",
            "src/app.py": "no documentation rule",
        },
        "documentation": {},
    }


def test_review_settings_floor_at_ordinary_even_when_documented(repo):
    commit_base_settings(repo, settings_text(["**"]))
    (repo / CONFIG).write_text(settings_text(["**"], extra="# reviewed\n"))
    change_plan(repo, paths=[CONFIG], tier="documentation")
    error = prepare(repo, status=1)["error"]
    assert f"{CONFIG} (review settings)" in error


@pytest.mark.parametrize(
    "setting,message",
    [
        ('documentation = "docs/**"', "review.documentation"),
        ("sensitive = [1]", "review.sensitive"),
        ('sensitive = [""]', "review.sensitive"),
        ("skip = true", "review"),
    ],
)
def test_invalid_review_settings_fail_planning(repo, setting, message):
    commit_base_settings(repo, settings_text(["docs/**"]))
    (repo / CONFIG).write_text(f"schema_version = 2\n[review]\n{setting}\n")
    change_plan(repo, paths=["app.txt", CONFIG])
    result = prepare(repo, status=1)
    assert result["status"] == "INCOMPLETE" and message in result["error"]


@pytest.mark.parametrize(
    "name,rule",
    [
        ("GNUmakefile", "build recipe"),
        ("build/rules.mk", "build recipe"),
        (".engineering/scripts/check.sh", "check script"),
        (".claude/statusline.sh", "agent-executed script"),
    ],
)
def test_build_and_agent_scripts_floor_at_sensitive(repo, name, rule):
    error = prepare_edits(repo, [name], tier="ordinary")["error"]
    assert f"{name} ({rule})" in error


def test_one_session_may_file_both_ordinary_reports(repo):
    token = prepare(repo)["snapshot"]
    cli(repo, "check", "--change", "example", "--snapshot", token)
    report(repo, token, "maintainability", reviewer="fresh-combined-session")
    report(repo, token, "behavioral", reviewer="fresh-combined-session")
    result = cli(repo, "status", "--change", "example")
    assert result["status"] == "PASS"
    assert result["shared_reviewers"] == {
        "fresh-combined-session": ["behavioral", "maintainability"]
    }


def test_sensitive_reports_need_separate_sessions(repo):
    change_plan(repo, tier="sensitive", tier_reason="Raised: parses credentials")
    token = prepare(repo)["snapshot"]
    cli(repo, "check", "--change", "example", "--snapshot", token)
    report(repo, token, "maintainability", reviewer="one-session")
    result = report(repo, token, "security", reviewer="one-session", expected=1)
    assert "separate" in result["error"]
    # Replacing a role's own report is not sharing.
    report(repo, token, "maintainability", reviewer="one-session")
    report(repo, token, "behavioral")
    report(repo, token, "security")
    assert cli(repo, "status", "--change", "example")["status"] == "PASS"
    # A record that bypassed the record check still cannot pass.
    path = repo / ".engineering/state/verification/example.json"
    data = json.loads(path.read_text())
    data["reports"]["security"]["reviewer"] = "one-session"
    path.write_text(json.dumps(data))
    result = cli(repo, "status", "--change", "example", status=1)
    assert result["status"] == "INCOMPLETE"
    assert result["shared_reviewers"] == {
        "one-session": ["maintainability", "security"]
    }
    assert any("separate" in item for item in result["missing"])


def test_record_stores_floor_categories_checks_and_roles(repo):
    (repo / "Makefile").write_text("check:\n\t@test -s app.txt\n\n")
    change_plan(repo, paths=["app.txt", "Makefile"], tier="sensitive")
    prepare(repo)
    data = json.loads(
        (repo / ".engineering/state/verification/example.json").read_text()
    )
    assert data["schema_version"] == 2
    assert data["requirements"] == {
        "floor": "sensitive",
        "paths": {
            "sensitive": {"Makefile": "build recipe"},
            "ordinary": {"app.txt": "no documentation rule"},
            "documentation": {},
        },
        "checks": [["make", "check"]],
        "roles": ["maintainability", "behavioral", "security"],
    }


def test_record_without_tier_data_requires_preparing_again(repo):
    complete(repo)
    path = repo / ".engineering/state/verification/example.json"
    legacy = json.loads(path.read_text())
    legacy["schema_version"] = 1
    del legacy["requirements"]
    plan = legacy["inputs"]["plan"]
    del plan["tier"], plan["tier_reason"]
    plan.update(security_required=False, security_reason="Legacy")
    path.write_text(json.dumps(legacy))
    result = cli(repo, "status", "--change", "example", status=1)
    assert result["status"] == "INCOMPLETE" and "prepare again" in result["error"]
    result = prepare(repo)
    assert result["status"] == "INCOMPLETE" and result["reports"] == {}
    history = json.loads((repo / result["previous_evidence"]).read_text())
    assert history["schema_version"] == 1


def floor_error(root, paths, checks, tier):
    return prepare_paths(root, paths, checks, status=1, tier=tier)["error"]


@consumers
@pytest.mark.parametrize(
    "name,rule",
    [
        ("pyproject.toml", "dependency manifest or lock"),
        ("uv.lock", "dependency manifest or lock"),
        ("web/package.json", "dependency manifest or lock"),
        (".claude/settings.json", "agent settings"),
        (".claude/hooks/project_hook.py", "hook"),
        (".github/workflows/ci.yml", "workflow"),
        ("Makefile", "build recipe"),
    ],
)
def test_consumer_starter_sensitive_paths_floor_at_sensitive(project, name, rule):
    path = project / name
    path.parent.mkdir(parents=True, exist_ok=True)
    edit(project, name, (path.read_text() if path.exists() else "") + "\n")
    checks = [CHECK, HEALTH]
    error = floor_error(project, [name], checks, "ordinary")
    assert "below the tier floor sensitive" in error
    assert name in error and rule in error
    assert prepare_paths(project, [name], checks)["floor"] == "sensitive"


@consumers
@pytest.mark.parametrize("name", ["CLAUDE.md", "AGENTS.md", "docs/agents/domain.md"])
def test_agent_policy_is_never_documentation(project, name):
    edit(project, name)
    error = floor_error(project, [name], [CHECK, HEALTH], "documentation")
    assert "below the tier floor ordinary" in error and "agent policy" in error
    result = prepare_paths(project, [name], [CHECK, HEALTH], tier="ordinary")
    assert result["floor"] == "ordinary"
    assert result["required_roles"] == ["maintainability", "behavioral"]


def test_generated_and_adopted_projects_share_review_defaults(pristine):
    settings = [
        tomllib.loads((pristine[kind] / CONFIG).read_text())["review"]
        for kind in ("generated", "adopted")
    ]
    assert settings[0] == settings[1]
    assert settings[0] == {
        "documentation": ["README.md", "docs/**/*.md"],
        "sensitive": [],
    }


@consumers
def test_consumer_readme_is_documentation_by_default(project):
    edit(project, "README.md")
    result = prepare_paths(project, ["README.md"], [CHECK], tier="documentation")
    assert result["floor"] == "documentation"
    assert result["required_roles"] == ["behavioral"]


@consumers
def test_mixed_change_takes_the_highest_path_floor(project):
    edit(project, "README.md")
    edit(project, "Makefile")
    names = ["README.md", "Makefile"]
    error = floor_error(project, names, [CHECK, HEALTH], "ordinary")
    assert "Makefile (build recipe)" in error and "README.md" not in error
    assert prepare_paths(project, names, [CHECK, HEALTH])["status"] == "INCOMPLETE"


@consumers
def test_required_checks_are_unchanged_by_tier(project):
    set_threshold(project)
    name = ".engineering/config.toml"
    errors = {
        tier: floor_error(project, [name], [CHECK], tier)
        for tier in ("ordinary", "sensitive")
    }
    assert all("engineering-check" in error for error in errors.values())
    assert errors["ordinary"] == errors["sensitive"]


@maintainer_checkout
@pytest.mark.parametrize(
    "name,rule",
    [
        (".engineering/engineering/verification.py", "verification module"),
        (".engineering/engineering/publication_git.py", "publication module"),
        (".engineering/engineering/deps.py", "dependency module"),
        (".engineering/engineering/graft.py", "dependency module"),
        (".engineering/engineering/skill_install.py", "skill installation module"),
        (".engineering/engineering/transaction.py", "apply or transaction module"),
        (".engineering/engineering/migrate/legacy.py", "migration module"),
    ],
)
def test_maintainer_destructive_modules_floor_at_sensitive(project, name, rule):
    (project / name).parent.mkdir(parents=True, exist_ok=True)
    edit(project, name, "VALUE = 2\n")
    checks = [CHECK, *SUITES]
    error = floor_error(project, [name], checks, "ordinary")
    assert name in error and rule in error
    assert prepare_paths(project, [name], checks)["floor"] == "sensitive"


@maintainer_checkout
def test_other_maintainer_source_floors_at_ordinary(project):
    name = ".engineering/engineering/tool.py"
    edit(project, name)
    result = prepare_paths(project, [name], [CHECK, *SUITES], tier="ordinary")
    assert result["floor"] == "ordinary"


def test_status_reports_the_floor_current_rules_give(repo):
    change_plan(repo, tier="sensitive", tier_reason="Raised: parses credentials")
    complete(repo)
    stricter = (
        "import engineering.verification_requirements as rules\n"
        "rules.STARTER_SENSITIVE['fixture rule'] = ('app.txt',)\n"
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            stricter + "from engineering.cli import main; raise SystemExit(main())",
            "--root",
            str(repo),
            "verify",
            "status",
            "--change",
            "example",
        ],
        env={**os.environ, "PYTHONPATH": str(TOOLING)},
        capture_output=True,
        text=True,
    )
    assert json.loads(proc.stdout)["floor"] == "sensitive"
    assert cli(repo, "status", "--change", "example")["floor"] == "ordinary"
