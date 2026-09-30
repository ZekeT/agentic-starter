"""Verify real starter update output against fetched, pinned Git objects."""

import functools
import hashlib
import json
import shutil
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

from .test_verification import cli, git
from .test_verification_requirements import CHECK, HEALTH, PLAN, ROOT, run

pytestmark = pytest.mark.integration
MANIFEST = ".engineering/manifest.json"
MANAGED = ".engineering/engineering/config.py"
RETIRED = ".engineering/engineering/retired_fixture.py"
ADDED = ".engineering/engineering/added_fixture.py"


class GitHTTPHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass  # Failed assertions already retain Git's command diagnostics.


def refresh(source):
    run(
        sys.executable,
        ".engineering/scripts/generate_template_manifest.py",
        cwd=source,
    )


def inventory(source, *, add=(), remove=()):
    path = source / ".engineering/template/files.json"
    data = json.loads(path.read_text())
    for name in add:
        data["managed"][name] = name
        (source / name).write_text('"""Fixture distribution module."""\n')
    for name in remove:
        del data["managed"][name]
        (source / name).unlink()
    path.write_text(json.dumps(data))
    refresh(source)


@pytest.fixture
def update(tmp_path):
    source = tmp_path / "source"
    git(ROOT, "clone", "--quiet", "--no-local", str(ROOT), str(source))
    # Serve only a tiny fixture history, containing real starter distributions.
    shutil.rmtree(source / ".git")
    git(source, "init", "--quiet", "-b", "main")
    git(source, "config", "user.name", "Fixture")
    git(source, "config", "user.email", "fixture@example.invalid")
    inventory(source, add=[RETIRED])
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "old distribution")
    consumer = tmp_path / "consumer"
    run(
        sys.executable,
        ".engineering/scripts/build_template.py",
        str(consumer),
        cwd=source,
    )
    run(sys.executable, "engineering", "init-installation", cwd=consumer)
    git(consumer, "init", "--quiet", "-b", "main")
    git(consumer, "config", "user.name", "Fixture")
    git(consumer, "config", "user.email", "fixture@example.invalid")
    git(consumer, "add", ".")
    git(consumer, "commit", "--quiet", "-m", "consumer baseline")
    git(consumer, "checkout", "--quiet", "-b", "feature")
    managed = source / MANAGED
    managed.write_text(managed.read_text() + "\n# Updated upstream fixture\n")
    inventory(source, add=[ADDED], remove=[RETIRED])
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "new distribution")
    commit = git(source, "rev-parse", "HEAD")
    git(source, "tag", "-a", "update-v1", "-m", "pinned release")
    git(source, "update-server-info")
    run(sys.executable, "engineering", "update", str(consumer), "--apply", cwd=source)

    handler = functools.partial(GitHTTPHandler, directory=str(source))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    plan = {
        "base": "main",
        "requirement": "Verify the consumer update against its pinned starter source",
        "paths": git(consumer, "diff", "--name-only", "HEAD").splitlines()
        + git(consumer, "ls-files", "--others", "--exclude-standard").splitlines(),
        "checks": [CHECK, HEALTH],
        "tools": [[sys.executable, "--version"]],
        "inputs": [],
        "tier": "sensitive",
        "tier_reason": "Updating managed executable code from a pinned source",
        "starter_source": {
            "repository": f"http://127.0.0.1:{server.server_port}/.git",
            "commit": commit,
            "tag": "refs/tags/update-v1",
        },
    }
    path = consumer / PLAN
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan))
    try:
        yield consumer, source, plan
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def prepare(update, *, status=0):
    consumer, _, plan = update
    (consumer / PLAN).write_text(json.dumps(plan))
    return cli(consumer, "prepare", "--change", "update", "--plan", PLAN, status=status)


def test_applied_update_prepares_with_pinned_distribution_evidence(update):
    consumer, source, plan = update
    assert (consumer / MANAGED).read_bytes() == (source / MANAGED).read_bytes()
    assert (consumer / ADDED).is_file() and not (consumer / RETIRED).exists()
    result = prepare(update)
    assert result["status"] == "INCOMPLETE"  # Checks/reviews have not happened.
    assert result["starter_source"]["commit"] == plan["starter_source"]["commit"]
    assert (
        result["starter_source"]["repository"] == plan["starter_source"]["repository"]
    )
    assert len(result["starter_source"]["manifest_sha256"]) == 64
    plan["checks"] = [CHECK]
    missing = prepare(update, status=1)
    assert "engineering-check" in missing["error"]
    assert "engineering-test" not in missing["error"]


def test_update_source_always_requires_security_review(update):
    _, _, plan = update
    plan["tier"] = "ordinary"
    result = prepare(update, status=1)
    assert "sensitive" in result["error"]


def test_source_is_required_even_for_real_update_output(update):
    _, _, plan = update
    del plan["starter_source"]
    result = prepare(update, status=1)
    assert result["status"] == "INCOMPLETE"
    assert "starter_source" in result["error"] and MANAGED in result["error"]


@pytest.mark.parametrize("forgery", ["digest", "drop", "ownership"])
def test_proposed_manifest_cannot_vouch_for_a_forged_update(update, forgery):
    consumer, _, _ = update
    path = consumer / MANAGED
    path.write_text("# Not from the starter source\n")
    manifest = json.loads((consumer / MANIFEST).read_text())
    if forgery == "digest":
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest["files"][MANAGED].update(sha256=sha, owned_sha256=sha)
    elif forgery == "drop":
        del manifest["files"][MANAGED]
    else:
        manifest["files"][MANAGED]["ownership"] = {"mode": "preserve"}
    (consumer / MANIFEST).write_text(json.dumps(manifest))
    result = prepare(update, status=1)
    assert result["status"] == "INCOMPLETE"
    assert "manifest differs from pinned starter source" in result["error"]


@pytest.mark.parametrize("mismatch", ["bytes", "mode", "missing", "retained"])
def test_managed_bytes_modes_and_removals_must_match_source(update, mismatch):
    consumer, _, _ = update
    if mismatch == "bytes":
        (consumer / MANAGED).write_text("# Forged bytes, original manifest\n")
    elif mismatch == "mode":
        (consumer / MANAGED).chmod(0o755)
    elif mismatch == "missing":
        (consumer / ADDED).unlink()
    else:
        (consumer / RETIRED).write_text("# Retained despite upstream removal\n")
    result = prepare(update, status=1)
    assert result["status"] == "INCOMPLETE"
    assert "differ from pinned starter source" in result["error"]


def test_omitted_managed_update_path_cannot_hide_old_bytes(update):
    _, _, plan = update
    plan["paths"].remove(MANAGED)
    result = prepare(update, status=1)
    assert MANAGED in result["error"]


def test_pinned_commit_without_tag_ignores_source_working_edits(update):
    consumer, source, plan = update
    del plan["starter_source"]["tag"]
    result = prepare(update)
    (source / MANAGED).write_text(
        "# Uncommitted source working bytes are not authority\n"
    )
    status = cli(consumer, "status", "--change", "update", status=1)
    assert status["snapshot"] == result["snapshot"]
    assert status["starter_source"] == result["starter_source"]


@pytest.mark.parametrize("operation", ["status", "check", "record"])
@pytest.mark.parametrize("change", ["moved", "unreachable"])
def test_source_failure_blocks_evidence_reuse(update, operation, change):
    consumer, source, _ = update
    result = prepare(update)
    if change == "moved":
        git(source, "tag", "-f", "update-v1", "HEAD~1")
        git(source, "update-server-info")
    else:
        (source / ".git").rename(source / "unavailable.git")
    extra = []
    if operation == "check":
        extra = ["--snapshot", result["snapshot"]]
    elif operation == "record":
        extra = ["--report", ".engineering/state/verification/report.json"]
        # Source validation happens before any reviewer attestation is consumed.
        (consumer / extra[-1]).write_text("{}")
    blocked = cli(consumer, operation, "--change", "update", *extra, status=1)
    assert blocked["status"] == "INCOMPLETE"
    assert "Starter source" in blocked["error"]


def test_invalid_committed_source_distribution_is_rejected(update):
    _, source, plan = update
    (source / MANAGED).write_text(
        "# Modified source without regenerating its manifest\n"
    )
    git(source, "add", MANAGED)
    git(source, "commit", "--quiet", "-m", "inconsistent release")
    git(source, "update-server-info")
    plan["starter_source"]["commit"] = git(source, "rev-parse", "HEAD")
    del plan["starter_source"]["tag"]
    result = prepare(update, status=1)
    assert "template distribution hash mismatch" in result["error"]


def test_source_file_mappings_define_the_bytes_offered_to_consumers(update):
    consumer, source, plan = update
    git(consumer, "add", ".")
    git(consumer, "commit", "--quiet", "-m", "first update")
    origin = ".engineering/template/config-module.py"
    (source / origin).write_bytes(
        (source / MANAGED).read_bytes() + b"\n# Mapped payload\n"
    )
    inventory_path = source / ".engineering/template/files.json"
    selected = json.loads(inventory_path.read_text())
    selected["managed"][MANAGED] = origin
    inventory_path.write_text(json.dumps(selected))
    refresh(source)
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "mapped distribution")
    git(source, "update-server-info")
    plan["starter_source"]["commit"] = git(source, "rev-parse", "HEAD")
    del plan["starter_source"]["tag"]
    run(sys.executable, "engineering", "update", str(consumer), "--apply", cwd=source)
    assert (consumer / MANAGED).read_bytes() != (source / MANAGED).read_bytes()
    assert (
        prepare(update)["starter_source"]["commit"] == plan["starter_source"]["commit"]
    )


def test_changed_annotated_tag_object_invalidates_existing_snapshot(update):
    consumer, source, _ = update
    prepare(update)
    git(source, "tag", "-f", "-a", "update-v1", "-m", "replacement annotation")
    git(source, "update-server-info")
    result = cli(consumer, "status", "--change", "update", status=1)
    assert result["status"] == "STALE"


@pytest.mark.parametrize(
    "source_spec",
    [
        {"repository": "/local/checkout", "commit": "a" * 40},
        {"repository": "file:///local/checkout", "commit": "a" * 40},
        {"repository": "ext::untrusted-command", "commit": "a" * 40},
        {"repository": "https://example.invalid/starter.git", "commit": "main"},
        {
            "repository": "https://example.invalid/starter.git",
            "commit": "a" * 40,
            "tag": "main",
        },
        {
            "repository": "https://example.invalid/starter.git",
            "tag": "refs/tags/release",
        },
    ],
)
def test_source_plan_requires_repository_and_immutable_pin(update, source_spec):
    _, _, plan = update
    plan["starter_source"] = source_spec
    result = prepare(update, status=1)
    assert result["status"] == "INCOMPLETE" and "starter_source" in result["error"]


@pytest.mark.parametrize("replacement_kind", ["commit", "blob"])
def test_inherited_git_directory_cannot_substitute_a_local_distribution(
    update, monkeypatch, replacement_kind
):
    consumer, source, plan = update
    # A local replacement is self-consistent, but the served tag still names the
    # genuine source. Only the latter may authorize this consumer's update.
    git(consumer, "add", ".")
    git(consumer, "commit", "--quiet", "-m", "genuine update")
    managed = source / MANAGED
    managed.write_bytes(managed.read_bytes() + b"\n# Local substitute\n")
    refresh(source)
    git(source, "add", ".")
    git(source, "commit", "--quiet", "-m", "local substitute distribution")
    replacement = git(source, "rev-parse", "HEAD")
    run(sys.executable, "engineering", "update", str(consumer), "--apply", cwd=source)
    git(consumer, "fetch", "--quiet", str(source), "main")
    pin = plan["starter_source"]["commit"]
    if replacement_kind == "commit":
        git(consumer, "replace", pin, replacement)
    else:
        for name in (MANAGED, MANIFEST):
            original_blob = git(source, "rev-parse", f"{pin}:{name}")
            replacement_blob = git(source, "rev-parse", f"{replacement}:{name}")
            git(consumer, "replace", original_blob, replacement_blob)
    monkeypatch.setenv("GIT_DIR", str(consumer / ".git"))
    result = prepare(update, status=1)
    assert "Proposed manifest differs from pinned starter source" in result["error"]
