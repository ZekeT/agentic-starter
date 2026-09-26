# 08: Prove and document the complete greenfield journey

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Present the assembled user journey clearly and demonstrate it
in a disposable generated application, recording observed behavior and limits.

**Blocked by:** 05 — Resume publishing after a failed push or PR request;
06 — Start a migration-free application without manifest chores;
07 — Close an accepted brownfield migration explicitly;
v3.1 issue 05 — Document and prove all onboarding paths
([external prerequisite](../../engineering-v3-1/issues/05-onboarding-verification.md)).

**Status:** implemented — revised acceptance scope approved; fresh verification and publication pending; remaining live trial deferred

- [x] Integrate v3.1 onboarding documentation. Lead the guide with onboarding,
  `/implement → /review → /ship`, expected observable outcomes, findings fixes and
  failed-push recovery. Put protocol and maintainer detail underneath or in links.
- [x] Explain local commits versus verification, acceptance and publication;
  reusable evidence, fresh-session fallback, human-directed fixes and focused
  grilling. Keep external brownfield access and closure guidance accurate.
- [x] Exercise live setup, implementation and initial independent verification in a
  disposable generated application; demonstrate runnable behavior and record limits.
  The remaining live correction, reverification and publication handoff are
  explicitly deferred by the 2026-09-26 acceptance revision.
- [x] Demonstrate absence of migration scaffolding and manifest chores, preservation
  of unrelated work, evidence reuse and failed-push recovery through safe fixtures
  and fake hosting tools; do not publish real test PRs.
- [x] Verify assembled policy/command/reviewer/eval consistency. Record actual
  commands, observations, evidence and unverified limits; static assertions alone
  do not establish independent model behavior. Authenticated model evals remain
  explicit and optional under repository policy.
- [ ] Pass required checks and fresh independent reviews; resolve material
  integration findings without reopening settled decisions silently.

## Accepted scope and deferred follow-up — 2026-09-26

The human approved the [spec acceptance revision](../spec.md#acceptance-revision--2026-09-26)
and authorized fresh verification followed by shipping this scope. The prior
behavioral CONCERNS remains historical evidence under the original requirement;
this revision does not relabel that report or claim completion of the live trial.

Deferred live-trial work (not a blocker for this revised publication scope):

- [ ] Move the trial subprocess tests into `tests/integration/` and add the
  integration marker, preserving greeting behavior, when that correction is authorized.
- [ ] Obtain fresh independent verification of the corrected live application.
- [ ] Record its publication handoff without publishing a real test PR.

## Comments

Started 2026-09-25. v3.1 issue 05 is integrated by PR #30 (local merge
`92d7e3e`); v3.1b issues 05–07 were already merged. The former external blocker
is resolved. The approved test seams are public commands in disposable Git
repositories, generated templates/external migration, and workflow evaluation.

Published following human approval of the eight-ticket breakdown. Earlier slices
own their incremental documentation and eval updates; this ticket assembles and
proves the complete journey.

## Implementation evidence

- Branch: `docs/complete-greenfield-journey`; local implementation commit `90b4a7a`.
- Added the daily loop, observable handoffs, correction guidance and retry behavior
  to upstream/consumer entry guides. Added isolated Python dependency preparation
  guidance after the live trial exposed missing development extras.
- Added a generated-application public-command integration case covering correction,
  unrelated staged/working files, evidence reuse, failed push and duplicate recovery.
  Targeted run passed; fixture reviewers/hosting are explicitly scripted doubles.
- Added assembled-policy eval 011; all 11 static cases passed during independent
  verification. Optional authenticated cases were not run.
- [Journey evidence](../../../docs-maintainer/greenfield-journey-evidence.md)
  records the live setup, initial independent reviews and their actual finding.
  The human was asked to authorize moving the live trial's subprocess tests into
  `tests/integration/` and adding its marker. That decision, correction,
  reverification and publication handoff remain outstanding; no human direction
  or acceptance is inferred from scripted fixture inputs.
- Independent Standards and Security reports passed for the implementation scope.
  The initial behavioral run passed `make check`, but maintainer tests lacked the
  full Graft runtime in isolation (302 passed / 15 failed). Verification preparation
  was corrected and the subsequent run passed 317 tests and 11 static evals.
  Use change `complete-journey` for fresh evidence of the revised scope. Publication
  is authorized after that verification; no merge is authorized or claimed.
