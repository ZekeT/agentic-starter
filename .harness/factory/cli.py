"""Command-line boundary for deterministic factory tooling."""

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
        description="Repository-local factory tooling (Python 3.12+)"
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Diagnose installation health offline")
    for operation in ("adopt", "update"):
        lifecycle = sub.add_parser(
            operation, help="Plan safe installation changes; apply explicitly"
        )
        lifecycle.add_argument("target", type=Path)
        lifecycle.add_argument("--template", type=Path)
        lifecycle.add_argument("--apply", action="store_true")
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
        if args.command in {"adopt", "update"}:
            from .adoption import plan_installation
            from .apply import apply_plan, show_plan

            plan = plan_installation(args.template or root, args.target, args.command)
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
        subprocess.CalledProcessError,
    ) as exc:
        print(f"✗ {args.command}: {exc}", file=sys.stderr)
        return 1


def legacy_main(template: Path, operation: str, argv: list[str] | None = None) -> int:
    """Translate legacy argument forms without a second mutation implementation."""
    parser = argparse.ArgumentParser(
        description="Deprecated adapter to factory " + operation
    )
    parser.add_argument("target", type=Path)
    parser.add_argument("--template", type=Path, default=template)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry", "--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.force:
        print(
            "--force overwrite is unsupported; resolve conflicts explicitly. No files written.",
            file=sys.stderr,
        )
        return 1
    print(
        f"Deprecated entry point: use factory {operation}; default is now a read-only plan. Use --apply explicitly."
    )
    translated = [operation, str(args.target), "--template", str(args.template)]
    if args.apply:
        translated.append("--apply")
    return main(translated)
