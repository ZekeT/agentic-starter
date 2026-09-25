# 07: Close an accepted brownfield migration explicitly

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Make accepted migration, pending cleanup and closed migration
explicit, extending the delivered finalizer only where behavior is missing.

**Blocked by:** v3.1 issue 03 — Finalize only accepted, current migration outputs
([external prerequisite](../../engineering-v3-1/issues/03-approved-finalization.md)).

**Status:** completed — merged in [PR #28](https://github.com/ZekeT/agentic-starter/pull/28)

- [x] Audit and integrate existing finalization; reuse inventory, reconciliation,
  validation and rollback protections rather than reimplementing migration.
- [x] Migration accepted requires validation and human acceptance. Migration
  closed requires temporary artifacts removed or explicitly retained. Unresolved
  semantic decisions or failed validation never produce completion claims.
- [x] Show exact temporary cleanup scope and retention choices; honor human
  removal authorization and requested snapshots. Changed artifacts are not
  silently deleted; retries are safe.
- [x] Keep pending cleanup visible in the migration handoff without blocking
  ordinary development. Normal gates do not depend on migration evidence or
  receipts. Add no automatic expiry or general migration service.
- [x] Demonstrate closure by approved cleanup and explicit retention; verify
  preservation of changed artifacts and refusal of false completion. Extend
  existing public migration tests only for new behavior.
- [x] Update guidance/evals and pass required checks and fresh independent reviews,
  including security review for destructive cleanup.

## Comments

Published following human approval of the eight-ticket breakdown. Confirm delivered
prerequisite behavior rather than treating a status label as acceptance evidence.

## Delivery reconciliation — 2026-09-25

- Local merge commit `e7bd1d6` records [PR #28](https://github.com/ZekeT/agentic-starter/pull/28) in this checkout history.
- Implementation `c68282d` adds acceptance, exact approved cleanup, retention and safe retries using existing validation. Correction `a1947ce` preserves closed status on finalization retries. Historical independent maintainability, behavioral and security reports for snapshot `dcfe3b0567a9360e0fba0d42f8fcbf92503a08d03ba25c4f0ec42922341944c7` record PASS; the behavioral report records `make check`, `make engineering-test` (314 tests) and `make engineering-evals` (10 static cases). Migration fixtures fake target validation subprocesses; no real external migration or optional authenticated model evals were performed.
- This reconciliation records delivered work and historical evidence, not fresh
  verification of the current checkout or these tracking edits.
