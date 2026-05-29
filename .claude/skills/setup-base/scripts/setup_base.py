"""
setup_base.py

Run once per project after installing BMAD and Superpowers.
Handles two cases:
  1. Fresh project  — creates the full folder structure
  2. Existing BMAD-only project — migrates _bmad/ output into the correct layout

Usage:
    python setup_base.py           # auto-detects mode
    python setup_base.py --dry-run # preview only, no changes
"""

import argparse
import shutil
import sys
from pathlib import Path

# ── Folders the pipeline needs ───────────────────────────────────────────────
KANBAN_DIRS = [
    "stories/draft",
    "stories/ready",
    "stories/in-progress",
    "stories/review",
    "stories/done",
]
DOCS_DIR = "docs"

# ── BMAD output locations to look for ────────────────────────────────────────
BMAD_OUTPUT_CANDIDATES = [
    "_bmad/output",
    "_bmad",
    "bmad-output",
]

# ── BMAD artefact filenames that belong in docs/ ──────────────────────────────
DOCS_ARTEFACTS = ["prd.md", "architecture.md"]

# ── CLAUDE.md template ───────────────────────────────────────────────────────
CLAUDE_MD_TEMPLATE = """\
# Project brain

Claude Code reads this file every session.
Edit it to reflect your actual conventions.

## Coding standards
- Language: Python
- Style: PEP 8, concise and readable
- Tests: pytest, write tests before implementation (Superpowers TDD)

## Architecture references
- Product requirements: [docs/prd.md](docs/prd.md)
- System design:        [docs/architecture.md](docs/architecture.md)

## Git strategy
- Branch naming: `feature/<story-id>-<short-description>`
- Commits: imperative mood, e.g. `add user auth endpoint`
- PRs: one story per PR

## Security policies
- No secrets in code — use environment variables
- Follow OWASP Top 10 for any web-facing code

## Review checklist
- [ ] Tests pass and cover the acceptance criteria
- [ ] No hardcoded secrets or credentials
- [ ] Follows conventions in this file
"""


def log(msg: str, dry_run: bool = False) -> None:
    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}{msg}")


def find_bmad_output(root: Path) -> Path | None:
    for candidate in BMAD_OUTPUT_CANDIDATES:
        p = root / candidate
        if p.exists():
            return p
    return None


def find_story_files(bmad_output: Path) -> list[Path]:
    """Return .md files that look like story files (not prd/architecture)."""
    return [
        f
        for f in bmad_output.rglob("*.md")
        if f.name not in DOCS_ARTEFACTS
        and ("story" in f.name.lower() or f.parent.name in ("stories", "epics"))
    ]


def create_structure(root: Path, dry_run: bool) -> None:
    log("Creating kanban folders...", dry_run)
    for d in KANBAN_DIRS:
        target = root / d
        if not target.exists():
            log(f"  mkdir {target.relative_to(root)}", dry_run)
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)

    docs = root / DOCS_DIR
    if not docs.exists():
        log(f"  mkdir {docs.relative_to(root)}", dry_run)
        if not dry_run:
            docs.mkdir(parents=True, exist_ok=True)


def create_claude_md(root: Path, dry_run: bool) -> None:
    target = root / "CLAUDE.md"
    if target.exists():
        log("CLAUDE.md already exists — skipping (edit it manually if needed)")
        return
    log("Creating CLAUDE.md template...", dry_run)
    if not dry_run:
        target.write_text(CLAUDE_MD_TEMPLATE)


def migrate_docs(bmad_output: Path, root: Path, dry_run: bool) -> None:
    docs = root / DOCS_DIR
    for name in DOCS_ARTEFACTS:
        src = bmad_output / name
        if not src.exists():
            # also search one level deeper
            candidates = list(bmad_output.rglob(name))
            src = candidates[0] if candidates else None
        if src and src.exists():
            dst = docs / name
            if dst.exists():
                log(f"  docs/{name} already exists — skipping")
            else:
                log(f"  copy {src.relative_to(root)} → docs/{name}", dry_run)
                if not dry_run:
                    shutil.copy2(src, dst)
        else:
            log(f"  {name} not found in BMAD output — run /prd and /architecture first")


def migrate_stories(bmad_output: Path, root: Path, dry_run: bool) -> None:
    story_files = find_story_files(bmad_output)
    if not story_files:
        log("  No story files found in BMAD output")
        return

    log(f"  Found {len(story_files)} story file(s) — moving to stories/draft/", dry_run)
    draft = root / "stories" / "draft"
    for src in story_files:
        dst = draft / src.name
        if dst.exists():
            log(f"    {src.name} already in draft/ — skipping")
        else:
            log(f"    {src.relative_to(root)} → stories/draft/{src.name}", dry_run)
            if not dry_run:
                shutil.copy2(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set up agentic engineering project structure"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing"
    )
    parser.add_argument(
        "--root", default=".", help="Project root (default: current directory)"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    dry_run = args.dry_run

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Agentic project setup")
    print(f"Root: {root}\n")

    # Detect mode
    bmad_output = find_bmad_output(root)
    if bmad_output:
        log(f"Detected existing BMAD output at: {bmad_output.relative_to(root)}")
        log("Mode: migration\n")
    else:
        log("No existing BMAD output found")
        log("Mode: fresh setup\n")

    # 1. Folder structure
    create_structure(root, dry_run)

    # 2. CLAUDE.md
    create_claude_md(root, dry_run)

    # 3. Migrate artefacts if BMAD exists
    if bmad_output:
        log("\nMigrating BMAD artefacts...")
        migrate_docs(bmad_output, root, dry_run)
        migrate_stories(bmad_output, root, dry_run)

    print("\nDone." if not dry_run else "\nDry run complete — no files were changed.")
    print("Next: run the scanner skill to verify the project is clean.")


if __name__ == "__main__":
    main()
