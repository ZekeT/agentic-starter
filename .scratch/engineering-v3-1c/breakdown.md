# Approved v3.1c implementation slices

Status: 12 of 13 tickets implemented and merged; ticket 09 remains open.
Audited 2026-09-30 against `origin/main` at `43a0b85`.

Source: [specification](spec.md) for slices A and C; slice B tickets 11–13 from
[spec-b-review-tiers](spec-b-review-tiers.md) (breakdown approved 2026-09-28).
D, E and F remain in [intent](intent.md).

| Ticket | Blocked by | Status |
| --- | --- | --- |
| [01 Record the installation role](issues/01-record-installation-role.md) | None | completed — merged in [PR #33](https://github.com/ZekeT/agentic-starter/pull/33) |
| [02 Make Engineering configuration project-owned](issues/02-project-configuration-ownership.md) | None | completed — merged in [PR #34](https://github.com/ZekeT/agentic-starter/pull/34) |
| [03 Derive verification requirements from role and ownership](issues/03-role-based-verification.md) | 01, 02 | completed — merged in [PR #36](https://github.com/ZekeT/agentic-starter/pull/36) |
| [04 Make Graft an optional capability in dependencies and doctor](issues/04-optional-graft-dependency.md) | None | completed — merged in [PR #35](https://github.com/ZekeT/agentic-starter/pull/35) |
| [05 Enable and disable navigation](issues/05-toggle-navigation.md) | 02, 04 | completed — merged in [PR #37](https://github.com/ZekeT/agentic-starter/pull/37) |
| [06 Upgrade existing navigation and document prerequisites](issues/06-navigation-upgrade-and-prerequisites.md) | 05 | completed — merged in [PR #42](https://github.com/ZekeT/agentic-starter/pull/42) (local merge commit 68490a0) |
| [07 Publish safely from a linked Git worktree](issues/07-publish-from-linked-worktree.md) | None | implemented and merged in [PR #32](https://github.com/ZekeT/agentic-starter/pull/32) (`28dd92c`); original independent-review record not established by this audit |
| [08 Verify consumer starter-update output against its source](issues/08-verified-starter-update-evidence.md) | 03, 10 | completed — merged in [PR #44](https://github.com/ZekeT/agentic-starter/pull/44) (`43a0b85`) |
| [09 Harden verification requirement edge cases](issues/09-verification-hardening.md) | 03 | ready-for-agent — four implementation gaps remain; non-Graft npm work stays deferred |
| [10 Make generation and update agree on the distributed file set](issues/10-distributed-file-set-agreement.md) | None | completed — merged in [PR #43](https://github.com/ZekeT/agentic-starter/pull/43) (observed merge commit `86c3df2`) |
| [11 Declare a review tier checked against a starter-rule floor](issues/11-declared-review-tier-and-floor.md) | None | completed — merged in [PR #39](https://github.com/ZekeT/agentic-starter/pull/39) |
| [12 Project review settings enable the documentation tier](issues/12-project-review-settings.md) | 11 | completed — merged in [PR #40](https://github.com/ZekeT/agentic-starter/pull/40) (local merge commit 21ec8b6) |
| [13 Carry reviewer reports across a clean rebase](issues/13-carried-evidence.md) | 11 (serialized after 12) | completed — merged in [PR #41](https://github.com/ZekeT/agentic-starter/pull/41) (local merge commit 5a382bb) |

Order agreed 2026-09-28: slice B 11 → 12 → 13 (serial; shared evidence and policy files) → 06 → 09 → 10 → 08. Each slice updates consumer generation,
adoption/update behavior, documentation and evals, not only the maintainer
checkout. Use a fresh implementation session and branch per ticket.

## Implementation audit — 2026-09-30

Checked all 13 issue files against merged history, implementation entry points
and regression coverage. Tickets 01–08 and 10–13 have landed; 09 has not.
Ticket 07 was missing from this table despite merging before ticket 01.
GitHub confirms PR #44 merged on 2026-09-30 at `43a0b85`.

| Tickets | Implementation and coverage inspected |
| --- | --- |
| 01–02 | `installation.py`, `adoption.py`, `settings.py`; installation-role, configuration-preservation and migration fixtures in `test_installation.py` and verification tests |
| 03 | `verification_requirements.py`; role/ownership, metadata, generated/adopted parity and missing-target cases in `test_verification_requirements.py` |
| 04–06 | Optional dependency/provider handling, navigation enable/disable and upgrade paths; `test_dependencies.py`, `test_doctor.py`, `test_navigation.py`, `test_navigation_upgrade.py` |
| 07 | `publication_git.py` clears hook repository variables before nested Git calls; `test_publication_worktree.py` checks accepted remote head and unchanged branch refs |
| 08 | Pinned-source comparison and isolated Git object reads; `test_verification_update.py` covers update output, tampering, modes, removals and source freshness |
| 10 | Shared `distribution.py` resolution used by adoption/update; generation/update payload and removal regressions |
| 11–12 | Plan tier validation, role separation and base/proposed review settings in verification modules; `test_review_tiers.py` and `test_review_settings_followups.py` |
| 13 | `verification_carry.py`; carry/no-carry, failed checks, provenance and publication coverage in `test_carried_evidence.py` |

### Remaining work: ticket 09

- **Mode-only consumer edits without a source pin:** `classify()` compares bytes
  with the base, not executable modes. Ticket 08 checks modes for source-backed
  updates but does not close this separate no-source case.
- **Comparison-base policy:** `validate_plan()` accepts a nonempty base reference;
  it does not enforce the configured base or provide a recorded override reason.
- **New maintainer tooling files:** `MAINTAINER_TOOLING` omits
  `.engineering/engineering/` and `.engineering/docs/`; a new unmanifested file
  there is not automatically classified as maintainer source.
- **Dependency-owned content:** classification consults manifest ownership and
  installation metadata, without a dependency-output/state rule requiring
  `make engineering-check`. A sensitive review tier does not add that check.
- Non-Graft npm handling remains explicitly deferred until a second npm
  dependency exists. Ticket 09 still needs implementation and independent gates.

This was a source, coverage and delivery audit, not a new full verification run.
The latest ticket 08 independent run passed all four gates, 542 tests and 13
static evals before PR #44 merged; five optional prompt evals were skipped.
That is historical evidence for its published snapshot, not certification of
these tracking edits. Ticket 07's original independent gate checkbox remains
unconfirmed rather than inferred from its merge. Slices D, E and F remain intent
only and are not included in the 13-ticket completion count.
