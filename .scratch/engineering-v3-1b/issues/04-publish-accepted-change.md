# 04: Publish accepted content as an actual PR/MR

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Ship the reviewed, verified and accepted content through a real
provider publication flow, committing remaining accepted corrections without
repeating current semantic review or authoritative checks.

**Blocked by:** 02 — Verify the proposed PR while preserving unrelated local work;
03 — Resolve review findings without reopening settled work.

**Status:** completed — merged in [PR #25](https://github.com/ZekeT/agentic-starter/pull/25)

- [x] `/ship` after completed acceptance review expresses acceptance and commit,
  push and PR/MR authorization for the presented unchanged scope with blockers
  resolved. Missing review is not silently supplied by invocation. Honor narrower
  requests and existing authorization; merge/force-push remain separate.
- [x] Preflight intended content/paths, evidence freshness, comparison base,
  branch/remote, authorization and unresolved findings. Missing or stale
  prerequisites return to the responsible earlier gate.
- [x] Reuse implementation commits, stage only accepted paths, commit remaining
  accepted fixes if necessary, push, create the configured provider's actual
  PR/MR, and report its URL with human-useful scope and test evidence.
- [x] Preserve unrelated work and provider independence. A PR body draft is not
  successful publication; a content-preserving commit does not invalidate proof.
- [x] Enforce hooks and stop on failures. Hook content mutations require evidence
  reassessment before publishing. Remove obsolete mandatory duplicate shipping
  checks coherently across policy, commands and evals.
- [x] Demonstrate an implementation commit plus a verified uncommitted fix
  producing a PR through fake hosting tooling. Test rejection of stale/missing
  evidence, missing acceptance review, unresolved blockers and hook mutations.
- [x] Update user guidance, run required checks and obtain independent reviews.
  Failure output identifies completed steps; resumable recovery is ticket 05.

## Comments

Published following human approval of the eight-ticket breakdown. Tests use fake
hosting tools rather than publishing real test PRs.

## Implementation evidence — reconciled 2026-09-22

- Implementation commit `8485114` adds acceptance review recording, publication
  preflight and scoped commit/push/provider PR creation using current evidence.
  Commit `d2e069e` preserves scoped pushes and configured nested hooks.
- Landed integration coverage exercises an implementation commit plus an
  uncommitted correction, missing/stale prerequisites, acceptance and blockers,
  hook failures/mutations, narrower authorization, provider failures, unrelated
  staged content, tag scope and nested hooks. Policy, guidance and evals were
  updated with the implementation.
- This reconciliation inspected landed changes and test coverage; it did not
  rerun checks or recover the original ignored independent review records.
  Completion is recorded from the merged delivery, not a new verification claim.
- Automatic recovery and duplicate detection remain scoped to ticket 05.

## Delivery reconciliation — 2026-09-22

- Merged in [PR #25](https://github.com/ZekeT/agentic-starter/pull/25)
  on 2026-09-22; local merge commit `02fbe31` is in the current checkout history.
- GitHub API access was unavailable during reconciliation; the merge record
  and landed repository content establish delivery.
