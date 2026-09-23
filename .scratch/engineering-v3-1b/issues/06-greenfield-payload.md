# 06: Start a migration-free application without manifest chores

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Generate a clean greenfield application with functional setup
and ordinary gates, no migration components and no application-development
manifest chores, while keeping brownfield migration available externally.

**Blocked by:** v3.1 issue 04 — Build and initialize a clean consumer template
([external prerequisite](../../engineering-v3-1/issues/04-clean-template.md)).

**Status:** ready-for-agent

- [ ] Confirm and integrate the delivered v3.1 template behavior. Reuse its positive
  inclusion mechanism rather than introducing duplicate packaging or modifying
  its approved ticket.
- [ ] Fresh payloads exclude migration implementations, migration skills and
  legacy baselines; setup, doctor and ordinary consumer gates work without them.
- [ ] Brownfield migration remains usable from a separate Engineering checkout.
  Do not automatically strip code from existing installations.
- [ ] Application edits pass normal gates without `make manifest` or fingerprint
  repair. Correct ownership boundaries and retain maintainer distribution
  integrity and installation safeguards.
- [ ] Generate and initialize a fresh project, change application behavior and
  run normal gates without manifest regeneration. Test payload exclusions and
  external migration through the approved public command boundaries.
- [ ] Update consumer/maintainer guidance and affected evals; pass required checks
  and independent reviews, including conditional security review.

## Comments

Published following human approval of the eight-ticket breakdown. This deliberately
revises v3.1's self-contained consumer migration choice after integration.
