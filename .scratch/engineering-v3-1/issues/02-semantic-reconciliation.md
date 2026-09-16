# 02: Produce evidence-based semantic reconciliation handoffs

**Status:** implemented — final integration review pending

**Spec:** ../spec.md

**Blocked by:** 01: Prepare OpenSpec inventory without removing source

**What to build:**

- Deliver the project-owned migration skill, all canonical and active-change
     classifications, human-review plan and structured application contract.
     Include static boundary evals and six representative fixture scenarios.
     Explicitly distinguish authored fixture decisions from model behavior.

- [ ] Deliver the behavior described above and its approved acceptance criteria.
- [ ] Add meaningful behavioral coverage at the approved seams.
- [ ] Update applicable user documentation.
- [ ] Pass targeted validation; record evidence and outstanding limitations.

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
