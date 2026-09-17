# 02: Produce evidence-based semantic reconciliation handoffs

**Status:** implemented and verified — ready for human review

**Spec:** ../spec.md

**Blocked by:** 01: Prepare OpenSpec inventory without removing source

**What to build:**

- Deliver the project-owned migration skill, all canonical and active-change
     classifications, human-review plan and structured application contract.
     Include static boundary evals and six representative fixture scenarios.
     Explicitly distinguish authored fixture decisions from model behavior.

- [x] Deliver the behavior described above and its approved acceptance criteria.
- [x] Add meaningful behavioral coverage at the approved seams.
- [x] Update applicable user documentation.
- [x] Pass targeted validation; record evidence and outstanding limitations.

## Comments

Published after explicit user approval of the breakdown. No commit or shipping authorization.

## Implementation evidence

- Added project-owned `.claude/skills/migrate-from-openspec/` with the semantic
  workflow and application-manifest v1 reference. This is not a managed upstream
  dependency; distribution must include both skill files explicitly.
- Added seven canonical classifications, six active states, upstream-only routing,
  evidence/current-HEAD bindings, exact review bytes and human decision boundaries.
  Existing durable docs remain evidence, not implicit removal targets. Shared
  integrations require exact replacement. Accepted Wayfinder deferral is distinct
  from an unresolved migration conflict.
- Added six brownfield source fixtures under
  `.engineering/tests/fixtures/openspec-brownfield/`, executable source/tests and
  authored expected reconciliation records/document bytes. These are authored
  examples, not measured model behavior or evidence of semantic dogfood.
- Added static boundary eval 006 and fixture-evidence tests at approved seams.
  Red: static eval failed before skill existed; six fixture tests failed before
  fixtures existed. Green: six tests passed; eval 006 passed. Ruff check and format
  checks passed across the added Python files (45 files including fixture data).
- Skill quick validator could not run: its PyYAML dependency is absent from both
  system Python and the project virtualenv. No dependency was installed implicitly.
  Frontmatter is present with name and description; independent review and full
  repository gates remain part of the parent implementation task.
- Finalizer runtime, real semantic dogfood and full acceptance/refusal integration
  coverage belong to subsequent tickets. No commit or push performed.

## Completion evidence — 2026-09-17

Completed issue 02 on `feat/engineering-v3-1`; implementation stops here for human
review. Issue 03 is next and has not been implemented by this session.

- Refined the project-owned skill and application contract: checkboxes do not
  prove implementation; distinguish pre-existing work from delivered change
  slices; retain decisions, alternatives, constraints, source references and
  known gaps; respect the configured tracker and unavailable upstream skills.
  The skill checks CLI support and stops at a handoff when finalization is absent.
- Corrected fixture D so its proposal and delta establish serialization as a
  delivered slice. C/E retain pre-existing serialization. Grounded tenant
  isolation constraints in C/D source design, and added references, missing tests
  and known gaps to authored handoff bytes.
- Added public preparation coverage across all six committed fixture projects,
  authored classification/routing coverage against inventory, source preservation,
  unapplied-destination assertions and distribution inclusion checks. Embedded
  application suites now run in copied projects with the current Python interpreter.
- Updated static boundary evals, fixture documentation and ENGINEERING.md.
- `make fmt`, `make manifest` and `git diff --check`: passed.
- `make engineering-test`: lint, format, types and **194 tests passed**.
- `make engineering-evals`: **6/6 static cases passed**; three optional prompt
  cases were not run.
- Independent behavioral/spec verifier: **PASS**, `make check` passed all seven
  stages and **13 targeted semantic fixture tests passed**.
- Independent maintainability/security-boundary reviewer: **PASS**; no blocking
  findings. Static phrase checks are limited boundary assertions, not proof that
  a model follows the instructions. No application roots require Graft preparation.

### Bounded independent skill trial

A separate agent received only the skill and raw B/D project copies, without
authored expectations or implementation notes. It produced readable plans,
application manifests and complete proposed diffs in temporary directories:
`/tmp/openspec-forward-bd-7ulc4zjd/{B,D}/.engineering/migration-work/openspec/reconciliation/`.

- B retained ownership context and raised the five-versus-ten threshold conflict,
  with an unresolved human question blocking finalization.
- D identified delivered serialization, routed only remaining delivery/retry work
  to `/to-spec`, retained design constraints and called out missing tests and the
  unverified claim that an outbox already exists.
- Three application tests passed across the copies. Direct checks verified
  manifest fields, coverage, inventory/plan hashes, baseline evidence, complete
  proposed removals, preserved sources and unapplied destinations.
- Neither project configured a tracker; the agent kept handoff input in the
  readable plan and invented no publication or tracker writes.

This was a bounded preparation/reconciliation trial, not the later realistic
end-to-end semantic dogfood or finalizer acceptance test. Temporary copies lacked
native installation, project check targets and Graft configuration. No human
semantic approval was asserted and no finalization ran.

The optional skill-creator quick validator remains unavailable because PyYAML is
absent; no dependency was installed. Frontmatter and reference structure were
inspected, and the repository gates and independent reviews passed.

No commits, pushes, PRs, source removals or migration of the user's repository were
performed. Human review remains before shipping.
