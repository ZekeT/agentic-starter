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

**Status:** implemented — independent verification recorded separately; awaiting human review

- [x] The base tip is removed from the snapshot fingerprint and kept as advisory recorded data; the merge-base stays in content identity; status and publication freshness compare identity fields, not the advisory tip.
- [x] Fetching an advanced base without rebasing keeps `verify status` current.
- [x] `verify prepare` carries reports, each marked `carried_from` the previous snapshot, only when each path's own patch is identical, plan (other than base-derived fields), tools and checks are unchanged, and no path changed between old and new merge-base intersects the plan's paths or explicit inputs; the previous record is kept as historical evidence.
- [x] A carried record has no checks and is INCOMPLETE until `verify check` passes; `verify check` keeps carried reports and records fresh results.
- [x] A failing check on a carried snapshot yields FAIL and removes the carried behavioral report; on records without carried reports, `verify check` behavior is unchanged.
- [x] Changed own patch, changed plan, tools or checks, or overlapping upstream change carries nothing and the existing previous-evidence reference and review-corrections procedure apply.
- [x] Reports are rebound to a new snapshot only through carry-forward; manual relabelling remains rejected.
- [x] The publication preflight accepts current carried PASS evidence without new review and still refuses when the remote base tip differs from the tip recorded at the latest prepare.
- [x] `CLAUDE.md`, `REVIEW.md`, the verification guide and `/review`/`/ship` skills describe carried evidence and permit the implementer `verify check` run for carried snapshots only.
- [x] Fixtures gain a helper that advances `main` and rebases the feature branch; command-level tests cover every carry and no-carry case above plus the publication cases.
- [x] Affected evals updated; no instruction permits self-certification outside the carried rerun.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review (`sensitive`: three separate sessions).

- Follow-ups from ticket 12 review (human-requested 2026-09-29; small, independent
  of carry-forward):
  - [x] `review_patterns` rejects unknown `[review]` keys, so base and proposed
    settings share one validation rule (today only `parse()` rejects them).
  - [x] Add `.pre-commit-config.yaml` and `.envrc` to the starter sensitive list
    (tool-executed configuration a broad project pattern such as `**` can reach).
  - [x] The verification guide says documentation patterns are for prose; decide
    whether the default `docs/**` narrows (e.g. `docs/**/*.md`), since code such
    as `docs/conf.py` gets the documentation tier. Narrowing changes the spec's
    default and the schema 2 migration, so settle it before editing.
  - [x] Keep `test_review_tiers.py` under 500 code lines (374 now): put carry
    tests elsewhere or split consumer-floor tests from repo-fixture tests.

## Implementation decisions

2026-09-29: Human approved narrowing documentation defaults to `docs/**/*.md`,
including the schema 2 migration and specification.

## Evidence and handoff

Implementation is on `feat/v3-1c-13-carried-evidence`, based on `main` at b839f74.
Command-level regressions are in `test_carried_evidence.py` and
`test_review_settings_followups.py`; the base-tip regression is in
`test_verification.py`. Targeted tests reproduced the old failures before fixes.
Typechecking and the maintainability gate pass; the existing size warnings remain.
`test_review_tiers.py` remains below 500 code lines.

Independent evidence is recorded under the local change `v3-1c-13`:
`./engineering verify status --change v3-1c-13`. The full-gate criterion above
is left unchecked until independent evidence establishes it; implementation
checkboxes do not claim full verification. Current checks, reports and any gaps
live in that record rather than being inferred from a commit. Human acceptance,
publication and merge remain outstanding.
