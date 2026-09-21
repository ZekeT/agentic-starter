"""Local verification evidence: prepare, check, record independent reports, reuse."""

import argparse
import json
import re
from pathlib import Path
from typing import Any

from .config import safe_path
from .ownership import encoded, json_object
from .source import git
from .transaction import write_files
from .verification_snapshot import (
    STATE,
    read_plan,
    run_command,
    snapshot,
    strings,
    validate_plan,
)


def add_parser(sub: Any) -> None:
    """Expose one small command family without a new application lifecycle."""
    parser = sub.add_parser(
        "verify", help="Prepare and reuse independent verification evidence"
    )
    parser.add_argument("operation", choices=["prepare", "check", "record", "status"])
    parser.add_argument("--change", required=True, help="Local evidence identifier")
    parser.add_argument("--plan", help="Repository-relative JSON plan (prepare only)")
    parser.add_argument("--snapshot", help="Prepared identity (check only)")
    parser.add_argument("--report", help="Independent JSON report (record only)")


def location(root: Path, change: str) -> str:
    """Require safe, ignored, untracked local evidence storage."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", change):
        raise ValueError("change must be a lowercase slug (maximum 80 characters)")
    name = f"{STATE}/{change}.json"
    safe_path(root, name)
    if git(root, "ls-files", "--", STATE):
        raise ValueError("Verification records must not be tracked")
    try:
        git(root, "check-ignore", "--quiet", "--", name)
    except ValueError as exc:
        raise ValueError(f"Ignore /{STATE}/ before preparing evidence") from exc
    return name


def read_record(root: Path, name: str) -> dict[str, Any]:
    """Refuse unsupported or incomplete record structure instead of assuming proof."""
    data = json_object(safe_path(root, name).read_bytes())
    if (
        type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
        or not isinstance(data.get("inputs"), dict)
        or not isinstance(data.get("reports"), dict)
        or not isinstance(data.get("checks"), list)
        or not isinstance(data.get("snapshot"), str)
    ):
        raise ValueError("Invalid or unsupported verification record; prepare again")
    plan = data["inputs"].get("plan")
    if not isinstance(plan, dict):
        raise ValueError("Invalid stored plan")
    validate_plan(root, plan)
    for role, report in data["reports"].items():
        if not isinstance(report, dict):
            raise ValueError("Invalid stored report")
        validate_report(report, data["snapshot"])
        if report["role"] != role:
            raise ValueError("Stored reviewer role differs from report")
    for item in data["checks"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"command", "exit_code", "stdout", "stderr"}
            or type(item["exit_code"]) is not int
            or not isinstance(item["stdout"], str)
            or not isinstance(item["stderr"], str)
        ):
            raise ValueError("Invalid recorded command result")
        strings(item["command"], "recorded command")
    return data


def outcome(data: dict[str, Any]) -> dict[str, Any]:
    """Summarize completeness without equating recorded proof with acceptance."""
    roles = ["maintainability", "behavioral"]
    if data["inputs"]["plan"]["security_required"]:
        roles.append("security")
    missing = [role for role in roles if role not in data["reports"]]
    checks = data["checks"]
    if [item["command"] for item in checks] != data["inputs"]["plan"]["checks"]:
        missing.append("authoritative checks")
    failed = any(item["exit_code"] != 0 for item in checks)
    failed |= any(report["verdict"] != "PASS" for report in data["reports"].values())
    status = "FAIL" if failed else "INCOMPLETE" if missing else "PASS"
    return {
        "status": status,
        "snapshot": data["snapshot"],
        "missing": missing,
        "reports": data["reports"],
        "checks": checks,
        "handoff": "Fresh read-only reviewer: inspect the plan requirement and actual scope; record missing roles. No implementer self-review."
        if missing
        else "",
        "meaning": "Recorded verification evidence only; not human acceptance or publication authorization.",
    }


def validate_report(report: dict[str, Any], token: str) -> None:
    """Validate explicit independent attestations; do not claim identity authentication."""
    if set(report) != {
        "snapshot",
        "role",
        "reviewer",
        "independent",
        "verdict",
        "summary",
        "findings",
        "coverage_gaps",
    }:
        raise ValueError(
            "Report fields: snapshot, role, reviewer, independent, verdict, summary, findings, coverage_gaps"
        )
    if report["snapshot"] != token:
        raise ValueError("STALE report: snapshot differs; reverify current content")
    if report["role"] not in ("maintainability", "behavioral", "security"):
        raise ValueError("Unknown reviewer role")
    if report["independent"] is not True:
        raise ValueError(
            "Independent review required; implementer self-review is not proof"
        )
    if report["verdict"] not in ("PASS", "FAIL", "CONCERNS"):
        raise ValueError("Report verdict must be PASS, FAIL or CONCERNS")
    for field in ("summary", "reviewer"):
        if not isinstance(report[field], str) or not report[field].strip():
            raise ValueError(f"Report {field} must be nonempty text")
    for field in ("findings", "coverage_gaps"):
        strings(report[field], field, empty=True)


def operate(root: Path, args: argparse.Namespace) -> int:
    """Perform one evidence operation and emit a readable JSON result."""
    allowed = {
        "prepare": "plan",
        "check": "snapshot",
        "record": "report",
        "status": None,
    }
    for field in ("plan", "snapshot", "report"):
        if bool(getattr(args, field)) != (allowed[args.operation] == field):
            raise ValueError(
                f"{args.operation}: requires only --{allowed[args.operation]}"
                if allowed[args.operation]
                else "status accepts only --change"
            )
    name = location(root, args.change)
    path = safe_path(root, name)
    if args.operation == "prepare":
        plan = read_plan(root, args.plan)
        token, inputs = snapshot(root, plan)
        data: dict[str, Any] = {
            "schema_version": 1,
            "snapshot": token,
            "inputs": inputs,
            "checks": [],
            "reports": {},
        }
        if path.exists():
            previous = read_record(root, name)
            if previous["snapshot"] == token and previous["inputs"] == inputs:
                data = previous
        write_files(root, {name: encoded(data)})
    else:
        if not path.exists():
            print(
                json.dumps(
                    {
                        "status": "INCOMPLETE",
                        "missing": ["prepare and independent verification"],
                    }
                )
            )
            return 1
        data = read_record(root, name)
        token, inputs = snapshot(root, data["inputs"]["plan"])
        if token != data["snapshot"] or inputs != data["inputs"]:
            print(
                json.dumps(
                    {
                        "status": "STALE",
                        "handoff": "Prepare current inputs and obtain fresh independent verification.",
                    }
                )
            )
            return 1
        if args.operation == "check":
            if args.snapshot != token:
                raise ValueError("STALE check request: obtain the current snapshot")
            # Clear old proof before running: interrupted or failed reruns cannot reuse PASS.
            data["checks"] = []
            data["reports"].pop("behavioral", None)
            write_files(root, {name: encoded(data)})
            for command in data["inputs"]["plan"]["checks"]:
                data["checks"].append(run_command(root, command, timeout=900))
            after, _ = snapshot(root, data["inputs"]["plan"])
            if after != token:
                raise ValueError(
                    "STALE: checks mutated verification inputs; prepare and reverify"
                )
            write_files(root, {name: encoded(data)})
        elif args.operation == "record":
            report = json_object(safe_path(root, args.report).read_bytes())
            validate_report(report, token)
            if report["role"] == "behavioral" and report["verdict"] == "PASS":
                if (
                    not data["checks"]
                    or any(c["exit_code"] for c in data["checks"])
                    or [c["command"] for c in data["checks"]]
                    != data["inputs"]["plan"]["checks"]
                ):
                    raise ValueError(
                        "Behavioral PASS requires successful recorded authoritative checks"
                    )
            data["reports"][report["role"]] = report
            write_files(root, {name: encoded(data)})
    result = outcome(data)
    print(json.dumps(result, indent=2))
    if args.operation == "status":
        return int(result["status"] != "PASS")
    if args.operation == "check":
        return int(any(item["exit_code"] for item in data["checks"]))
    return 0
