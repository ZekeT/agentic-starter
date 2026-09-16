"""Command-line boundary for deterministic engineering tooling."""

import argparse
import subprocess
import sys
import tokenize
from pathlib import Path

from . import doctor, graft
from .config import load_config
from .growth import check_growth


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, print actionable findings, and retain failure status."""
    parser = argparse.ArgumentParser(
        description="Repository-local engineering tooling (Python 3.12+)"
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="Print the Engineering System template version")
    sub.add_parser("doctor", help="Diagnose installation health offline")
    deps = sub.add_parser("deps", help="Manage pinned upstream capabilities")
    deps.add_argument("operation", choices=["status", "plan", "install", "update"])
    deps.add_argument("name", nargs="?")
    mode = deps.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--plan", action="store_true")
    deps.add_argument("--ref")
    deps.add_argument("--check-remote", action="store_true")
    migrate = sub.add_parser("migrate", help="Plan one-way legacy migrations")
    migrate.add_argument("migration", choices=["openspec", "legacy-starter"])
    migrate.add_argument("--target", type=Path)
    migrate.add_argument("--template", type=Path)
    mode = migrate.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    migrate.add_argument("--legacy-history", choices=["snapshot", "git-only"])
    for operation in ("adopt", "update"):
        lifecycle = sub.add_parser(
            operation, help="Plan safe installation changes; apply explicitly"
        )
        lifecycle.add_argument(
            "target", type=Path, nargs="?" if operation == "update" else None
        )
        lifecycle.add_argument("--template", type=Path)
        mode = lifecycle.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true")
        mode.add_argument("--plan", action="store_true")
    navigation = sub.add_parser("navigation", help="Pinned application-only Graft CLI")
    navigation.add_argument("arguments", nargs=argparse.REMAINDER)
    growth = sub.add_parser("maintainability", help="Check Python code-line growth")
    growth.add_argument("--base", help="Comparison branch (uses its merge base)")
    growth.add_argument(
        "--verbose", action="store_true", help="Include evidence for passing files"
    )
    growth.add_argument(
        "--all", action="store_true", help="Inspect sizes without growth history"
    )
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.command == "version":
            print((root / ".engineering/TEMPLATE_VERSION").read_text().strip())
            return 0
        if args.command == "deps":
            from .deps import operate, status

            if args.operation == "status":
                if args.apply or args.ref or args.check_remote or args.name:
                    parser.error("deps status accepts no mutation or selection flags")
                return status(root)
            if args.operation == "plan" and args.apply:
                parser.error("deps plan cannot apply")
            return operate(
                root,
                args.operation,
                args.name,
                apply=args.apply,
                ref=args.ref,
                check_remote=args.check_remote,
            )
        if args.command == "migrate":
            from .migrate.common import execute
            from .migrate.legacy import plan as legacy_plan
            from .migrate.openspec import plan as openspec_plan

            target = (args.target or root).resolve()
            template = (args.template or root).resolve()
            from .settings import load

            policy = args.legacy_history
            if policy is None:
                policy = (
                    load(target).get("migration", {}).get("legacy_history", "snapshot")
                    if (target / ".engineering/config.toml").is_file()
                    else "snapshot"
                )
            planner = (
                (lambda: openspec_plan(target, policy))
                if args.migration == "openspec"
                else (lambda: legacy_plan(template, target, policy))
            )
            return execute(planner, apply=args.apply)
        if args.command in {"adopt", "update"}:
            from .adoption import plan_installation
            from .apply import apply_plan, show_plan

            plan = plan_installation(
                args.template or root, args.target or root, args.command
            )
            show_plan(plan)
            return apply_plan(plan) if args.apply else int(bool(plan.conflicts))
        if args.command == "doctor":
            return doctor.run(root)
        if args.command == "navigation":
            return graft.run(root, args.arguments)
        config = load_config(root)
        if not config.enabled:
            print("⚠ maintainability: explicitly disabled by project configuration")
            return 0
        findings, unsupported = check_growth(
            root, config, args.base, all_files=args.all
        )
        for finding in findings:
            if finding.status == "PASS" and not args.verbose:
                continue
            counts = f"{finding.previous if finding.previous is not None else 'unknown'} → {finding.current} code lines (growth {finding.growth if finding.growth is not None else 'unknown'})"
            print(f"{finding.status} {finding.path}: {counts}\n  {finding.reason}")
        if unsupported:
            print(
                f"Scope: Python v1; {len(unsupported)} non-Python source files not analyzed."
            )
        if args.all:
            print("Size-only inspection: no growth history; oversized files warn.")
        failed = any(f.status == "FAIL" for f in findings)
        print(
            f"{'✗' if failed else '✓'} maintainability: {'pathological growth detected' if failed else 'no pathological file growth'} (warn={config.warn_file_lines}, max={config.max_file_lines}, growth={config.substantial_growth_lines})"
        )
        return int(failed)
    except (
        OSError,
        ValueError,
        tokenize.TokenError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"✗ {args.command}: {exc}", file=sys.stderr)
        return 1
