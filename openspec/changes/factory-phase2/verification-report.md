# Verification handoff

Date: 2026-09-15
Change: factory-phase2
Task group: 3
Branch: feat/factory-phase2-g3
Reviewed HEAD: e643ff6c96f275361975a2fa19477616af41965c
Status: STALE — CI setup changed after independent verification

Scope: current tracked and non-ignored untracked changes; no staged changes at cycle start.

```text
 M .claude/commands/dev-change.md
 M .claude/commands/review.md
 M .github/workflows/evals.yml
 M .harness/docs/setup.md
 M .harness/evals/README.md
 M .harness/evals/run_evals.py
 M .harness/factory/cli.py
 M .harness/factory/config.py
 M .harness/factory/graft.py
 M .harness/scripts/cmd_check.sh
 M .harness/scripts/migrate_to_framework.py
 M .harness/template-manifest.json
 M .harness/tests/integration/test_factory_checks.py
 M HARNESS.md
 M openspec/changes/factory-phase2/design.md
 M openspec/changes/factory-phase2/implementation-report.md
 M openspec/changes/factory-phase2/program-design.md
 M openspec/changes/factory-phase2/specs/factory-installation/spec.md
 M openspec/changes/factory-phase2/tasks.md
?? .harness/evals/cases/017-offline-doctor.yaml
?? .harness/evals/cases/018-installation-health.yaml
?? .harness/factory/doctor.py
?? .harness/factory/doctor_wiring.py
?? .harness/factory/eval_config.py
?? .harness/factory/installation.py
?? .harness/tests/integration/test_doctor.py
?? .harness/tests/integration/test_doctor_cli.py
?? .harness/tests/integration/test_legacy_installation.py
?? openspec/changes/factory-phase2/feasibility-assessment.md
```

## Maintainability reviewer

PASS

No maintainability concerns requiring review.

## Verifier

Verification — factory-phase2, group 3

Ran:

- `.harness/bin/graft check`: exit 0; no application sources configured.
- `make check`: exit 0; all gates passed.
- `make harness-test`: exit 0; lint/format/types passed; 412 tests passed.
- `make evals`: exit 0; 18 static cases passed.
- Doctor under Python 3.12: exit 0; zero installation errors; freshness explicitly deferred.
- Independent manifest assertion: exit 0; all 107 fingerprints match.
- `git diff --check`: exit 0.

Checked against: tasks 3.1–3.4’s implementation and packaging claims and relevant installation scenarios → HOLDS. Confirmed the expected branch. Regression fixtures exercise malformed/nonregular inputs, schema and eval parsing, wiring, permissions, legacy version reconciliation, offline/non-mutating diagnosis, and gate failure propagation.

Mismatches: none found. Previous stale command fingerprints are corrected. Initial sandbox cache failures resolved through approved reruns. Direct invocation using older Python correctly rejected the unsupported interpreter.

Not covered: seven prompt evals, remote CI, group 4 ownership behavior. Graft structural build was not repeated because verification prohibits refreshing navigation; its check reports no applicable sources. Separate maintainability evidence remains the responsibility of that reviewer. No files edited or committed.

Verdict: PASS.

## Coverage and history

The prior run passed all behavioral gates but found two stale command fingerprints.
`make manifest` refreshed those entries; no source or command instructions changed.
Maintainability PASS remains applicable. Fresh verification confirms all 107 hashes.
Only packaging metadata and evidence files changed after the first reviews;
only evidence files changed after the final verifier. Both reviewers ran as
fresh subagents with only role instructions and slug/group supplied.
Prior FAIL is preserved in [implementation-report.md](implementation-report.md).
Not covered: seven prompt evals, remote CI, and group 4 ownership behavior.

## Post-verification CI correction — 2026-09-15

PR 20 exposed missing uv in the static job. Added uv, Node 22 and Graft
installation, plus a workflow path trigger; refreshed the workflow fingerprint.
Prior independent verdicts above are retained verbatim for their original scope.
Implementer reruns: 18 static evals and all make check gates passed.
Fresh remote validation and independent coverage of the CI edit are pending.
