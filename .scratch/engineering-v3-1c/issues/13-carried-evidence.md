# 13: Carry reviewer reports across a clean rebase

**Spec:** [Review tiers and carried evidence](../spec-b-review-tiers.md) (slice B)

**What to build:** Base-tip movement alone no longer invalidates evidence. When a
change is rebased cleanly onto an advanced base — its own diff, plan, tools and
checks unchanged and no upstream change touching its scope — `verify prepare`
carries reviewer reports to the new snapshot and only the authoritative checks
rerun, which the implementer may run for carried snapshots only. Any overlap
carries nothing and routes to the review-corrections procedure. `/ship` accepts
current carried PASS evidence and still requires the current remote base.

**Blocked by:** 11 (Declare a review tier checked against a starter-rule floor). Serialized after 12 because both edit the evidence record and policy text.

**Status:** ready-for-agent

- [ ] The base tip is removed from the snapshot fingerprint and kept as advisory recorded data; the merge-base stays in content identity; status and publication freshness compare identity fields, not the advisory tip.
- [ ] Fetching an advanced base without rebasing keeps `verify status` current.
- [ ] `verify prepare` carries reports, each marked `carried_from` the previous snapshot, only when each path's own patch is identical, plan (other than base-derived fields), tools and checks are unchanged, and no path changed between old and new merge-base intersects the plan's paths or explicit inputs; the previous record is kept as historical evidence.
- [ ] A carried record has no checks and is INCOMPLETE until `verify check` passes; `verify check` keeps carried reports and records fresh results.
- [ ] A failing check on a carried snapshot yields FAIL and removes the carried behavioral report; on records without carried reports, `verify check` behavior is unchanged.
- [ ] Changed own patch, changed plan, tools or checks, or overlapping upstream change carries nothing and the existing previous-evidence reference and review-corrections procedure apply.
- [ ] Reports are rebound to a new snapshot only through carry-forward; manual relabelling remains rejected.
- [ ] The publication preflight accepts current carried PASS evidence without new review and still refuses when the remote base tip differs from the tip recorded at the latest prepare.
- [ ] `CLAUDE.md`, `REVIEW.md`, the verification guide and `/review`/`/ship` skills describe carried evidence and permit the implementer `verify check` run for carried snapshots only.
- [ ] Fixtures gain a helper that advances `main` and rebases the feature branch; command-level tests cover every carry and no-carry case above plus the publication cases.
- [ ] Affected evals updated; no instruction permits self-certification outside the carried rerun.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review (`sensitive`: three separate sessions).
