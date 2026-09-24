# 07: Close an accepted brownfield migration explicitly

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Make accepted migration, pending cleanup and closed migration
explicit, extending the delivered finalizer only where behavior is missing.

**Blocked by:** v3.1 issue 03 — Finalize only accepted, current migration outputs
([external prerequisite](../../engineering-v3-1/issues/03-approved-finalization.md)).

**Status:** ready-for-agent

- [ ] Audit and integrate existing finalization; reuse inventory, reconciliation,
  validation and rollback protections rather than reimplementing migration.
- [ ] Migration accepted requires validation and human acceptance. Migration
  closed requires temporary artifacts removed or explicitly retained. Unresolved
  semantic decisions or failed validation never produce completion claims.
- [ ] Show exact temporary cleanup scope and retention choices; honor human
  removal authorization and requested snapshots. Changed artifacts are not
  silently deleted; retries are safe.
- [ ] Keep pending cleanup visible in the migration handoff without blocking
  ordinary development. Normal gates do not depend on migration evidence or
  receipts. Add no automatic expiry or general migration service.
- [ ] Demonstrate closure by approved cleanup and explicit retention; verify
  preservation of changed artifacts and refusal of false completion. Extend
  existing public migration tests only for new behavior.
- [ ] Update guidance/evals and pass required checks and fresh independent reviews,
  including security review for destructive cleanup.

## Comments

Published following human approval of the eight-ticket breakdown. Confirm delivered
prerequisite behavior rather than treating a status label as acceptance evidence.
