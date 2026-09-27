# 06: Upgrade existing navigation and document prerequisites

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Existing installations keep Graft when they visibly use it.
Otherwise the update preview proposes switching navigation to `none`, explains
how to re-enable it, and applies the change only with the approved update. The
engineering guide explains the navigation field, and documentation separates
core prerequisites (including Node for skill installation) from optional ones.

**Blocked by:** 05 (Enable and disable navigation).

**Status:** ready-for-agent

- [ ] Updating an installation with a Graft index or recorded Graft installation keeps provider `graft`.
- [ ] Updating an installation with neither proposes `graft → none` in the preview with re-enable instructions.
- [ ] The navigation change is applied only as part of an approved update; declining leaves configuration untouched.
- [ ] The engineering guide explains each provider value, enabling, disabling, and that Graft is optional.
- [ ] Documentation states Node is a core prerequisite for skill installation and Graft's npm package is an optional-capability prerequisite; no Node-free core is claimed.
- [ ] After `engineering update`, an existing `graft` installation must not fail `make check` with a misleading `graft: MISSING` merely because older records lack the launcher/guidance outputs — use a clearer status, state it in the update preview, or write the fixed launcher and guidance during the update (ticket 05 behavioral review).
- [ ] Command-level update fixture tests cover both upgrade paths and declined approval.
- [ ] Affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

### Note (2026-09-28)

Ticket 05 already added the ENGINEERING.md navigation guide and the core/optional
prerequisite split. Check this ticket's documentation criteria (provider values,
enabling/disabling, Graft optional, Node core vs Graft npm optional) against that
existing text and fill only gaps; do not redo it.
