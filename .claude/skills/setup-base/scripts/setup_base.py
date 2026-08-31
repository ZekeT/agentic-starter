"""
setup_base.py

Idempotent scaffolder for the agentic engineering project layout.
Creates the story kanban folders, docs/, and a starter CLAUDE.md if missing.

Usage:
    python setup_base.py           # scaffold missing pieces
    python setup_base.py --dry-run # preview only, no changes
"""

import argparse
from pathlib import Path

# ── Folders the change loop needs ────────────────────────────────────────────
# openspec/ itself is created by `openspec init`; these are the two dirs that
# are empty on a fresh init and would otherwise be lost by git.
LOOP_DIRS = [
    "openspec/specs",
    "openspec/changes/archive",
    "docs/decisions",
]
DOCS_DIR = "docs"

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
- What it does today:   [openspec/specs/](openspec/specs/)  (`openspec list --specs`)
- Product intent:       [docs/product.md](docs/product.md)
- System shape:         [docs/architecture.md](docs/architecture.md)
- Decisions:            [docs/decisions/](docs/decisions/)

## Git strategy
- Branch naming: `feat/<change-slug>-g<N>` (one task group per branch)
- Commits: conventional commits, e.g. `feat(auth): add login endpoint`
- PRs: one task group per PR

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


def create_structure(root: Path, dry_run: bool) -> None:
    log("Creating kanban folders...", dry_run)
    for d in LOOP_DIRS:
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

    # 1. Folder structure
    create_structure(root, dry_run)

    # 2. CLAUDE.md
    create_claude_md(root, dry_run)

    print("\nDone." if not dry_run else "\nDry run complete — no files were changed.")
    print("Next: run the scanner skill to verify the project is clean.")


if __name__ == "__main__":
    main()
