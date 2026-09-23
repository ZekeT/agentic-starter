"""Check provider CLI lookup contracts with fake hosting executables."""

import json
import os
import sys

import pytest

from .test_publication import STATE, publish, review
from .test_publication import hosting as hosting
from .test_verification import git
from .test_verification import repo as repo

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("provider,tool", [("github", "gh"), ("gitlab", "glab")])
@pytest.mark.parametrize("existing", [False, True])
def test_builtin_provider_reconciles_uncertain_create(
    repo, hosting, monkeypatch, provider, tool, existing
):
    review(repo, hosting, provider=provider)
    publish(repo, "run", "--authorize", "push")
    head = git(repo, "rev-parse", "HEAD")
    state = repo / STATE
    tools = state / "bin"
    tools.mkdir()
    receipt = state / "provider.json"
    item = (
        {
            "url": "https://hosting.invalid/pull/1",
            "headRefOid": head,
            "state": "OPEN",
            "isCrossRepository": False,
        }
        if provider == "github"
        else {
            "web_url": "https://hosting.invalid/pull/1",
            "sha": head,
            "state": "opened",
            "source_project_id": 1,
            "target_project_id": 1,
        }
    )
    if existing:
        receipt.write_text(json.dumps([item]))
    executable = tools / tool
    executable.write_text(
        f"#!{sys.executable}\nimport json, pathlib, sys\n"
        f"receipt = pathlib.Path({str(receipt)!r})\n"
        f"calls = pathlib.Path({str(state / 'provider-calls')!r})\n"
        "with calls.open('a') as f: f.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if sys.argv[2] == 'list':\n"
        "    print(receipt.read_text() if receipt.exists() else '[]')\n"
        "else:\n"
        f"    receipt.write_text({json.dumps([item])!r})\n"
        "    sys.exit(7)\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tools) + ":" + os.environ["PATH"])
    result = publish(repo, "run", "--authorize", "pr", status=0 if existing else 1)
    if not existing:
        assert result["failed"] == "pr creation"
    assert publish(repo, "run")["url"] == "https://hosting.invalid/pull/1"
    calls = [
        json.loads(line) for line in (state / "provider-calls").read_text().splitlines()
    ]
    assert sum(c[1] == "create" for c in calls) == (0 if existing else 1)
    for call in calls:
        assert call[call.index("--repo") + 1] == str(hosting[0])
        if call[1] == "list":
            source, target = (
                ("--head", "--base")
                if provider == "github"
                else ("--source-branch", "--target-branch")
            )
            assert call[call.index(source) + 1] == "feature"
            assert call[call.index(target) + 1] == "main"
