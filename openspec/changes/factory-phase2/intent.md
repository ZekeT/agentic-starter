# Intent: factory-phase2

Workflow: DEEP
Reason: Maintainability gates, source navigation, and safe adoption/update introduce cross-cutting contracts and migration boundaries.

## Classification

New capabilities `factory-maintainability`, `factory-codemap`, and
`factory-installation`. Preserve existing submission and credential-free eval
contracts and the implemented Phase 1 workflow. Its specifications remain in
`openspec/changes/software-factory/specs/`; do not archive them implicitly.

## Problem

The factory has no deterministic source-growth gate or generated navigation
index. Migration and update use separate ownership lists; the template manifest
currently includes whole project instruction, build, CI, and documentation files.
There is no shared deterministic installation health check or per-installation
upstream fingerprint for distinguishing local changes from upstream changes.

## Proposed outcome

Implement the Phase 2 requirements in the repository-root `idea.md`: concrete
maintainability guidance and independent review, Python AST-based CODEMAP
generation, and one doctor/map/adopt/update interface over shared lifecycle code.

## Accepted decisions

The user requested implementation of `idea.md` and explicitly confirmed:

- Evolve existing migration/update tooling into one shared engine with
  compatibility entry points; mixed ownership uses bounded sections and
  installation fingerprints are recorded separately.
- Upgrade the project and factory tooling to Python 3.12+; maintaining Python
  3.9 updater compatibility is unnecessary.
- Default warning threshold: 300 code lines; maximum: 500 code lines.
- Existing oversized files require 150 net added code lines to fail on growth.
- These thresholds are project-configurable. Blank lines, comment-only lines,
  and Python docstrings do not count.
- Create the Phase 2 branch from main. `feat/factory-phase2-g1` was created
  from `35d871f`, which includes Phase 1.
- The user accepted the architecture and three capability deltas on 2026-09-10,
  authorizing program design and task-group preparation.

## Constraints

Preserve FAST/STANDARD/DEEP, OpenSpec ownership, DEEP program design, independently
shippable groups, fresh behavioral verification, human gates, compact checks,
selective skills, and context boundaries. Keep tooling stdlib-only. Do not modify
canonical specs directly, application ownership, or unrelated project settings.
Do not commit, publish, or archive without the existing human gates.

## Open questions

The user accepted program design and shipping groups on 2026-09-10 and
authorized group 1 implementation. No unresolved group 1 design choice remains.

## Areas of concern

- Legacy migration supports destructive `--force`; it cannot silently retain
  that behavior under the approved preservation contract.
- Existing upstream hash history is not a per-installation baseline. Unknown
  customizations require conflicts, not guessed ownership.
- Phase 1 is merged but not archived in this checkout. Preserve its artifacts
  and reference its implemented contracts without taking over archive work.
- Existing large harness scripts must remain reviewable without causing every
  unrelated change to fail.
