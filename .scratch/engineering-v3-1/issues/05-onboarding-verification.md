# 05: Document and prove all onboarding paths

**Status:** implemented — awaiting human acceptance; current verification is recorded under change `onboarding`

**Spec:** ../spec.md

**Blocked by:** 04: Build and initialize a clean consumer template

**What to build:**

- Finish upstream/consumer/maintainer documentation; place retained history
     with maintainers; exercise normal adoption, legacy upgrade, a realistic
     semantic migration and fresh-template setup. Run required gates and fresh
     independent reviews. Record actual evidence and any remaining human decisions.
   - Remote template publication remains deferred by the accepted decision.

- [x] Deliver the behavior described above and its approved acceptance criteria.
- [x] Add meaningful behavioral coverage at the approved seams.
- [x] Update applicable user documentation.
- [x] Pass targeted validation; record evidence and outstanding limitations.

## Comments

Published after explicit user approval of the breakdown. No commit or shipping authorization.

## Implementation progress — 2026-09-25

- Added explicit new-project, adoption, legacy-upgrade and external OpenSpec
  onboarding paths, plus consumer and maintainer guidance. Relocated retained
  migration reports/source packages under `docs-maintainer/history/` without
  reclassifying historical semantics. Consumer payload excludes this directory.
- New public CLI onboarding tests initially failed in both adoption and legacy
  upgrade: the installed `engineering-check` invoked a maintainer-only eval
  requiring absent template files. Removed eval execution from that shared gate;
  doctor and maintainability remain mandatory, and maintainers run the separate
  required `engineering-evals` target. Both regression cases now pass, including
  preserved OpenSpec, native CI/package/check content, preview immutability and
  a deliberately broken native test proving the gate still detects failures.
- Targeted template/onboarding coverage: 17 passed. Typechecking: 36 source files
  passed. Live fresh setup/repeat setup/doctor/checks and an application edit
  passed without manifest changes. An arbitrary OpenSpec fixture passed real
  adoption, dependency installation, native tests, inventory, approved semantic
  finalization and an unchanged retry. See [onboarding evidence](../../../docs-maintainer/onboarding-evidence.md).
- Independent review caught a git-only claim that contradicted the actual snapshot
  policy. The user directed correction to snapshot and approved the regenerated
  exact proposal before finalization. Validation, unchanged retry and subsequent
  checks passed; application/test/snapshot bytes were preserved. Fixture output
  acceptance and cleanup remain human decisions, not inferred completion.
  Required full checks and independent review results are recorded separately
  under change `onboarding` in ignored `.engineering/state/verification/`.
  No acceptance, publication or merge is claimed. The current `/implement`
  request authorizes scoped local commits.
