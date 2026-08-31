#!/usr/bin/env python3
"""Update a project created from agentic-starter to the latest template.

Compares every template-owned file in the target against the starter's
template-manifest.json (see scripts/generate_template_manifest.py):

  - missing in target                → NEW: copied from the starter
  - matches the current hash         → up to date: skipped
  - matches an older pristine hash   → AUTO-UPDATE: overwritten (never edited)
  - matches nothing                  → CUSTOMIZED: flagged for a guided merge

Special cases:
  - .gitignore is never overwritten — missing template lines are appended

Run from the starter checkout against a target project:

    python setup_update.py /path/to/target --dry   # report only
    python setup_update.py /path/to/target         # apply

Stdlib-only and Python 3.9-compatible on purpose — it must run on the
system python3 of a machine that has not bootstrapped the venv yet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STARTER_DIR = Path(__file__).resolve().parents[4]
MANIFEST_NAME = "template-manifest.json"
VERSION_STAMP = ".claude/template-version.json"

# Never auto-copied even if listed in the manifest.
APPEND_ONLY = {".gitignore"}

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    """Print a green check line."""
    print(f"  {GREEN}✓{RESET}  {msg}")


def warn(msg: str) -> None:
    """Print a yellow warning line."""
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def fail(msg: str) -> None:
    """Print a red failure line."""
    print(f"  {RED}✗{RESET}  {msg}")


def info(msg: str) -> None:
    """Print a cyan info line."""
    print(f"  {CYAN}→{RESET}  {msg}")


def header(msg: str) -> None:
    """Print a bold section header."""
    print(f"\n{BOLD}{msg}{RESET}\n{'─' * 60}")


def sha256_of(path: Path) -> str:
    """Return the sha256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(starter: Path) -> dict[str, Any]:
    """Load template-manifest.json from the starter, or exit with an error."""
    manifest_path = starter / MANIFEST_NAME
    if not manifest_path.exists():
        fail(f"{MANIFEST_NAME} not found in starter: {starter}")
        info("Regenerate it there first: make manifest")
        sys.exit(1)
    return json.loads(manifest_path.read_text())  # type: ignore[no-any-return]


def read_target_version(target: Path) -> str:
    """Return the template version the target was created from, if recorded."""
    stamp = target / VERSION_STAMP
    if stamp.exists():
        try:
            return str(json.loads(stamp.read_text()).get("template_version", "unknown"))
        except json.JSONDecodeError:
            return "unknown"
    report = target / ".claude" / "migration-report.json"
    if report.exists():
        try:
            return str(json.loads(report.read_text()).get("starter_version", "unknown"))
        except json.JSONDecodeError:
            return "unknown"
    return "unknown"


def classify(rel: str, entry: dict[str, Any], target: Path) -> str:
    """Classify one manifest file against the target project.

    Args:
        rel: Path relative to the project root.
        entry: Manifest entry with "sha256" and "previous" keys.
        target: Target project root.

    Returns:
        One of "new", "current", "auto-update", "customized".
    """
    target_file = target / rel
    if not target_file.exists():
        return "new"
    digest = sha256_of(target_file)
    if digest == entry["sha256"]:
        return "current"
    if digest in entry.get("previous", []):
        return "auto-update"
    return "customized"


def merge_gitignore(starter: Path, target: Path, dry: bool) -> list[str]:
    """Append template .gitignore lines missing from the target's.

    Returns:
        The list of appended lines (empty if nothing was missing).
    """
    src = starter / ".gitignore"
    dst = target / ".gitignore"
    if not src.exists():
        return []
    template_lines = src.read_text().splitlines()
    existing = set(dst.read_text().splitlines()) if dst.exists() else set()
    added = [
        line for line in template_lines if line.strip() and line not in existing
    ]
    if added and not dry:
        prefix = "" if not dst.exists() else "\n# Appended by setup-update\n"
        with dst.open("a") as f:
            f.write(prefix + "\n".join(added) + "\n")
    return added


def write_version_stamp(target: Path, version: str, dry: bool) -> None:
    """Record which template version the target now matches."""
    if dry:
        return
    stamp = target / VERSION_STAMP
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(
        json.dumps(
            {
                "template_version": version,
                "updated_at": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
            },
            indent=2,
        )
        + "\n"
    )


def run_update(starter: Path, target: Path, dry: bool) -> dict[str, list[str]]:
    """Apply (or preview) the template update.

    Args:
        starter: Starter repo root containing the manifest and pristine files.
        target: Target project root to update.
        dry: When True, report without writing anything.

    Returns:
        Mapping of category name to the affected relative paths.
    """
    manifest = load_manifest(starter)
    results: dict[str, list[str]] = {
        "new": [],
        "current": [],
        "auto-update": [],
        "customized": [],
    }

    header("1 / TEMPLATE FILES")
    for rel, entry in sorted(manifest["files"].items()):
        if rel in APPEND_ONLY:
            continue
        src = starter / rel
        if not src.exists():
            continue  # manifest is stale for this file; regenerate it
        category = classify(rel, entry, target)
        results[category].append(rel)
        if category == "current":
            continue
        if category == "new":
            info(f"NEW         {rel}")
        elif category == "auto-update":
            ok(f"AUTO-UPDATE {rel} (pristine older version)")
        else:
            warn(f"CUSTOMIZED  {rel} — left untouched, needs guided merge")
            continue
        if not dry:
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    ok(f"{len(results['current'])} file(s) already up to date")

    header("2 / .gitignore (append-only)")
    added = merge_gitignore(starter, target, dry)
    if added:
        info(f"{len(added)} missing line(s) appended to .gitignore")
    else:
        ok(".gitignore already covers all template entries")

    return results


def print_summary(
    results: dict[str, list[str]], from_version: str, to_version: str, dry: bool
) -> None:
    """Print the final report and manual follow-up steps."""
    header("3 / SUMMARY")
    mode = "DRY RUN — nothing written" if dry else "applied"
    info(f"Template {from_version} → {to_version} ({mode})")
    ok(f"up to date: {len(results['current'])}")
    ok(f"auto-updated: {len(results['auto-update'])}")
    info(f"new files copied: {len(results['new'])}")
    if results["customized"]:
        warn(f"customized, needs guided merge: {len(results['customized'])}")
        for rel in results["customized"]:
            print(f"       - {rel}")

    header("4 / MANUAL STEPS")
    info("The manifest only tracks files that still exist, so removed and renamed")
    info("template files are never auto-deleted. Clean these up by hand:")
    print("       Removed in 1.1.0:")
    print("         .claude/commands/plan.md, prd.md, architecture.md, gate-check.md")
    print("         scripts/trim_bmad_skills.py")
    print("         _bmad/, _bmad-output/, .claude/skills/bmad-*/")
    print("       Removed in 1.3.0:")
    print("         AGENTS.md          — merged into CLAUDE.md; drop the @AGENTS.md import")
    print("         docs/local-models.md — local model profiles dropped")
    print("       Renamed in 1.3.0 (new copy already written; delete the old path):")
    print("         setup.sh                 → harness_setup.sh")
    print("         docs/SETUP.md            → docs/harness/setup.md")
    print("         docs/coding-standards.md → docs/harness/coding-standards.md")
    info("Update the global Superpowers plugin inside Claude Code:")
    print("       /plugin update superpowers@superpowers-marketplace")
    info("Then verify: run the setup-base skill (scan my project).")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Update a project copied from agentic-starter to the latest template."
    )
    parser.add_argument("target", help="Path to the target project root")
    parser.add_argument(
        "--dry", action="store_true", help="Report only — write nothing"
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        fail(f"Target is not a directory: {target}")
        sys.exit(1)
    if target == STARTER_DIR:
        fail("Target is the starter repo itself — nothing to update.")
        sys.exit(1)

    manifest = load_manifest(STARTER_DIR)
    to_version = str(manifest.get("template_version", "unknown"))
    from_version = read_target_version(target)

    print(f"\n{BOLD}Agentic Starter — Template Update{RESET}")
    print(f"Starter: {CYAN}{STARTER_DIR}{RESET} (v{to_version})")
    print(f"Target:  {CYAN}{target}{RESET} (from v{from_version})")
    if args.dry:
        print(f"Mode:    {YELLOW}DRY RUN{RESET}")

    results = run_update(STARTER_DIR, target, args.dry)
    write_version_stamp(target, to_version, args.dry)
    print_summary(results, from_version, to_version, args.dry)


if __name__ == "__main__":
    main()
