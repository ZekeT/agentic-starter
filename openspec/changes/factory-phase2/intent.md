# Intent: factory-phase2

Workflow: DEEP
Reason: Maintainability gates, source navigation, and safe adoption/update introduce cross-cutting contracts and migration boundaries.

## Classification

New capabilities `factory-maintainability`, `factory-navigation`, and
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
maintainability guidance and independent review, Graft-backed implementation
navigation, and one doctor/maintainability/adopt/update interface over shared
lifecycle code. Navigation uses the upstream `/graft` skill and CLI.

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

## Accepted navigation revision — 2026-09-11

The user approved replacing CODEMAP with Graft and explicitly requested updates
to proposal, design, program design and tasks. This supersedes the original
brief's committed CODEMAP, custom analyzer/renderer and annotation requirements.
Use a local ignored graph and on-demand review evidence. Preserve the merged
300/500/150 policy, Code Shape planning, and independent maintainability review.
Use structural builds by default, optional explicit deep enrichment, no automatic
hooks, and non-refreshing queries during read-only review. Group 1 is merged;
group 2's paused custom CODEMAP work is not an accepted deliverable.

## Constraints

Preserve FAST/STANDARD/DEEP, OpenSpec ownership, DEEP program design, independently
shippable groups, fresh behavioral verification, human gates, compact checks,
selective skills, and context boundaries. Keep factory-owned tooling stdlib-only; Graft is an explicit external navigation
dependency. Do not modify
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

## Navigation scope clarification — 2026-09-11

The user explicitly excludes all factory and harness tooling from the graph.
Graft navigation focuses only on the main project implementation. Hidden-harness
coverage is no longer an integration requirement; application coverage and tooling
exclusion must be verified instead.

No-application behavior accepted 2026-09-11: when no application sources are
configured, report `not applicable: no application sources configured`. Validate
Graft against an application fixture; retain tooling growth and behavioral gates.
Document `/graft` usage in HARNESS.md.

### Approved skill-only integration — 2026-09-11

Graft 0.18.0's Claude installer adds hooks despite `--no-hooks`. The user approved
installing only its unchanged upstream skill and isolated CLI. Preview skill
installation, preserve customized skill files, and do not run upstream `init`.
The generated skill stays upstream-owned and ignored; `make graft-install`
regenerates it from the locked package without hooks, MCP or global agent wiring.

The factory's `.harness/bin/graft` launcher delegates through `factory navigation`
to the thin `graft.py` boundary. `project.navigation.application_roots` in the
existing manifest records the explicit application input list (empty in this
starter), forwarded as upstream `--only-dir` options. Graft still owns all graph
and cache formats. The launcher checks the pinned release, disables dotenv and
query refresh, and detects a mismatch with upstream's cached scope metadata.
This input list is not an alternate graph/configuration store. Supported review
commands are check, ask, grep, skeleton, callers, map and blast; structural build
and explicit optional `build --deep` belong to the implementer. Upstream visual
exports remain optional, outside the required read-only command surface.
