# 05: Resume publishing after a failed push or PR request

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Resume partial publication after connectivity or provider
failure without recreating completed work or repeating unchanged verification.

**Blocked by:** 04 — Publish accepted content as an actual PR/MR.

**Status:** implemented and reviewed — awaiting human acceptance and publication

- [x] Report exactly which commit/push/PR steps succeeded, what failed, and the
  concrete next recovery action.
- [x] After commit succeeds and push fails, retry following restored connectivity
  using the existing commit, scoped authorization and current evidence.
- [x] Recognize completed pushes and existing PRs, including uncertain provider
  responses, before retrying creation. Avoid duplicate commits and PRs.
- [x] Reassess changed content or relevant evidence inputs; transport failure alone
  does not require new review/checks. Never recover with automatic force-push.
- [x] Demonstrate failed push followed by successful retry with one intended
  commit/PR and no repeated unchanged verification. Cover later PR failure and
  uncertain success using disposable repositories and fake hosting tools.
- [x] Update recovery guidance and pass required checks and independent reviews.

## Comments

Published following human approval of the eight-ticket breakdown. Failed push
after successful local commit is the primary user-reported recovery scenario.


### Implementation and review — 2026-09-22

- Implementation on `feat/resume-publishing` delivers scoped
  authorization reuse, completed push/PR detection, uncertain-response recovery,
  failure-step reporting and recovery guidance.
- Independent maintainability, behavioral and security reviews passed with no
  findings. `/review` confirmed current evidence and recorded the presentation.
- Recorded checks passed: `make check`, `make engineering-test` (284 tests plus
  lint/format/types), and `make engineering-evals` (9 static cases).
- Tests use disposable Git repositories and fake providers. Live hosting,
  concurrent publication and five optional model evals remain untested.
- Evidence reviewed before this tracking update: change `issue-05`, snapshot
  `1323204b23a05a70b5e75ff4b9dc2ed4ced5fc104528150eaf6c8541a9b7160b`.
  This documentation update changes the reviewed inputs; refresh evidence and
  the presented scope before publication. The prior results describe the
  implementation reviewed, not fresh verification of these tracking edits.
- Human acceptance, publication and merge remain pending; implementation and
  review completion do not establish delivery.
