# 03: Resolve review findings without reopening settled work

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Present actionable read-only review, wait for human fix
instructions, and independently reverify authorized corrections without repeated
planning or silently undoing agreed behavior and decisions.

**Blocked by:** 01 — Verify a shippable change once and reuse its evidence.

**Status:** completed — merged in [PR #24](https://github.com/ZekeT/agentic-starter/pull/24)

- [x] Explain changed behavior, requirements coverage, consequences, risks and
  gaps. Each finding states what, why, how, recommendation and its rationale with
  concrete evidence. Review does not edit application content.
- [x] Findings identify violated requirements, demonstrated defects or concrete
  risks; consult settled decisions and keep preference-only alternatives
  non-blocking. Wait for human instructions identifying fixes to make.
- [x] Authorized corrections preserve agreed behavior/decisions and may remain
  uncommitted. Rerun authoritative automated checks after code fixes and obtain
  independent inspection of the fix and affected behavior; justify retained
  evidence for unchanged areas and broaden review for scope/architecture changes.
- [x] Present updated acceptance scope and evidence; prior acceptance does not
  automatically transfer to changed content. Routine fixes need no new spec,
  tickets or dedicated fix command.
- [x] Pause edits after two unsuccessful attempts at one finding or before a fix
  would undo a settled decision. Explain the conflict and route to focused
  `/grill-me`; record the agreed resolution before resuming and reverifying.
  Material scope expansion returns to `/to-spec` and `/to-tickets`.
- [x] Demonstrate an ordinary correction plus a correction that challenges a
  settled decision. Use behavioral coverage for evidence updates and workflow
  evals for human direction/escalation; do not claim static tests prove judgment.
- [x] Update affected guidance and pass required checks and independent reviews.

## Comments

Published following human approval of the eight-ticket breakdown. This slice can
be demonstrated without unrelated local edits and therefore does not depend on 02.


## Implementation evidence — 2026-09-21

- Prior verification records remain available through `previous_evidence` after
  corrections. Active checks/reports clear; stale reports cannot certify new
  content. Fresh reviewers justify retained unchanged-area coverage explicitly.
- Shared policy, review command and reviewer guidance cover actionable findings,
  human fix direction, non-blocking preferences, updated acceptance, and focused
  `/grill-me` after two unsuccessful attempts or before undoing a settled decision.
- The CLI correction scenario verifies preserved history, invalidation, required
  fresh checks/reports and reuse after completion. Workflow eval scenarios cover
  ordinary human-directed correction and a conflict with settled offline retries.
- `make check`, all 241 starter tests and all eight static evals passed. Fresh
  maintainability, behavioral and security reviews passed without findings.
- Five optional authenticated prompt evals were not run. Static checks establish
  instruction consistency, not model judgment. The isolated checkout required
  explicit local dependency installation and native parser compilation before
  the successful gate. No remote publication or human acceptance is implied.

## Delivery reconciliation — 2026-09-22

- Merged in [PR #24](https://github.com/ZekeT/agentic-starter/pull/24)
  on 2026-09-22; local merge commit `d07969d` is in the current checkout history.
- GitHub API access was unavailable during reconciliation; the merge record
  and landed repository content establish delivery.
