"""Derive required checks from installation role and ownership through `verify prepare`."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .test_verification import cli, git

ROOT = Path(__file__).parents[3]
pytestmark = pytest.mark.integration

PLAN = ".engineering/state/verification/plan.json"
CHECK = ["make", "check"]
HEALTH = ["make", "engineering-check"]
SUITES = [["make", "engineering-test"], ["make", "engineering-evals"]]
MANAGED = ".engineering/engineering/cli.py"


def run(*args, cwd):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def commit_baseline(root):
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Fixture")
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "baseline")
    git(root, "checkout", "--quiet", "-b", "feature")


@pytest.fixture(scope="module")
def pristine(tmp_path_factory):
    """Build each installation kind once; tests work on disposable copies."""
    base = tmp_path_factory.mktemp("installations")
    generated = base / "generated"
    run(
        sys.executable,
        str(ROOT / ".engineering/scripts/build_template.py"),
        str(generated),
        cwd=ROOT,
    )
    run(sys.executable, "-B", "engineering", "init-installation", cwd=generated)
    git(generated, "init", "--quiet", "-b", "main")
    commit_baseline(generated)

    adopted = base / "adopted"
    adopted.mkdir()
    git(adopted, "init", "--quiet", "-b", "main")
    (adopted / "Makefile").write_text("check:\n\t@echo native check\n")
    (adopted / "README.md").write_text("Existing application\n")
    commit_baseline(adopted)
    git(adopted, "checkout", "--quiet", "main")
    git(adopted, "branch", "--quiet", "-D", "feature")
    run(
        sys.executable,
        str(ROOT / "engineering"),
        "adopt",
        str(adopted),
        "--apply",
        cwd=adopted,
    )
    git(adopted, "add", ".")
    git(adopted, "commit", "--quiet", "-m", "adopt engineering")
    git(adopted, "checkout", "--quiet", "-b", "feature")
    return {"generated": generated, "adopted": adopted, "maintainer": maintainer(base)}


def maintainer(base):
    """A maintainer checkout: distributed managed files plus maintainer-only tooling."""
    root = base / "maintainer"
    content = {
        ".engineering/engineering/tool.py": "VALUE = 1\n",
        ".engineering/engineering/extra.py": "EXTRA = 1\n",
        ".engineering/config.toml": 'schema_version = 1\n[navigation]\nprovider = "none"\n',
        "Makefile": (
            "check:\n\t@true\nengineering-test:\n\t@true\n"
            "# engineering:integration:begin\nengineering-check:\n\t@true\n"
            "engineering-evals:\n\t@true\n# engineering:integration:end\n"
        ),
    }
    modes = {
        ".engineering/engineering/tool.py": {"mode": "file"},
        ".engineering/engineering/extra.py": {"mode": "file"},
        ".engineering/config.toml": {"mode": "preserve"},
        "Makefile": {"mode": "section", "marker": "integration"},
    }
    content[".engineering/tests/test_tool.py"] = "def test_tool():\n    pass\n"
    content[".engineering/template/README.md"] = "Consumer README\n"
    content["app.txt"] = "application\n"
    content[".gitignore"] = "/.engineering/state/verification/\n"
    for name, text in content.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    write_manifest(root, {name: (content[name], spec) for name, spec in modes.items()})
    state = {
        "schema_version": 1,
        "installed_version": "3.0.0",
        "role": "maintainer",
        "entries": {},
    }
    (root / ".engineering/state").mkdir()
    (root / ".engineering/state/install.json").write_text(json.dumps(state))
    git(root, "init", "--quiet", "-b", "main")
    commit_baseline(root)
    return root


def write_manifest(root, entries):
    files = {}
    for name, (text, spec) in entries.items():
        sha = hashlib.sha256(text.encode()).hexdigest()
        files[name] = {
            "ownership": spec,
            "sha256": sha,
            "owned_sha256": sha,
            "executable": False,
            "previous": [],
        }
    manifest = {
        "schema_version": 1,
        "ownership_version": 1,
        "template_version": "3.0.0",
        "files": files,
    }
    (root / ".engineering/manifest.json").write_text(json.dumps(manifest))


@pytest.fixture
def project(pristine, tmp_path, request):
    root = tmp_path / request.param
    shutil.copytree(pristine[request.param], root, symlinks=True)
    return root


consumers = pytest.mark.parametrize("project", ["generated", "adopted"], indirect=True)
maintainer_checkout = pytest.mark.parametrize("project", ["maintainer"], indirect=True)


def edit(root, name, text=None):
    path = root / name
    path.write_text(
        text if text is not None else path.read_text() + "\n# local change\n"
    )


def prepare(root, paths, checks, status=0):
    plan = {
        "base": "main",
        "requirement": "Exercise role-based verification requirements",
        "paths": paths,
        "checks": checks,
        "tools": [[sys.executable, "--version"]],
        "inputs": [],
        "security_required": False,
        "security_reason": "Fixture change has no security-sensitive behavior",
    }
    path = root / PLAN
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan))
    return cli(root, "prepare", "--change", "example", "--plan", PLAN, status=status)


def set_threshold(root):
    config = root / ".engineering/config.toml"
    config.write_text(
        config.read_text().replace("warn_file_lines = 300", "warn_file_lines = 250")
    )


@consumers
@pytest.mark.parametrize(
    "name",
    [".engineering/config.toml", "docs/agents/domain.md", "CLAUDE.md", "Makefile"],
)
def test_consumer_configuration_needs_project_and_health_checks(project, name):
    if name == ".engineering/config.toml":
        set_threshold(project)
    else:
        edit(project, name)
    # Neither a missing health check nor a maintainer suite the project lacks.
    missing = prepare(project, [name], [CHECK], status=1)
    assert missing["status"] == "INCOMPLETE" and "engineering-check" in missing["error"]
    assert "engineering-test" not in missing["error"]
    assert prepare(project, [name], [CHECK, HEALTH])["status"] == "INCOMPLETE"


@consumers
def test_consumer_hook_settings_are_configuration(project):
    settings = project / ".claude/settings.json"
    data = json.loads(settings.read_text())
    data["env"] = {"PROJECT_FLAG": "1"}
    settings.write_text(json.dumps(data, indent=2) + "\n")
    names = [".claude/settings.json"]
    assert "engineering-check" in prepare(project, names, [CHECK], status=1)["error"]
    assert prepare(project, names, [CHECK, HEALTH])["status"] == "INCOMPLETE"


@consumers
def test_consumer_application_change_needs_only_project_checks(project):
    edit(project, "README.md")
    assert prepare(project, ["README.md"], [CHECK])["status"] == "INCOMPLETE"


@consumers
def test_invalid_consumer_configuration_fails_visibly(project):
    config = project / ".engineering/config.toml"
    config.write_text(
        config.read_text().replace("max_file_lines = 500", 'max_file_lines = "many"')
    )
    result = prepare(project, [".engineering/config.toml"], [CHECK, HEALTH], status=1)
    assert result["status"] == "INCOMPLETE" and "max_file_lines" in result["error"]
    assert not (project / ".engineering/state/verification/example.json").exists()


@consumers
def test_unparseable_consumer_configuration_names_the_file(project):
    name = ".engineering/config.toml"
    (project / name).write_text("schema_version = \n")
    result = prepare(project, [name], [CHECK, HEALTH], status=1)
    assert result["status"] == "INCOMPLETE"
    assert result["error"].startswith(f"{name}: ")


@consumers
def test_consumer_managed_implementation_edit_is_rejected_with_route(project):
    edit(project, MANAGED)
    result = prepare(project, [MANAGED], [CHECK, HEALTH, *SUITES], status=1)
    assert result["status"] == "INCOMPLETE"
    assert MANAGED in result["error"]
    assert "engineering update" in result["error"] and "upstream" in result["error"]
    assert not (project / ".engineering/state/verification/example.json").exists()
    status = cli(project, "status", "--change", "example", status=1)
    assert status["status"] == "INCOMPLETE"


@consumers
def test_consumer_deleting_managed_implementation_is_rejected(project):
    (project / MANAGED).unlink()
    result = prepare(project, [MANAGED], [CHECK, HEALTH], status=1)
    assert "engineering update" in result["error"]


@consumers
def test_forged_manifest_digest_does_not_admit_a_managed_edit(project):
    edit(project, MANAGED)
    manifest = project / ".engineering/manifest.json"
    data = json.loads(manifest.read_text())
    sha = hashlib.sha256((project / MANAGED).read_bytes()).hexdigest()
    data["files"][MANAGED].update(sha256=sha, owned_sha256=sha)
    manifest.write_text(json.dumps(data, indent=2) + "\n")
    paths = [MANAGED, ".engineering/manifest.json"]
    result = prepare(project, paths, [CHECK, HEALTH, *SUITES], status=1)
    assert result["status"] == "INCOMPLETE" and MANAGED in result["error"]
    assert "engineering update" in result["error"]


@consumers
def test_deleting_managed_file_and_its_entry_is_rejected(project):
    (project / MANAGED).unlink()
    manifest = project / ".engineering/manifest.json"
    data = json.loads(manifest.read_text())
    del data["files"][MANAGED]
    manifest.write_text(json.dumps(data, indent=2) + "\n")
    paths = [MANAGED, ".engineering/manifest.json"]
    result = prepare(project, paths, [CHECK, HEALTH, *SUITES], status=1)
    assert result["status"] == "INCOMPLETE" and MANAGED in result["error"]
    assert "engineering update" in result["error"]


@consumers
@pytest.mark.parametrize(
    "name", [".engineering/manifest.json", ".engineering/state/install.json"]
)
def test_installation_metadata_needs_health_check(project, name):
    path = project / name
    path.write_text(json.dumps(json.loads(path.read_text()), indent=4) + "\n")
    assert "engineering-check" in prepare(project, [name], [CHECK], status=1)["error"]
    assert prepare(project, [name], [CHECK, HEALTH])["status"] == "INCOMPLETE"


@consumers
def test_distributed_managed_content_is_not_a_local_edit(project):
    # Unchanged distributed bytes are not a local edit; any change is rejected.
    assert (
        "engineering-check" in prepare(project, [MANAGED], [CHECK], status=1)["error"]
    )
    assert prepare(project, [MANAGED], [CHECK, HEALTH])["status"] == "INCOMPLETE"


@consumers
def test_recorded_role_is_trusted_and_fails_closed(project):
    state = project / ".engineering/state/install.json"
    data = json.loads(state.read_text())
    data["role"] = "maintainer"
    state.write_text(json.dumps(data, indent=2) + "\n")
    edit(project, MANAGED)
    paths = [MANAGED, ".engineering/state/install.json"]
    # A declared maintainer must run maintainer suites, whatever targets exist.
    assert (
        "engineering-evals"
        in prepare(project, paths, [CHECK, HEALTH], status=1)["error"]
    )
    assert prepare(project, paths, [CHECK, HEALTH, *SUITES])["status"] == "INCOMPLETE"


def test_generated_and_adopted_projects_classify_identically(pristine, tmp_path):
    outcomes = {}
    for kind in ("generated", "adopted"):
        root = tmp_path / kind
        shutil.copytree(pristine[kind], root, symlinks=True)
        results = []
        for name in (".engineering/config.toml", "AGENTS.md", MANAGED):
            git(root, "checkout", "--quiet", "--", ".")
            if name == ".engineering/config.toml":
                set_threshold(root)
            else:
                edit(root, name)
            result = prepare(root, [name], [CHECK], status=1)
            results.append(result["error"].replace(str(root), "<root>"))
        outcomes[kind] = results
    assert outcomes["generated"] == outcomes["adopted"]


@maintainer_checkout
@pytest.mark.parametrize(
    "name",
    [
        ".engineering/engineering/tool.py",
        ".engineering/tests/test_tool.py",
        ".engineering/template/README.md",
    ],
)
def test_maintainer_source_requires_maintainer_suites(project, name):
    edit(project, name)
    result = prepare(project, [name], [CHECK, HEALTH], status=1)
    assert (
        "engineering-test" in result["error"] and "engineering-evals" in result["error"]
    )
    assert prepare(project, [name], [CHECK, *SUITES])["status"] == "INCOMPLETE"


@maintainer_checkout
def test_role_switch_to_consumer_applies_only_after_merge(project):
    state = project / ".engineering/state/install.json"
    data = json.loads(state.read_text())
    data["role"] = "consumer"
    state.write_text(json.dumps(data, indent=2) + "\n")
    name = ".engineering/tests/test_tool.py"
    edit(project, name)
    paths = [name, ".engineering/state/install.json"]
    # The stricter base role still governs the proposed change.
    result = prepare(project, paths, [CHECK, HEALTH], status=1)
    assert "engineering-test" in result["error"] and "maintainer" in result["error"]
    assert prepare(project, paths, [CHECK, HEALTH, *SUITES])["status"] == "INCOMPLETE"


@maintainer_checkout
def test_maintainer_configuration_needs_only_project_and_health_checks(project):
    edit(
        project,
        ".engineering/config.toml",
        'schema_version = 1\n[navigation]\nprovider = "none"\n\n',
    )
    name = ".engineering/config.toml"
    assert "engineering-check" in prepare(project, [name], [CHECK], status=1)["error"]
    assert prepare(project, [name], [CHECK, HEALTH])["status"] == "INCOMPLETE"


@maintainer_checkout
def test_maintainer_manifest_is_maintainer_source(project):
    # Dropping an entry and weakening ownership changes every consumer's contract.
    write_manifest(
        project,
        {
            ".engineering/engineering/tool.py": ("VALUE = 1\n", {"mode": "preserve"}),
            ".engineering/config.toml": (
                'schema_version = 1\n[navigation]\nprovider = "none"\n',
                {"mode": "preserve"},
            ),
        },
    )
    names = [".engineering/manifest.json"]
    assert "engineering-test" in prepare(project, names, [CHECK], status=1)["error"]
    result = prepare(project, names, [CHECK, HEALTH], status=1)
    assert (
        "engineering-test" in result["error"] and "engineering-evals" in result["error"]
    )
    assert (
        "engineering-check"
        in prepare(project, names, [CHECK, *SUITES], status=1)["error"]
    )
    assert prepare(project, names, [CHECK, HEALTH, *SUITES])["status"] == "INCOMPLETE"


@maintainer_checkout
def test_maintainer_install_state_is_maintainer_source(project):
    name = ".engineering/state/install.json"
    path = project / name
    path.write_text(json.dumps(json.loads(path.read_text()), indent=4) + "\n")
    result = prepare(project, [name], [CHECK, HEALTH], status=1)
    assert (
        "engineering-test" in result["error"] and "engineering-evals" in result["error"]
    )
    assert (
        "engineering-check"
        in prepare(project, [name], [CHECK, *SUITES], status=1)["error"]
    )
    assert prepare(project, [name], [CHECK, HEALTH, *SUITES])["status"] == "INCOMPLETE"


@maintainer_checkout
def test_removing_a_maintainer_target_cannot_lower_requirements(project):
    makefile = project / "Makefile"
    makefile.write_text(
        makefile.read_text().replace("engineering-test:\n\t@true\n", "")
    )
    edit(project, ".engineering/engineering/tool.py")
    paths = ["Makefile", ".engineering/engineering/tool.py"]
    result = prepare(project, paths, [CHECK, HEALTH], status=1)
    assert "engineering-test" in result["error"]
    assert prepare(project, paths, [CHECK, HEALTH, *SUITES])["status"] == "INCOMPLETE"


@maintainer_checkout
def test_removing_distributed_source_still_requires_maintainer_suites(project):
    # Ownership from the baseline manifest applies even when the entry is dropped.
    (project / ".engineering/engineering/extra.py").unlink()
    write_manifest(
        project,
        {
            ".engineering/engineering/tool.py": ("VALUE = 1\n", {"mode": "file"}),
            ".engineering/config.toml": (
                'schema_version = 1\n[navigation]\nprovider = "none"\n',
                {"mode": "preserve"},
            ),
        },
    )
    paths = [".engineering/engineering/extra.py", ".engineering/manifest.json"]
    assert (
        "engineering-evals"
        in prepare(project, paths, [CHECK, HEALTH], status=1)["error"]
    )


@consumers
def test_missing_manifest_blocks_classification(project):
    (project / ".engineering/manifest.json").unlink()
    names = [".engineering/manifest.json"]
    result = prepare(project, names, [CHECK, HEALTH, *SUITES], status=1)
    assert result["status"] == "INCOMPLETE" and "manifest" in result["error"]
