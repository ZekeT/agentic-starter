# 06: Upgrade existing navigation and document prerequisites

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Existing installations keep Graft when they visibly use it.
Otherwise the update preview proposes switching navigation to `none`, explains
how to re-enable it, and applies the change only with the approved update. The
engineering guide explains the navigation field, and documentation separates
core prerequisites (including Node for skill installation) from optional ones.

**Blocked by:** 05 (Enable and disable navigation).

**Status:** implemented — verification incomplete (maintainer suite timeout)

- [x] Updating an installation with a Graft index or recorded Graft installation keeps provider `graft`.
- [x] Updating an installation with neither proposes `graft → none` in the preview with re-enable instructions.
- [x] The navigation change is applied only as part of an approved update; declining leaves configuration untouched.
- [x] The engineering guide explains each provider value, enabling, disabling, and that Graft is optional.
- [x] Documentation states Node is a core prerequisite for skill installation and Graft's npm package is an optional-capability prerequisite; no Node-free core is claimed.
- [x] After `engineering update`, an existing `graft` installation must not fail `make check` with a misleading `graft: MISSING` merely because older records lack the launcher/guidance outputs — use a clearer status, state it in the update preview, or write the fixed launcher and guidance during the update (ticket 05 behavioral review).
- [x] Command-level update fixture tests cover both upgrade paths and declined approval.
- [x] Affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

### Note (2026-09-28)

Ticket 05 already added the ENGINEERING.md navigation guide and the core/optional
prerequisite split. Check this ticket's documentation criteria (provider values,
enabling/disabling, Graft optional, Node core vs Graft npm optional) against that
existing text and fill only gaps; do not redo it.

## Implementation and handoff

Branch: `feat/v3-1c-06-navigation-upgrade`, based on `main` at `5a382bb`.
The update previews its navigation migration and applies it through the existing
approval and transaction boundary. An index or recorded installation keeps Graft;
unused Graft changes to `none`, preserving roots and other configuration. Older
registries gain their missing capability declaration without changing pins.
Older installation records report `UPGRADE REQUIRED` and the dependency repair
command in the preview and doctor.

Command-level coverage is in `.engineering/tests/test_navigation_upgrade.py`;
the existing launcher-handover fixture now supplies an index as evidence of use.
Coverage includes preview/decline, both retention paths, repeated updates,
legacy registry migration, old output records, schema migration composition,
and alternate configuration table forms. ENGINEERING.md and the optional
navigation policy eval cover upgrade guidance and the existing prerequisite split.
Typechecking and the maintainability gate pass; existing size warnings remain.

Independent verification uses change `v3-1c-06` and plan
`.engineering/state/verification/v3-1c-06-plan.json`. The evidence record is the
source of current check and reviewer results: `./engineering verify status
--change v3-1c-06`. Full checks and fresh maintainability, behavioral and security
review remain pending. Human acceptance and publication are separate and pending.

### Independent review (2026-09-30)

Implementation commit `aaf517a`, snapshot
`654e4fb08d4afe52301ec8bc85d6885a930466f5cf8597f485973afe6f041f23`:
maintainability PASS and security PASS, with no implementation findings.
Behavioral FAIL because the full required proof is unavailable: both recorded
runs passed `make check` and `make engineering-check`, but `make engineering-test`
timed out after 900 seconds. The second run used approved access to the normal
uv cache instead of the initial sandbox workaround. Neither run reported a test
failure before timing out; this does not establish a full-suite pass.

All 93 targeted tests passed during implementation. The independent verifier also
ran the eval command separately: 13 static cases passed and five optional prompt
cases were skipped. Both timeout histories and the reviewer reports are preserved
under `.engineering/state/verification/` for change `v3-1c-06`.

The human chose to keep the 900-second limit and hand off incomplete verification.
No timeout or check command has been changed. The full-check criterion remains
unchecked. A future fresh verification session must resolve suite runtime within
the existing limit before obtaining current PASS evidence.
This tracking update changes the snapshot; the results above are historical
proof of the named implementation snapshot, not a current PASS. Acceptance and
publication remain outstanding.
