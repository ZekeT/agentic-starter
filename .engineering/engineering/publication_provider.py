"""Provider creation and read-only reconciliation for publication retries."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any  # Provider and evidence JSON have heterogeneous values.

from .ownership import encoded, json_object
from .source import git


def body(plan: dict[str, Any], data: dict[str, Any]) -> str:
    """Carry human-useful scope, observed checks, independent evidence and gaps."""
    lines = [
        plan["summary"],
        "",
        "## Scope",
        *[f"- `{p}`" for p in data["inputs"]["plan"]["paths"]],
        "",
        "## Verification",
    ]
    lines += [
        f"- `{' '.join(c['command'])}`: exit {c['exit_code']}" for c in data["checks"]
    ]
    for role, report in data["reports"].items():
        lines += [f"- {role}: {report['verdict']} — {report['summary']}"]
        lines += [f"  - Finding: {finding}" for finding in report["findings"]]
        lines += [f"  - Not covered: {gap}" for gap in report["coverage_gaps"]]
    return "\n".join(lines) + "\n"


def create_pr(root: Path, plan: dict[str, Any], data: dict[str, Any]) -> str:
    """Invoke actual provider creation; custom adapters return a JSON URL receipt."""
    with tempfile.TemporaryDirectory(prefix="engineering-pr-") as folder:
        description = Path(folder) / "body.md"
        description.write_text(body(plan, data))
        provider = plan["provider"]
        if provider == "github":
            command = [
                "gh",
                "pr",
                "create",
                "--repo",
                plan["remote_url"],
                "--head",
                plan["branch"],
                "--base",
                plan["base"],
                "--title",
                plan["title"],
                "--body-file",
                str(description),
            ]
        elif provider == "gitlab":
            command = [
                "glab",
                "mr",
                "create",
                "--repo",
                plan["remote_url"],
                "--source-branch",
                plan["branch"],
                "--target-branch",
                plan["base"],
                "--title",
                plan["title"],
                "--description",
                description.read_text(),
                "--yes",
            ]
        else:
            request = Path(folder) / "request.json"
            request.write_bytes(
                encoded(
                    {
                        **plan,
                        "action": "create",
                        "body_file": str(description),
                        "head": git(root, "rev-parse", "HEAD").decode().strip(),
                    }
                )
            )
            command = [*provider, "--request", str(request)]
        proc = subprocess.run(
            command, cwd=root, capture_output=True, text=True, check=True
        )
        url = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
        if isinstance(provider, list):
            url = json_object(proc.stdout.encode()).get("url", "")
        return validate_url(url)


def validate_url(url: Any) -> str:
    """Reject missing or malformed provider receipts, whose creation is uncertain."""
    if (
        not isinstance(url, str)
        or not url.startswith(("https://", "http://"))
        or any(char.isspace() for char in url)
    ):
        raise ValueError(
            "Provider returned no valid PR/MR URL; inspect provider before retry"
        )
    return url


def find_pr(root: Path, plan: dict[str, Any]) -> str | None:
    """Require a definitive lookup before creation, including after lost responses."""
    provider = plan["provider"]
    head = git(root, "rev-parse", "HEAD").decode().strip()
    with tempfile.TemporaryDirectory(prefix="engineering-pr-lookup-") as folder:
        if provider == "github":
            command = [
                "gh",
                "pr",
                "list",
                "--repo",
                plan["remote_url"],
                "--head",
                plan["branch"],
                "--base",
                plan["base"],
                "--state",
                "all",
                "--limit",
                "100",
                "--json",
                "url,headRefOid,state,isCrossRepository",
            ]
        elif provider == "gitlab":
            command = [
                "glab",
                "mr",
                "list",
                "--repo",
                plan["remote_url"],
                "--source-branch",
                plan["branch"],
                "--target-branch",
                plan["base"],
                "--all",
                "--per-page",
                "100",
                "--output",
                "json",
            ]
        else:
            request = Path(folder) / "request.json"
            request.write_bytes(encoded({**plan, "action": "lookup", "head": head}))
            command = [*provider, "--request", str(request)]
        proc = subprocess.run(
            command, cwd=root, capture_output=True, text=True, check=True
        )
        value = json.loads(proc.stdout)
    if isinstance(provider, list):
        if value == {"url": None}:
            return None
        matches = [value]
    else:
        if not isinstance(value, list) or not all(isinstance(p, dict) for p in value):
            raise ValueError("Malformed provider lookup; inspect provider before retry")
        if len(value) >= 100:
            raise ValueError("Truncated provider lookup; inspect provider before retry")
        if provider == "github":
            matches = [
                {
                    "url": p.get("url"),
                    "head": p.get("headRefOid"),
                    "state": p.get("state"),
                }
                for p in value
                if p.get("isCrossRepository") is False
            ]
            if any(not isinstance(p.get("isCrossRepository"), bool) for p in value):
                raise ValueError("Provider lookup missing repository identity")
        else:
            if any(
                not p.get("source_project_id") or not p.get("target_project_id")
                for p in value
            ):
                raise ValueError("Provider lookup missing repository identity")
            matches = [
                {"url": p.get("web_url"), "head": p.get("sha"), "state": p.get("state")}
                for p in value
                if p["source_project_id"] == p["target_project_id"]
            ]
    if not matches:
        return None
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise ValueError("Ambiguous provider lookup; inspect matching PRs before retry")
    match = matches[0]
    if match.get("head") != head or match.get("state") not in (
        "OPEN",
        "opened",
        "open",
    ):
        raise ValueError(
            "Existing PR/MR has different content or is closed/merged; inspect provider"
        )
    return validate_url(match.get("url"))
