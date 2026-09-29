# Approved v3.1c implementation slices

Status: ready-for-agent — breakdown approved 2026-09-27

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
| [08 Verify consumer starter-update output against its source](issues/08-verified-starter-update-evidence.md) | 03, 10 | ready-for-agent |
| [09 Harden verification requirement edge cases](issues/09-verification-hardening.md) | 03 | ready-for-agent |
| [10 Make generation and update agree on the distributed file set](issues/10-distributed-file-set-agreement.md) | None | implemented — independent verification pending |
| [11 Declare a review tier checked against a starter-rule floor](issues/11-declared-review-tier-and-floor.md) | None | completed — merged in [PR #39](https://github.com/ZekeT/agentic-starter/pull/39) |
| [12 Project review settings enable the documentation tier](issues/12-project-review-settings.md) | 11 | completed — merged in [PR #40](https://github.com/ZekeT/agentic-starter/pull/40) (local merge commit 21ec8b6) |
| [13 Carry reviewer reports across a clean rebase](issues/13-carried-evidence.md) | 11 (serialized after 12) | completed — merged in [PR #41](https://github.com/ZekeT/agentic-starter/pull/41) (local merge commit 5a382bb) |

Order agreed 2026-09-28: slice B 11 → 12 → 13 (serial; shared evidence and policy files) → 06 → 09 → 10 → 08. Each slice updates consumer generation,
adoption/update behavior, documentation and evals, not only the maintainer
checkout. Use a fresh implementation session and branch per ticket.
