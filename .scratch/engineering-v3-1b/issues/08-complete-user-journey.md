# 08: Prove and document the complete greenfield journey

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Present the assembled user journey clearly and demonstrate it
in a disposable generated application, recording observed behavior and limits.

**Blocked by:** 05 — Resume publishing after a failed push or PR request;
06 — Start a migration-free application without manifest chores;
07 — Close an accepted brownfield migration explicitly;
v3.1 issue 05 — Document and prove all onboarding paths
([external prerequisite](../../engineering-v3-1/issues/05-onboarding-verification.md)).

**Status:** blocked — v3.1 issue 05 remains open; v3.1b issues 05–07 are merged

- [ ] Integrate v3.1 onboarding documentation. Lead the guide with onboarding,
  `/implement → /review → /ship`, expected observable outcomes, findings fixes and
  failed-push recovery. Put protocol and maintainer detail underneath or in links.
- [ ] Explain local commits versus verification, acceptance and publication;
  reusable evidence, fresh-session fallback, human-directed fixes and focused
  grilling. Keep external brownfield access and closure guidance accurate.
- [ ] Exercise a disposable generated application from setup through implementation,
  independent verification, human review, an authorized fix, reverification and
  publication handoff. Demonstrate runnable behavior for human assessment.
- [ ] Demonstrate absence of migration scaffolding and manifest chores, preservation
  of unrelated work, evidence reuse and failed-push recovery through safe fixtures
  and fake hosting tools; do not publish real test PRs.
- [ ] Verify assembled policy/command/reviewer/eval consistency. Record actual
  commands, observations, evidence and unverified limits; static assertions alone
  do not establish independent model behavior. Authenticated model evals remain
  explicit and optional under repository policy.
- [ ] Pass required checks and fresh independent reviews; resolve material
  integration findings without reopening settled decisions silently.

## Comments

Published following human approval of the eight-ticket breakdown. Earlier slices
own their incremental documentation and eval updates; this ticket assembles and
proves the complete journey.
