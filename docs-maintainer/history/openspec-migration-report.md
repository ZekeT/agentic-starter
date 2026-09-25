# OpenSpec Migration Report

## Summary
Canonical capabilities found: 3
Active changes found: 2
Archived changes found: 0
ADRs recovered: 0
Context documents proposed: 1

## Preserved
History policy: git-only. Recovery/source commit: 154425666f98b6045f9cad1d3e9c7ca6eef4dc64.
Existing ADRs preserved unchanged: 1. No semantic ADRs manufactured.
All original bytes are preserved in the snapshot or verified Git history.

## Converted
Active changes become review packages; canonical sources become one context candidate.

## Active changes requiring human decision
- factory-phase2: UNKNOWN (all tasks checked; merge not inferred)
- software-factory: UNKNOWN (all tasks checked; merge not inferred)

## Not migrated
Custom/unclassified files retained as source evidence:
- openspec/config.yaml
- openspec/specs/.gitkeep
Archived records are not promoted into active documentation.

## Removed dependencies/configuration
OpenSpec source/config and project-generated commands/skills listed in metadata.
Global tools remain untouched. Use legacy-starter migration to replace starter-owned instructions and lifecycle wiring; reconcile unrelated custom references manually.

## Follow-up commands
engineering migrate legacy-starter --plan
/grill-with-docs docs/migrations/openspec/<slug>.md
/wayfinder (only for unresolved large architectural questions)
/to-spec → /to-tickets → /implement
engineering doctor
make check
