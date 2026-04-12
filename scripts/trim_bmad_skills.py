#!/usr/bin/env python3
"""
scripts/trim_bmad_skills.py — remove non-core bmad- skills from .claude/skills/

Keeps only the 7 skills that map directly to the Agentic Engineering guide's
5-step BMAD pipeline. Everything else with a bmad- prefix is removed.

Source: Agentic Engineering guide (Layer 2: Planning with BMAD)
  Step 1: /plan        → bmad-agent-analyst
  Step 2: /prd         → bmad-agent-pm + bmad-create-prd
  Step 3: /architecture → bmad-agent-architect + bmad-create-architecture
  Step 4: /gate-check  → bmad-check-implementation-readiness
  Step 5: /sprint-plan → bmad-create-epics-and-stories

Usage:
    python scripts/trim_bmad_skills.py           # dry-run (safe, no changes)
    python scripts/trim_bmad_skills.py --apply   # actually delete
    python scripts/trim_bmad_skills.py --audit   # show keep/remove table only
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / ".claude" / "skills"

# Exactly the 7 skills the Agentic Engineering guide's pipeline needs.
# Nothing more — this is intentionally lean.
KEEP: set[str] = {
    "bmad-agent-analyst",            # /plan  — Analyst agent
    "bmad-agent-pm",                 # /prd   — PM agent
    "bmad-agent-architect",          # /architecture — Architect agent
    "bmad-create-prd",               # generates docs/prd.md
    "bmad-create-architecture",      # generates docs/architecture.md
    "bmad-create-epics-and-stories", # /sprint-planning — story breakdown
    "bmad-check-implementation-readiness",  # /gate-check — PRD↔arch validation
}


def get_bmad_skills() -> list[Path]:
    """Return all bmad- prefixed skill folders, sorted."""
    if not SKILLS_DIR.exists():
        return []
    return sorted(
        p for p in SKILLS_DIR.iterdir()
        if p.is_dir() and p.name.startswith("bmad-")
    )


def partition(skills: list[Path]) -> tuple[list[Path], list[Path]]:
    """Split into (keep, remove) lists."""
    keep = [s for s in skills if s.name in KEEP]
    remove = [s for s in skills if s.name not in KEEP]
    return keep, remove


def print_table(keep: list[Path], remove: list[Path]) -> None:
    """Print a clear keep/remove summary."""
    col = 45

    print("\n=== BMAD Skill Audit (Agentic Engineering guide — lean pipeline) ===\n")

    print(f"  {'KEEP':<{col}}  Role")
    print(f"  {'-' * col}  {'-' * 35}")
    roles = {
        "bmad-agent-analyst":                   "/plan → Analyst",
        "bmad-agent-pm":                        "/prd → PM",
        "bmad-agent-architect":                 "/architecture → Architect",
        "bmad-create-prd":                      "generates docs/prd.md",
        "bmad-create-architecture":             "generates docs/architecture.md",
        "bmad-create-epics-and-stories":        "/sprint-planning → story breakdown",
        "bmad-check-implementation-readiness":  "/gate-check → PRD↔arch validation",
    }
    for p in keep:
        print(f"  {p.name:<{col}}  {roles.get(p.name, '')}")

    if not remove:
        print("\n  Nothing to remove — already lean.\n")
        return

    print(f"\n  {'REMOVE':<{col}}  Reason")
    print(f"  {'-' * col}  {'-' * 35}")
    for p in remove:
        print(f"  {p.name:<{col}}  not in guide pipeline")

    print(f"\n  Total: {len(keep)} keep, {len(remove)} remove\n")


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Trim bmad- skills to the lean Agentic Engineering guide pipeline."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the non-core skills (default is dry-run).",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Print the keep/remove table and exit — no deletions, no prompts.",
    )
    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        print(f"Skills directory not found: {SKILLS_DIR}")
        print("Run from the project root, or check that .claude/skills/ exists.")
        return

    skills = get_bmad_skills()
    if not skills:
        print("No bmad- skills found in .claude/skills/")
        return

    keep, remove = partition(skills)
    print_table(keep, remove)

    if args.audit or not remove:
        return

    if not args.apply:
        # Dry-run — show what would happen, prompt to confirm
        print("  Dry-run. To apply, run:")
        print("    python scripts/trim_bmad_skills.py --apply\n")
        return

    # --apply: confirm then delete
    print("  About to permanently delete the REMOVE skills listed above.")
    answer = input("  Type 'yes' to confirm: ").strip().lower()
    if answer != "yes":
        print("  Aborted.")
        return

    removed = []
    errors = []
    for p in remove:
        try:
            shutil.rmtree(p)
            removed.append(p.name)
        except Exception as e:
            errors.append((p.name, str(e)))

    print()
    for name in removed:
        print(f"  deleted  {name}")
    for name, err in errors:
        print(f"  ERROR    {name}: {err}")

    print(f"\n  Done. {len(removed)} skills removed, {len(errors)} errors.")
    if errors:
        print("  Check the errors above — those skills may need manual removal.")


if __name__ == "__main__":
    main()
