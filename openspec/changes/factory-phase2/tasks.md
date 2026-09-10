# Factory Phase 2 tasks

Implementation reporting: append each completed group’s results to the shared
[implementation-report.md](implementation-report.md) before human review. Follow
its per-group structure and preserve prior evidence; use dated addenda for later
corrections. This checklist remains the authority for task completion.

## 1. Ship Python 3.12 and configurable source-growth enforcement

Branch: `feat/factory-phase2-g1`, already created from main for this session.
Prerequisites: accepted program design/tasks; no prerequisite implementation group.
Shipping boundary: usable growth command and integrated deterministic gate,
including policy, configuration, runtime upgrade, packaging, docs, and tests.
Does not introduce instructions requiring the later map/reviewer/doctor commands.

Context:
- specs/factory-maintainability/spec.md: Configurable code-line growth policy; Diff-aware evidence and explicit analysis scope; Reasoned checked-in exceptions
- specs/factory-installation/spec.md: Unified versioned factory tooling, Unsupported interpreter
- design.md: Runtime and interface; Configuration and installation metadata; Code-line accounting and growth
- program-design.md: Code Shape; Configuration and diagnostics; Group 1; Test design

- [x] 1.1 Upgrade active project/tooling requirements, bootstrap guards, migration-emitted Python settings, CI, and lockfile to Python 3.12+; verify environment sync and unsupported-interpreter diagnostics without touching targets.
- [x] 1.2 Add the thin factory launcher and shared config/source modules, extending the existing manifest with preserved project overrides; verify parsing, malformed settings, override round-trips, safe inventory, and code-line accounting fixtures.
- [x] 1.3 Implement merge-base-aware growth findings with 300/500/150 defaults, staged/unstaged/untracked coverage and rename baselines; verify exact threshold boundaries, grandfathered files, exceptions, and missing-history failures.
- [x] 1.4 Add the short maintainability policy and required Code Shape template, integrate growth into the full gate, and package the complete runtime dependencies; verify static policy/packaging evals and quiet gate failure propagation.
- [x] 1.5 Add maintainer lint/type coverage for new factory modules and run targeted tests/formatting plus manifest refresh; obtain fresh verifier evidence from make check, make harness-test, and make evals, append the group’s implementation report, then stop uncommitted for human review.

Group 1 verification evidence (2026-09-11):
- Local final `make check`: PASS after approved uv-cache access.
- Local final `make harness-test`: PASS, including factory lint/format/types and
  196 tests. `make evals`: 15/15 static cases passed; six prompt cases not run.
- Strict OpenSpec validation passed; all 94 template hashes match current files.
- Fresh verifier initially found missing verbose PASS-file evidence, a bypassed
  quiet wrapper, and incorrect tomllib-version wording. All three were corrected
  with regression coverage; the verifier confirmed those findings resolved and
  reran make check and static evals successfully.
- After resuming from its usage limit, the fresh verifier completed final checks
  against the docstring-semicolon fix and returned PASS. It independently ran
  make check, make harness-test (196 tests), make evals (15/15 static), verbose
  growth evidence, all 94 manifest-hash assertions, and docstring edge cases.
  No unresolved mismatch remains. A clean environment rebuild was not repeated;
  checks used the Python 3.12 environment. Six prompt evals were not run, and
  groups 2–4 remain outside this verification.
- No commit or PR created. Groups 2–4 have not started.

Group 1 review fixes (2026-09-11):
- The growth gate selects isolated Python 3.12 tooling without changing a
  downstream project's Python requirements, virtual environment, or lockfile.
  A migrated Python 3.11 fixture exercises the actual uv/factory invocation;
  CI installs both interpreters to run this regression.
- Manifest regeneration rejects unsupported schema versions before writing,
  while preserving legacy/schema-1 project overrides and hash history.
- Local validation: 39 targeted tests passed; make check and make harness-test
  passed (204 tests); make evals passed all 15 static cases. Six prompt cases
  were not run. Manifest refreshed; git diff --check passed.
- These are implementer checks after review fixes, not a new independent
  verifier report. Changes remain uncommitted.

## 2. Ship CODEMAP navigation and independent maintainability review

Branch: `feat/factory-phase2-g2`. Prerequisite: group 1 merged.
Shipping boundary: usable map/map --check, checked-in navigation, and the complete
new review sequence. Analyzer, renderer, annotations, reviewer, docs, packaging,
and tests ship together so completion instructions point only to available tools.

Context:
- specs/factory-codemap/spec.md: all requirements
- specs/factory-maintainability/spec.md: Code-shape planning and narrow independent review; Maintainability joins existing completion boundaries
- design.md: Source graph and navigation; Maintainability review and lifecycle
- program-design.md: Source and graph contracts; Group 2; Test design

- [ ] 2.1 Add graph records, Python AST symbol/import/entry-point analysis and supported call resolution; verify semantic fixtures including ambiguous imports and unsupported dynamic targets without executing fixture source.
- [ ] 2.2 Add annotation validation and compact Markdown/Mermaid rendering with navigation sections, bounded diagrams and physical/code metrics; verify required headings, escaped labels, omitted external nodes, and disclosed graph limits.
- [ ] 2.3 Expose factory map and non-mutating map --check, generate the starter graph/CODEMAP, and document source-of-truth hierarchy and targeted retrieval; verify repeated byte stability and stale/missing artifact failures without writes.
- [ ] 2.4 Add the fresh read-only maintainability reviewer and integrate tests → map → maintainability → verifier → human review; verify restricted inputs/tools, PASS/CONCERNS output, FAST exceptions, and architectural drift coverage through static and focused prompt evals where necessary.
- [ ] 2.5 Refresh packaging, navigation and relevant human review docs, run targeted tests/formatting, and obtain independent maintainability and verifier evidence from map --check, make check, make harness-test, and applicable evals; append the group’s implementation report and stop uncommitted for human review.

## 3. Ship deterministic installation diagnosis

Branch: `feat/factory-phase2-g3`. Prerequisite: group 2 merged.
Shipping boundary: usable doctor for the currently shipped installation, with
actionable checks, CI/full-gate integration, documentation and fixture tests.
Per-installation ownership baselines become required only when group 4 ships them.

Context:
- specs/factory-installation/spec.md: Fast actionable installation health checks; Deterministic installation regression coverage
- specs/factory-maintainability/spec.md: Reasoned checked-in exceptions
- design.md: Doctor, dogfooding, and validation
- program-design.md: Group 3; Integration boundaries; Test design

- [ ] 3.1 Implement doctor diagnostics for current manifest/version, directories, command/hook wiring, executable bits, OpenSpec, git protections, configuration/exception paths, map freshness and eval configuration; verify each failure category in independent filesystem fixtures.
- [ ] 3.2 Expose factory doctor and integrate it into make check/CI without recursion, while retaining stale-map warning semantics; verify no source writes, no project-command execution, and no environment-secret reads.
- [ ] 3.3 Dogfood ordinary installation health against the starter, update lifecycle documentation and manifest packaging, and add credential-free static doctor evals; verify healthy/stale/broken fixtures and starter doctor results.
- [ ] 3.4 Run targeted tests/formatting, refresh map and manifest, then obtain fresh maintainability and verifier evidence from doctor, map --check, make check, make harness-test and make evals; append the group’s implementation report and stop uncommitted for human review.

## 4. Ship shared safe adoption, update, and ownership migration

Branch: `feat/factory-phase2-g4`. Prerequisite: group 3 merged.
Shipping boundary: one ownership engine, per-installation state, both plan/apply
flows, and both legacy adapters migrate together. Separating their rollout would
leave entry points with conflicting preservation rules. Include all mutation
fixtures, template version/baselines, docs, and final acceptance evidence here.

Context:
- specs/factory-installation/spec.md: all requirements, particularly Explicit ownership and preserved project configuration; Inspection-first non-destructive adoption; Fingerprint-based deterministic updates; Recoverable and validated application
- design.md: Ownership, adoption, and update; Configuration and installation metadata; Migration Plan
- program-design.md: Ownership and plan contracts; Group 4; Migration / compatibility; Test design

- [ ] 4.1 Implement explicit ownership scopes, bounded-section/JSON merges, and versioned installation state while preserving project overrides; verify containment, malformed markers, hash consistency, preserved surrounding bytes and non-self-referential metadata.
- [ ] 4.2 Extract conservative target inspection and implement read-only adoption plans with ADD/MERGE/PRESERVE/CONFLICT/SKIP; verify plan-only byte preservation, existing instructions/CI/canonical make check, supported tool evidence, and unsupported-stack diagnostics.
- [ ] 4.3 Implement fingerprint-based update planning and legacy baseline conversion; verify all four update outcomes, convergence, local deletion, upstream removals, historical pristine hashes and unknown customized content.
- [ ] 4.4 Implement explicit apply with clean committed Git preflight, changed-input detection, all-conflict validation, state handling, doctor and recovery reporting; verify zero writes on preflight failure and honest reporting of write/postcheck failures.
- [ ] 4.5 Replace legacy migration/update execution paths with shared-engine adapters, retaining supported argument forms and rejecting unsafe force behavior; verify old/new entry-point agreement and replace only tests for intentionally changed overwrite contracts.
- [ ] 4.6 Convert the starter inventory and mixed-ownership regions, activate doctor baseline validation, set completed template version 2.0.0 and make manifest refresh behavior; verify ordinary starter doctor health, deterministic regeneration and install/update fixture round trips.
- [ ] 4.7 Update FACTORY/HARNESS/setup/review documentation and lifecycle diagrams, refresh map and manifest, and verify command instructions plus managed dependency completeness through static evals.
- [ ] 4.8 Run targeted tests and formatting, obtain fresh maintainability review and verifier evidence covering doctor, map --check, make check, make harness-test and full static/behavioral evals; report actual gaps and stop uncommitted for human review.
- [ ] 4.9 Append group 4 results and the final Phase 2 acceptance summary to implementation-report.md, retaining the earlier group reports and listing delivered behavior, files, evidence, limitations, deferred work and deviations; verify every acceptance claim against recorded results without changing canonical specs or archiving implicitly.
