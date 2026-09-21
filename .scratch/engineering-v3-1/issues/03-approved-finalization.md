# 03: Finalize only accepted, current migration outputs

**Status:** implemented and verified — ready for human review

**Spec:** ../spec.md

**Blocked by:** 02: Produce evidence-based semantic reconciliation handoffs

**What to build:**

- Deliver previewable finalization, exact approved docs/removals, conflict and
     stale-input refusal, committed-history preservation, rollback/idempotency,
     validation reports and removable temporary evidence. Cover destructive
     behavior with regression tests and security review.

- [x] Deliver the behavior described above and its approved acceptance criteria.
- [x] Add meaningful behavioral coverage at the approved seams.
- [x] Update applicable user documentation.
- [x] Pass targeted validation; record evidence and outstanding limitations.

## Comments

Published after explicit user approval of the breakdown. No commit or shipping authorization.

## Implementation evidence — 2026-09-17

- Added `migrate openspec-project --finalize [--plan|--apply]`: exact readable
  plan, complete diffs, manifest digest and recovery commit precede application.
  The explicit apply command remains the human authorization boundary.
- Reuses the v1 application contract and preparation inventory to reject changed
  HEAD/source/evidence/destinations, incomplete removals, unresolved decisions,
  unsafe paths and dirty Git. Git-only verifies exact original bytes in history;
  explicitly selected snapshots remain intact.
- Exact document and integration edits run in the existing rollback transaction.
  Doctor, native project checks and applicable Graft checks must pass before a
  temporary fingerprinted receipt is written. Changed repeat outputs conflict;
  exact retries are read-only. Empty retired source directories are removed.
- Added 28 command-level tests across preview, success/retry, refusal, rollback,
  snapshot retention, six authored scenarios, real doctor failure and hostile
  validation side effects. Authored scenarios establish finalizer behavior, not
  autonomous semantic judgment.
- Independent reviews found and resolved receipt symlink following and missing
  post-gate integration checks. Exclusive contained receipt creation prevents
  external overwrite; rollback continues restoring other files after a path
  becomes unsafe. New regression cases verify both failures.
- Updated ENGINEERING.md, the project migration skill/contract and generated
  distribution fingerprints. No upstream skill was modified.

### Disposable end-to-end trial

`/tmp/issue03-dogfood.py` builds an installed sacrificial project using fixture D,
with real source/tests, native `make check`, installed pinned dependencies and an
explicit no-application-graph configuration. The readable proposal distinguishes
implemented serialization from remaining delivery work, retains domain ownership
context and routes only decided remaining work to upstream to-spec.

Real doctor and project tests passed through finalization, an unchanged retry,
and subsequent removal of the temporary workspace. Doctor and project checks
still passed without migration evidence. Graft reported NOT APPLICABLE. The
independent verifier inspected and reran the script successfully. The script/log
are temporary artifacts, not shipped tooling; this is a bounded fixture trial,
not human semantic approval of a production migration.

Project checks execute trusted project code; offline dependency flags are not a
sandbox. On validation failure the transaction restores its own affected files;
additional project-check artifacts and process-kill recovery require inspection.
Optional authenticated prompt evals were not run. No production source removal,
commit, push, PR or work on issue 04 was performed.

### Final verification

- `make fmt` and `git diff --check`: passed.
- Independent maintainability/Standards review: PASS.
- Independent security review: PASS; no outstanding findings.
- Independent behavioral/Spec verification: PASS.
- `make check`: all seven gates passed.
- `make engineering-test`: lint, formatting, types and **222 tests passed**.
- `make engineering-evals`: **6/6 static cases passed**; three optional
  model-backed cases skipped.

Implementation stops here for human review. All changes remain uncommitted.
