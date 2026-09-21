# 01: Prepare OpenSpec inventory without removing source

**Status:** implemented and verified — ready for human review

**Spec:** ../spec.md

**Blocked by:** None (can start immediately)

**What to build:**

- Deliver the openspec-project preview/preparation commands and deprecated
     alias, deterministic inventory and indexes, temporary workspace, Git/source
     evidence, and clean-tree/path protection. Legacy-starter preserves OpenSpec
     and advertises the semantic handoff; adoption detects OpenSpec. Include
     regression coverage and command documentation.

- [x] Deliver the behavior described above and its approved acceptance criteria.
- [x] Add meaningful behavioral coverage at the approved seams.
- [x] Update applicable user documentation.
- [x] Pass targeted validation; record evidence and outstanding limitations.

## Comments

Published after explicit user approval of the breakdown. No commit or shipping authorization.

## Previous interrupted-session evidence

The implementation session hit an account usage limit after saving partial
changes. The user has approved both decisions in ../open-decisions.md; there
is no pending design approval.

Local verification after interruption:

- `.venv/bin/python -m pytest .engineering/tests/test_inventory.py .engineering/tests/test_migration.py .engineering/tests/test_legacy.py -o addopts='' -q`: 27 passed.
- Ruff check: one import-order failure in legacy migration.
- Ruff format check: eight files need formatting.
- Distribution manifest and install state were refreshed by the implementation session.

Still required: preserve or explicitly conflict on OpenSpec integration in a
pristine legacy Makefile, complete command documentation and additional stale
input/retry regression coverage, format, refresh fingerprints after final edits,
and run the required independent reviews and gates. Tickets 2–5 are not started.
No commits, pushes or migration against the user's repository were performed.
This ticket remains incomplete and is not ready to ship.

## Completion evidence — 2026-09-16

Resumed only issue 01 on `feat/engineering-v3-1`. The earlier incomplete status
above is superseded by this entry. Issue 02 already contains partial saved work;
it is the next issue to finish and review in a fresh session. Do not jump to 03.

- Confirmed safe preview/preparation, deprecated alias, standalone-project
  detection, deterministic inventory, temporary snapshots, stale-input refusal,
  retry behavior and legacy OpenSpec preservation; command documentation is in
  ENGINEERING.md.
- Independent review found unmarked OpenSpec instructions could be lost during
  legacy replacement. CLAUDE.md and AGENTS.md now explicitly conflict if those
  references would be removed; regression tests cover both files.
- Independent verification found invalid recorded Git evidence was accepted on
  retries. Retained commits, branch records and source-history flags are now
  validated. Tests also cover identical retries with ignored source files under
  both preservation policies.
- Repaired existing shared-gate blockers from partial later work: three generic
  type annotations in application.py and fixture collection isolation. The six
  embedded fixture suites still execute through test_semantic_fixtures.py.
- `make fmt` and `make manifest`: passed; distribution fingerprints refreshed.
- `make engineering-test`: lint, formatting, types and **187 tests passed**.
- `make engineering-evals`: **6/6 static cases passed**; three optional model
  prompt cases were not run.
- Independent behavioral verifier: **PASS**, `make check` passed, **37 targeted
  tests passed**, plus retry/staleness probes under both preservation policies.
- Independent maintainability/security review: **PASS**, no remaining findings.
- `git diff --check`: passed. No application roots configured; Graft preparation
  is not applicable.

No commits, pushes, PRs or migration of the user's repository were performed.
Human review remains before shipping. Finalization and semantic dogfood are later
ticket work; this completion applies only to safe inventory/preparation.
