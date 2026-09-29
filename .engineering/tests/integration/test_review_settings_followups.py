"""Review settings reject typos and keep executable configuration out of prose."""

import pytest

from .test_review_tiers import CONFIG, commit_base_settings, settings_text
from .test_verification import change_plan, prepare
from .test_verification import repo as repo

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("where", ["base", "proposed"])
def test_unknown_review_keys_rejected_in_both_versions(repo, where):
    good = settings_text(["**"])
    bad = good + "typo = []\n"
    commit_base_settings(repo, bad if where == "base" else good)
    (repo / CONFIG).write_text(good if where == "base" else bad)
    change_plan(repo, paths=["app.txt", CONFIG])
    assert "unknown" in prepare(repo, status=1)["error"]


@pytest.mark.parametrize("name", [".pre-commit-config.yaml", ".envrc"])
def test_executed_configuration_is_sensitive_under_broad_docs(repo, name):
    commit_base_settings(repo, settings_text(["**"]))
    # Fixture data only; no real environment file is read or executed.
    (repo / name).write_text("# fixture\n")
    change_plan(repo, paths=["app.txt", name], tier="ordinary")
    result = prepare(repo, status=1)
    assert "sensitive" in result["error"] and name in result["error"]


@pytest.mark.parametrize(
    "name,tier",
    [
        ("docs/intro.md", "documentation"),
        ("docs/deep/intro.md", "documentation"),
        ("docs/conf.py", "ordinary"),
    ],
)
def test_markdown_default_includes_root_and_nested_prose_only(repo, name, tier):
    commit_base_settings(repo, settings_text(["docs/**/*.md"]))
    (repo / "app.txt").write_text("before\n")
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("content\n")
    change_plan(repo, paths=[name], tier=tier)
    assert prepare(repo)["floor"] == tier
