# 02: Verify the proposed PR while preserving unrelated local work

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Verify the exact proposed PR content in an isolated temporary
checkout when unrelated working edits could affect results. Associate evidence
with that content while preserving the user's working files.

**Blocked by:** 01 — Verify a shippable change once and reuse its evidence.

**Status:** implemented and verified

- [x] Include all intended committed, staged, unstaged and new content in the
  verification checkout, while excluding unrelated edits.
- [x] Run applicable independent reviews and authoritative checks against the
  proposed content, and bind their evidence to that content and its inputs.
- [x] Preserve unrelated working files without requiring stash or commit, and
  report preparation/verification failures without claiming PASS.
- [x] Demonstrate a test that passes only because of an unrelated local edit:
  isolated verification rejects the proposed change and preserves the local edit.
- [x] Cover intended uncommitted/new files and workspace preservation through
  disposable-repository behavioral tests, including failure paths.
- [x] Update affected guidance/evals and pass required checks and independent
  reviews, including security review where applicable.

## Comments

Published following human approval of the eight-ticket breakdown.

## Implementation evidence — 2026-09-21

- Implemented in `d0a6a96` on `feat/engineering-v3-1b-02`.
- Verification prepares a separate checkout from comparison-base content plus
  intended committed, staged, unstaged and new working files. Unrelated edits
  are excluded without changing the working tree or index; omitted committed
  PR changes fail preparation.
- Independent reviewers inspect the prepared checkout. Recorded checks execute
  there, and fingerprints bind reports to the proposed content and inputs.
  Checkout mutations invalidate proof; fresh preparation restores a reviewable
  checkout and clears outdated reports.
- Disposable-repository tests prove an unrelated local file can make a working
  check pass while isolated verification fails, preserving that file. Coverage
  includes intended content layers, executable modes, deletions, index
  preservation, preparation/check failures and legacy evidence recovery.
- `make check` passed; `make engineering-test` passed lint, formatting, types and
  all 240 tests; `make engineering-evals` passed all seven static cases.
  Independent maintainability, behavioral and security reviews each passed.
- Development and Graft dependencies were explicitly installed in the isolated
  checkout from local caches before the successful final verification. Missing
  dependencies produced failed checks rather than a false PASS.
- Three optional authenticated prompt evals were not run. Execution inherits
  external environment state: content isolation is not a security sandbox.
- The completion status and checklist were corrected after the user identified
  that the implementation handoff had left this ticket marked ready-for-agent.
