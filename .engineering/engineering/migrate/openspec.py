"""Extract legacy evidence without inventing architecture or implementing tasks."""

import re
from pathlib import Path

from ..source import git
from .common import Migration, begin, finish, tree
from .wiring import cleanup

REPORT = ".engineering/migrations/openspec-migration-report.md"


def task_status(raw: bytes) -> str:
    """Classify only checkbox evidence; completion never proves merge/archive."""
    checks = re.findall(rb"(?m)^\s*-\s*\[([ xX])\]", raw)
    if not checks:
        return "UNKNOWN"
    done = sum(item.lower() == b"x" for item in checks)
    if done == len(checks):
        return "UNKNOWN (all tasks checked; merge not inferred)"
    return "PARTIALLY_IMPLEMENTED" if done else "PLANNING"


def package(slug: str, sources: dict[str, bytes]) -> bytes:
    """Preserve source sections verbatim, labelling unresolved interpretation."""
    status = task_status(sources.get(f"openspec/changes/{slug}/tasks.md", b""))
    lines = [
        f"# Legacy OpenSpec Migration: {slug}",
        "",
        "## Status",
        "Unmigrated / Requires review",
        f"Evidence classification: {status}",
        "",
        "## Original sources",
    ]
    lines += [f"- `{name}`" for name in sources]
    roles = {
        "Original intent": ("intent.md", "proposal.md"),
        "Decisions already made": ("design.md", "program-design.md"),
        "Known unresolved questions": (),
        "Existing design constraints": (),
        "Existing task status": ("tasks.md",),
        "Existing behavioral requirements": ("spec.md",),
    }
    for title, names in roles.items():
        lines += ["", f"## {title}"]
        matching = [
            (name, raw) for name, raw in sources.items() if Path(name).name in names
        ]
        if not matching:
            lines += ["Not inferred. Review the original sources and current code."]
        for name, raw in matching:
            lines += [
                "",
                f"### Source: {name}",
                "",
                raw.decode("utf-8", errors="replace"),
            ]
    lines += [
        "",
        "## Suggested next action",
        "Run /grill-with-docs on this package. For architectural uncertainty use /wayfinder; once decisions are resolved use /to-spec, then /to-tickets and /implement. A human may instead abandon/archive the work. No tasks have been implemented or published by migration.",
        "",
        "This is a migration aid, not an approved spec. Complete originals remain in the snapshot or recorded Git commit.",
        "",
    ]
    return "\n".join(lines).encode()


def extract(plan: Migration, policy: str) -> dict[str, bytes]:
    """Scan legacy source structure and stage candidate docs plus complete history."""
    sources = tree(plan.root, "openspec")
    canonical = {
        name: raw
        for name, raw in sources.items()
        if name.startswith("openspec/specs/") and name.endswith("/spec.md")
    }
    active: dict[str, dict[str, bytes]] = {}
    archived = set()
    for name, raw in sources.items():
        parts = Path(name).parts
        if len(parts) > 3 and parts[1] == "changes":
            if parts[2] == "archive":
                if len(parts) > 4:
                    archived.add(parts[3])
            else:
                active.setdefault(parts[2], {})[name] = raw
    for slug, files in sorted(active.items()):
        plan.add(f"docs/migrations/openspec/{slug}.md", package(slug, files))
    if canonical:
        lines = [
            "# Legacy context candidates — requires review",
            "",
            "These are unclassified source excerpts, not current behavior documentation. Retain only durable product/domain context that cannot be inferred from code. Promote clear architectural decisions to docs/adr/ after review; deduplicate existing ADRs. Delete this candidate once reconciled.",
            "",
        ]
        for name, raw in canonical.items():
            lines += [
                f"## Original source: {name}",
                "",
                raw.decode("utf-8", errors="replace"),
                "",
            ]
        plan.add(
            "docs/context/legacy-openspec-candidates.md", "\n".join(lines).encode()
        )
    wiring = tree(plan.root, ".claude/commands/opsx")
    skills = plan.root / ".claude/skills"
    if skills.is_dir():
        for path in sorted(skills.glob("openspec-*")):
            wiring.update(tree(plan.root, path.relative_to(plan.root).as_posix()))
    rewrites = cleanup(plan)
    all_sources = {**sources, **wiring, **rewrites}
    if not all_sources:
        plan.notes.append("No OpenSpec source or project wiring found.")
        return {}
    if policy == "git-only":
        if not plan.head:
            plan.conflicts.append(
                "migration.history: git-only requires a recorded HEAD"
            )
        else:
            for name, raw in all_sources.items():
                try:
                    matches = git(plan.root, "show", f"{plan.head}:{name}") == raw
                except ValueError:
                    matches = False
                if not matches:
                    plan.conflicts.append(
                        f"migration.history: {name} is not safely preserved at HEAD"
                    )
    else:
        for name, raw in all_sources.items():
            plan.add(f".engineering/migrations/legacy-openspec/{name}", raw)
    for name in {**sources, **wiring}:
        plan.add(name, None)
    existing_adrs = tree(plan.root, "docs/adr")
    summary = f"Canonical capabilities found: {len(canonical)}\nActive changes found: {len(active)}\nArchived changes found: {len(archived)}\nADRs recovered: 0\nContext documents proposed: {int(bool(canonical))}"
    unknown = [
        name
        for name in sources
        if name not in canonical and not name.startswith("openspec/changes/")
    ]
    report = f"""# OpenSpec Migration Report

## Summary
{summary}

## Preserved
History policy: {policy}. Recovery/source commit: {plan.head or "uncommitted"}.
Existing ADRs preserved unchanged: {len(existing_adrs)}. No semantic ADRs manufactured.
All original bytes are preserved in the snapshot or verified Git history.

## Converted
Active changes become review packages; canonical sources become one context candidate.

## Active changes requiring human decision
{chr(10).join("- " + slug + ": " + task_status(files.get(f"openspec/changes/{slug}/tasks.md", b"")) for slug, files in sorted(active.items())) or "None."}

## Not migrated
Custom/unclassified files retained as source evidence:
{chr(10).join("- " + name for name in unknown) or "None."}
Archived records are not promoted into active documentation.

## Removed dependencies/configuration
OpenSpec source/config, project-generated commands/skills, explicit instruction markers, and direct npm dependencies listed in metadata.
Global tools remain untouched. Use legacy-starter migration to replace starter-owned instructions and lifecycle wiring; reconcile unrelated custom references manually.

## Follow-up commands
engineering migrate legacy-starter --plan
/grill-with-docs docs/migrations/openspec/<slug>.md
/wayfinder (only for unresolved large architectural questions)
/to-spec → /to-tickets → /implement
engineering doctor
make check
"""
    plan.add(REPORT, report.encode())
    plan.notes.append(summary)
    return all_sources


def plan(root: Path, policy: str = "snapshot") -> Migration:
    """Build an idempotent read-only extraction plan."""
    result, completed = begin(root, "openspec")
    if completed:
        return result
    sources = extract(result, policy)
    if sources:
        finish(result, sources)
    return result
