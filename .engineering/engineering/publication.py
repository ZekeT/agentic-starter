"""Publish reviewed content using current proof and explicit human authorization."""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from .config import safe_path
from .ownership import encoded, json_object
from .publication_git import commit_scope, guard_push, pushed, validate_tree
from .publication_provider import create_pr, find_pr
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


def authorize_scope(
    root: Path, change: str, plan: dict[str, Any], scope: str | None
) -> str:
    """Retain only explicitly authorized scope bound to the exact presented review."""
    name = location(root, change).removesuffix(".json") + "-publication.json"
    path = safe_path(root, name)
    if scope is None and path.exists():
        saved = json_object(path.read_bytes())
        if saved.get("review") == plan and saved.get("authorization") in (
            "commit",
            "push",
            "pr",
        ):
            return str(saved["authorization"])
    if scope is None:
        raise ValueError(
            "Missing human authorization: specify only the authorized commit/push/pr scope"
        )
    write_files(root, {name: encoded({"review": plan, "authorization": scope})})
    return scope


def operate(root: Path, args: argparse.Namespace) -> int:
    """Reconcile completed work and reuse current proof under scoped authorization."""
    completed: list[str] = []
    step = "preflight"
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
        step = "authorization"
        scope = authorize_scope(root, args.change, plan, args.authorize)
        step = "commit"
        commit_scope(root, data, plan["title"])
        completed.append("commit")
        step = "reassessment"
        reviewed(root, args.change)
        validate_tree(root, data)
        if scope in ("push", "pr"):
            step = "push"
            if not pushed(root, plan):
                guard_push(root, args.change, plan, data)
            completed.append("push")
            step = "reassessment"
            reviewed(root, args.change)
            validate_tree(root, data)
        url = None
        if scope == "pr":
            step = "pr lookup"
            url = find_pr(root, plan)
            if url is None:
                step = "pr creation"
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
                    "failed": step,
                    "error": detail,
                    "handoff": (
                        f"Resolve the {step} failure, then run engineering publish run --change {args.change}. "
                        "The retry checks current evidence and reconciles Git/provider state before changes; "
                        "stored authorization applies only to the unchanged review. "
                        "Changed content or evidence returns to verification and acceptance review. "
                        "A failed push or PR creation response may be uncertain; no automatic force-push."
                    ),
                }
            )
        )
        return 1
