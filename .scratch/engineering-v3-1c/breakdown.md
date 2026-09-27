# Approved v3.1c implementation slices

Status: ready-for-agent — breakdown approved 2026-09-27

Source: [specification](spec.md). Slices A and C only; B, D, E and F remain in
[intent](intent.md).

| Ticket | Blocked by | Status |
| --- | --- | --- |
| [01 Record the installation role](issues/01-record-installation-role.md) | None | completed — merged in [PR #33](https://github.com/ZekeT/agentic-starter/pull/33) |
| [02 Make Engineering configuration project-owned](issues/02-project-configuration-ownership.md) | None | completed — merged in [PR #34](https://github.com/ZekeT/agentic-starter/pull/34) |
| [03 Derive verification requirements from role and ownership](issues/03-role-based-verification.md) | 01, 02 | ready-for-agent |
| [04 Make Graft an optional capability in dependencies and doctor](issues/04-optional-graft-dependency.md) | None | completed — merged in [PR #35](https://github.com/ZekeT/agentic-starter/pull/35) |
| [05 Enable and disable navigation](issues/05-toggle-navigation.md) | 02, 04 | ready-for-agent |
| [06 Upgrade existing navigation and document prerequisites](issues/06-navigation-upgrade-and-prerequisites.md) | 05 | ready-for-agent |

Frontier: 03 and 05 (01, 02 and 04 merged); 06 after 05. Each slice updates consumer generation,
adoption/update behavior, documentation and evals, not only the maintainer
checkout. Use a fresh implementation session and branch per ticket.
