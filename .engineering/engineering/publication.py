"""Publish reviewed content using current proof and explicit human authorization."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .config import safe_path
from .ownership import encoded, json_object
from .publication_git import commit_scope, guard_push, validate_tree
from .source import git
from .transaction import write_files
from .verification import location, outcome, read_record
from .verification_checkout import validate_checkout
from .verification_inputs import strings
from .verification_snapshot import snapshot


def add_parser(sub: Any) -> None:
    """Separate recording the presented review from authorized publication."""
    parser = sub.add_parser(
        "publish", help="Publish accepted, independently verified content"
    )
    parser.add_argument("operation", choices=["review", "preflight", "run"])
    parser.add_argument("--change", required=True)
    parser.add_argument(
        "--plan", help="Presented acceptance summary JSON (review only)"
    )
    parser.add_argument(
        "--authorize",
        choices=["commit", "push", "pr"],
        help="Explicit human scope; cumulative, never merge or force-push",
    )


def current(root: Path, change: str) -> dict[str, Any]:
    """Consume current evidence without rerunning checks or semantic review."""
    data = read_record(root, location(root, change))
    token, inputs = snapshot(root, data["inputs"]["plan"])
    if token != data["snapshot"] or inputs != data["inputs"]:
        raise ValueError("STALE evidence: return to verification and acceptance review")
    validate_checkout(safe_path(root, data.get("checkout", "")), inputs)
    if outcome(data)["status"] != "PASS":
        raise ValueError("Missing or failed independent proof: return to verification")
    return data


def target(root: Path, plan: dict[str, Any], data: dict[str, Any]) -> None:
    """Bind the presented target to an explicit branch, remote URL and base tip."""
    for field in ("branch", "remote", "base"):
        value = plan[field]
        if not isinstance(value, str) or not value or value.startswith("-"):
            raise ValueError(f"Invalid publication {field}")
    git(root, "check-ref-format", "--branch", plan["branch"])
    git(root, "check-ref-format", "--branch", plan["base"])
    if git(root, "symbolic-ref", "--short", "HEAD").decode().strip() != plan["branch"]:
        raise ValueError("Branch changed or detached: return to acceptance review")
    if plan["branch"] == plan["base"]:
        raise ValueError("Publish from a topic branch, not the comparison branch")
    urls = (
        git(root, "remote", "get-url", "--push", "--all", plan["remote"])
        .decode()
        .splitlines()
    )
    if urls != [plan["remote_url"]]:
        raise ValueError(
            "Remote target changed or has multiple push URLs: review target"
        )
    refs = (
        git(
            root,
            "ls-remote",
            "--heads",
            plan["remote_url"],
            f"refs/heads/{plan['base']}",
        )
        .decode()
        .split()
    )
    if not refs or refs[0] != data["inputs"]["base_tip"]:
        raise ValueError(
            "Comparison base missing or moved remotely: refresh base and reverify"
        )


def validate_review(plan: dict[str, Any]) -> None:
    """Require an explicit presented summary; flags cannot invent a missing review."""
    fields = {
        "snapshot",
        "summary",
        "blockers",
        "branch",
        "remote",
        "remote_url",
        "base",
        "provider",
        "title",
    }
    if set(plan) != fields:
        raise ValueError(f"Acceptance review requires exactly {sorted(fields)}")
    for field in fields - {"provider", "blockers"}:
        if not isinstance(plan[field], str) or not plan[field].strip():
            raise ValueError(f"Review {field} must be nonempty text")
    strings(plan["blockers"], "blockers", empty=True)
    provider = plan["provider"]
    if provider not in ("github", "gitlab"):
        strings(provider, "provider adapter argv")


def reviewed(root: Path, change: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Preflight every prerequisite before mutating Git or contacting hosting APIs."""
    name = location(root, change).removesuffix(".json") + "-review.json"
    if not safe_path(root, name).exists():
        raise ValueError("Missing acceptance review: run /review before /ship")
    plan = json_object(safe_path(root, name).read_bytes())
    validate_review(plan)
    data = current(root, change)
    if plan["snapshot"] != data["snapshot"]:
        raise ValueError("STALE acceptance review: present the current scope again")
    if plan["blockers"]:
        raise ValueError(
            "Unresolved blockers: return to human-directed review corrections"
        )
    target(root, plan, data)
    return plan, data


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
        if (
            not isinstance(url, str)
            or not url.startswith(("https://", "http://"))
            or any(c.isspace() for c in url)
        ):
            raise ValueError(
                "Provider returned no PR/MR URL; creation may have completed, inspect provider before retry"
            )
        return url


def operate(root: Path, args: argparse.Namespace) -> int:
    """Report completed steps on any failure; transport recovery is a separate slice."""
    completed: list[str] = []
    try:
        if bool(args.plan) != (args.operation == "review") or (
            args.operation != "run" and args.authorize
        ):
            raise ValueError(
                "review requires only --plan; authorization applies only to run"
            )
        if args.operation == "review":
            plan = json_object(safe_path(root, args.plan).read_bytes())
            validate_review(plan)
            data = current(root, args.change)
            if plan["snapshot"] != data["snapshot"]:
                raise ValueError(
                    "STALE presented review: inspect and present current content"
                )
            target(root, plan, data)
            name = location(root, args.change).removesuffix(".json") + "-review.json"
            write_files(root, {name: encoded(plan)})
            print(
                json.dumps(
                    {
                        "status": "REVIEWED",
                        "meaning": "Presented review recorded; not human authorization",
                        "blockers": plan["blockers"],
                    }
                )
            )
            return 0
        plan, data = reviewed(root, args.change)
        completed.append("preflight")
        if args.operation == "preflight":
            print(
                json.dumps(
                    {
                        "status": "READY",
                        "paths": data["inputs"]["plan"]["paths"],
                        "branch": plan["branch"],
                        "remote": plan["remote"],
                        "base": plan["base"],
                    }
                )
            )
            return 0
        if not args.authorize:
            raise ValueError(
                "Missing human authorization: specify only the authorized commit/push/pr scope"
            )
        commit_scope(root, data, plan["title"])
        completed.append("commit")
        reviewed(root, args.change)
        validate_tree(root, data)
        if args.authorize in ("push", "pr"):
            guard_push(root, args.change, plan, data)
            completed.append("push")
            reviewed(root, args.change)
            validate_tree(root, data)
        url = None
        if args.authorize == "pr":
            url = create_pr(root, plan, data)
            completed.append("pr")
        print(
            json.dumps(
                {
                    "status": "PUBLISHED" if url else "COMPLETE",
                    "completed": completed,
                    "url": url,
                }
            )
        )
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        detail = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            detail += ": " + str(exc.stderr or "")
        print(
            json.dumps(
                {
                    "status": "STOPPED",
                    "completed": completed,
                    "error": detail,
                    "handoff": "Inspect Git and provider state before retry; changed content returns to verification and acceptance review.",
                }
            )
        )
        return 1
