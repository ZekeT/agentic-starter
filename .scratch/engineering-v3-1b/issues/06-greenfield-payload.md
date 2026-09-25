# 06: Start a migration-free application without manifest chores

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Generate a clean greenfield application with functional setup
and ordinary gates, no migration components and no application-development
manifest chores, while keeping brownfield migration available externally.

**Blocked by:** v3.1 issue 04 — Build and initialize a clean consumer template
([external prerequisite](../../engineering-v3-1/issues/04-clean-template.md)).

**Status:** completed — merged in [PR #27](https://github.com/ZekeT/agentic-starter/pull/27)

- [x] Confirm and integrate the delivered v3.1 template behavior. Reuse its positive
  inclusion mechanism rather than introducing duplicate packaging or modifying
  its approved ticket.
- [x] Fresh payloads exclude migration implementations, migration skills and
  legacy baselines; setup, doctor and ordinary consumer gates work without them.
- [x] Brownfield migration remains usable from a separate Engineering checkout.
  Do not automatically strip code from existing installations.
- [x] Application edits pass normal gates without `make manifest` or fingerprint
  repair. Correct ownership boundaries and retain maintainer distribution
  integrity and installation safeguards.
- [x] Generate and initialize a fresh project, change application behavior and
  run normal gates without manifest regeneration. Test payload exclusions and
  external migration through the approved public command boundaries.
- [x] Update consumer/maintainer guidance and affected evals; pass required checks
  and independent reviews, including conditional security review.

## Comments

Published following human approval of the eight-ticket breakdown. This deliberately
revises v3.1's self-contained consumer migration choice after integration.

## Delivery reconciliation — 2026-09-25

- Local merge commit `9da241a` records [PR #27](https://github.com/ZekeT/agentic-starter/pull/27) in this checkout history.
- Implementation `2ec59df` reuses the positive payload list, excludes migration components, preserves external migration and tests normal application edits without manifest regeneration. Historical independent maintainability, behavioral and security reports for snapshot `387c882ea3f5e298f4ea4b34e2d89074988737b00f53b16a1990a4e2a3509f7a` record PASS; the behavioral report records `make check`, `make engineering-test` (299 tests) and `make engineering-evals` (10 static cases). Network installers were substituted in fixtures; live downloads and five optional model evals were not exercised.
- This reconciliation records delivered work and historical evidence, not fresh
  verification of the current checkout or these tracking edits.
