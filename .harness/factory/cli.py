"""Command-line boundary for deterministic factory tooling."""

import argparse
import sys
import tokenize
from pathlib import Path

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
    except (OSError, ValueError, tokenize.TokenError) as exc:
        print(f"✗ maintainability: {exc}", file=sys.stderr)
        return 1
