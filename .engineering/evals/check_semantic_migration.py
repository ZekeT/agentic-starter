"""Check explicit migration instruction boundaries; this does not run a model."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".claude/skills/migrate-from-openspec/SKILL.md"
REQUIRED = (
    "OpenSpec canonical prose is not automatically correct",
    "current code and current tests",
    "Do not create one new file per old spec",
    "KEEP_AS_CONTEXT",
    "KEEP_AS_ADR",
    "KEEP_AS_FEATURE_DOC",
    "REPRESENTED_BY_CODE_OR_TESTS_DROP",
    "OBSOLETE_DROP",
    "PLANNING",
    "DECIDED_NOT_IMPLEMENTED",
    "PARTIALLY_IMPLEMENTED",
    "IMPLEMENTED_NOT_CLOSED",
    "UNKNOWN",
    "`OBSOLETE`",
    "CONFLICT_REQUIRES_HUMAN",
    "UNCERTAIN_REQUIRES_HUMAN",
    "Do not implement unfinished changes",
    "/wayfinder",
    "/to-spec",
    "/to-tickets",
    "human acceptance",
    "temporary migration state",
    "application-manifest.md",
    "arbitrary OpenSpec projects",
    "Task checkboxes are historical claims, not evidence of implementation",
    "Do not emulate finalization",
    "docs/agents/issue-tracker.md",
    "useful source references",
    "complete diff and manifest digest",
    "migration accepted from migration closed",
    "cleanup pending",
    "--accept --apply",
    "--cleanup --plan",
    "--approved-cleanup",
    "Changed artifacts must be preserved",
    "Pending cleanup never blocks ordinary development",
    "A generated digest is not human removal authorization",
)


def main() -> None:
    """Fail if the project-owned skill loses an explicit safety boundary."""
    text = SKILL.read_text()
    missing = [phrase for phrase in REQUIRED if phrase not in text]
    if missing:
        raise SystemExit(f"Missing semantic boundaries: {missing}")
    print("Semantic boundary instructions present (static only).")


if __name__ == "__main__":
    main()
