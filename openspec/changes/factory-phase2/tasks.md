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

## 2. Ship Graft navigation and independent maintainability review

Branch: `feat/factory-phase2-g2`. Prerequisite: group 1 merged (satisfied).
Navigation revision accepted 2026-09-11. This replaces the uncompleted custom
CODEMAP plan; no earlier CODEMAP test run counts as Graft integration evidence.
Shipping boundary: validated upstream Graft skill/CLI, local-cache lifecycle,
reviewer, documentation, packaging and tests ship together. No committed map,
in-house graph schema/analyzer/renderer, or factory map command is required.

Context:
- specs/factory-navigation/spec.md: all requirements
- specs/factory-maintainability/spec.md: Code-shape planning and narrow independent review; Maintainability joins existing completion boundaries
- design.md: Graft navigation and review evidence; Maintainability review and lifecycle
- program-design.md: Source counting and Graft contracts; Group 2; Test design

- [x] 2.1 Remove the paused custom CODEMAP navigation implementation, generated artifacts, annotations and integrations while retaining merged growth checks and reusable reviewer work; verify the diff contains no unrelated reversions and no active CODEMAP command/schema dependencies.
- [x] 2.2 Select and validate a pinned Graft release with Node.js 22.12+ tooling (the locked dependency minimum) isolated from application dependencies, then install its unchanged upstream /graft skill directly from the package template through previewed repository-local wiring (do not run upstream init); verify application Python coverage and exclusion of factory/harness tooling, no automatic hooks, preserved instructions/statusline and no global configuration writes on a disposable fixture.
- [x] 2.3 Integrate explicit structural builds, non-mutating freshness checks and non-refreshing reviewer queries; document the local ignored cache, optional deep enrichment and on-demand impact/visualization evidence; verify no model credentials are required, read-only queries preserve source/config/cache bytes, and absent application scope reports not applicable.
- [x] 2.4 Complete the fresh read-only maintainability reviewer and tests → Graft build → maintainability → verifier → human review sequence; verify restricted inputs/tools, PASS/CONCERNS output, FAST exceptions, actionable drift findings and missing-cache disposition through static and focused prompt evals where necessary.
- [x] 2.5 Refresh packaging and navigation/review guidance (including /graft usage in HARNESS.md), remove obsolete CODEMAP CI checks, prepare Graft’s local cache in CI, and obtain independent maintainability/verifier evidence from graft check, make check, make harness-test and applicable evals; append actual group results to implementation-report.md and stop uncommitted for human review.


Group 2 final verification (2026-09-11):
The evidence below predates the human-review P2 correction. See the latest
implementation-report.md entry for the structural/enrichment gate correction and
its verification; earlier independent verdicts do not cover that correction.
- Fresh maintainability review: PASS on the final tree.
- Fresh verifier: PASS; make check, make harness-test (227 tests), make evals
  (16 static cases), diff whitespace and all 101 template hashes passed.
- Focused prompt eval 106 and independent impact/non-mutation fixture passed.
- The nested-tooling finding was fixed and re-verified. Final regressions also
  cover dotenv override rejection; no unresolved mismatch remains.
- Starter Graft build/check report the accepted no-application disposition;
  actual application graphs are exercised in disposable fixtures.
- Six unrelated prompt cases, remote Node 22 CI, optional deep enrichment and
  visualization exports were not exercised. See implementation-report.md for
  cumulative evidence, corrections and the final verifier report.
- Group 2 remains uncommitted on feat/factory-phase2-g2 for human review.
  Groups 3 and 4 remain unchecked.

## 3. Ship deterministic installation diagnosis

Branch: `feat/factory-phase2-g3`. Prerequisite: group 2 merged (satisfied).
Offline doctor scope adjustment accepted 2026-09-12: Graft freshness remains
the separate explicit check; doctor does not invoke the upstream CLI.
Shipping boundary: usable doctor for the currently shipped installation, with
actionable checks, CI/full-gate integration, documentation and fixture tests.
Per-installation ownership baselines become required only when group 4 ships them.

Context:
- specs/factory-installation/spec.md: Fast actionable installation health checks; Deterministic installation regression coverage
- specs/factory-maintainability/spec.md: Reasoned checked-in exceptions
- design.md: Doctor, dogfooding, and validation
- program-design.md: Group 3; Integration boundaries; Test design

- [x] 3.1 Implement doctor diagnostics for current manifest/version, directories, command/hook wiring, executable bits, OpenSpec, git protections, configuration/exception paths, Graft availability/version/wiring/application paths and eval configuration; verify each failure category in independent filesystem fixtures.
- [x] 3.2 Expose factory doctor and integrate it into make check/CI without recursion, while explicitly reporting that Graft freshness is not assessed offline; verify no source writes, no project-command execution, and no environment-secret reads.
- [x] 3.3 Dogfood ordinary installation health against the starter, update lifecycle documentation and manifest packaging, and add credential-free static doctor evals; verify healthy/broken fixtures, deferred freshness and starter doctor results.
- [x] 3.4 Run targeted tests/formatting, build the Graft structural cache and refresh the manifest, then obtain fresh maintainability and verifier evidence from doctor, graft check, make check, make harness-test and make evals; append the group’s implementation report and stop uncommitted for human review.

2026-09-14 review correction: all three latest findings are addressed; final
implementer gates pass (361 harness tests, 18 static evals). Version reconciliation
and eval parsing now have shared implementations and cross-consumer fixtures.
See the latest implementation-report.md addendum and
[feasibility assessment](feasibility-assessment.md). Task 3.4 remains unchecked
until fresh independent maintainability/verifier evidence covers this tree.

2026-09-14 schema review correction: doctor now validates a documented inline
OpenSpec schema-name form, rejecting empty/null-like values, duplicate declarations
and next-line spillover. Thirty added cases reproduce 23 pre-fix false passes;
all now pass. Final implementer checks: make check, 391 harness tests and 18 static
evals pass. Feasibility reassessment adds explicit group 4 decision gates. Task
3.4 remains pending fresh independent evidence; group 4 was not implemented.

2026-09-14 eighth review correction: FIFO manifest reads now share the guarded
configuration reader across doctor and navigation. A timeout-protected CLI matrix
passes 21 nonregular-input cases; make check, 412 harness tests and 18 static evals
pass. See implementation-report.md and feasibility-assessment.md for the
implementation/verifier audit. Independent evidence remains pending; 3.4 stays
unchecked.

## 4. Ship shared safe adoption, update, and ownership migration

Branch: `feat/factory-phase2-g4`. Prerequisite: group 3 merged (satisfied).
2026-09-15 human decision: proceed without refreshing group 3 verification after
the CI correction. Preserve its STALE report in history; group 4 receives its own
fresh independent review cycle. This does not retroactively verify the CI edit.
Shipping boundary: one ownership engine, per-installation state, both plan/apply
flows, and both legacy adapters migrate together. Separating their rollout would
leave entry points with conflicting preservation rules. Include all mutation
fixtures, template version/baselines, docs, and final acceptance evidence here.

Context:
- specs/factory-installation/spec.md: all requirements, particularly Explicit ownership and preserved project configuration; Inspection-first non-destructive adoption; Fingerprint-based deterministic updates; Recoverable and validated application
- design.md: Ownership, adoption, and update; Configuration and installation metadata; Migration Plan
- program-design.md: Ownership and plan contracts; Group 4; Migration / compatibility; Test design
- feasibility-assessment.md: Recommended completion sequence; Seventh review round decision gates; Eighth review round input/consumer matrix

Carry-forward constraints: reuse config.py guarded readers, installation.py legacy
version reconciliation, and eval_config.py parsing. Factory tooling requires Python
3.12+ while downstream Python metadata, environments and locks remain project-owned.
Doctor stays offline; Graft build/check is separate and no application scope remains
not applicable. No automatic Graft hooks, cache copying or upstream init.

Implementation checkpoint within this shipping group: before widening adapter and
inventory coverage, prove clean Python adoption → apply → doctor → template change
→ update → apply → doctor → unchanged repeat. Include customized instructions,
Makefile and JSON, preserved surrounding bytes, and conflict refusal with zero writes.
Stop and clarify if that bounded contract cannot be demonstrated.

- [x] 4.1 Implement explicit ownership scopes, bounded-section/structural JSON merges (JSON whitespace may normalize), and versioned installation state while preserving project overrides; explicitly distinguish distribution version, installed state authority and legacy conversion inputs before any target write; verify containment, malformed markers, hash consistency, preserved surrounding bytes and non-self-referential metadata.
- [x] 4.2 Extract conservative target inspection and implement read-only adoption plans with ADD/MERGE/PRESERVE/CONFLICT/SKIP; verify plan-only byte preservation, existing instructions/CI/canonical make check, supported tool evidence, and unsupported-stack diagnostics; require initialized OpenSpec and canonical make check, preserve its recipe and offer make factory-check alongside it.
- [x] 4.3 Implement fingerprint-based update planning and legacy baseline conversion; verify all four update outcomes, convergence, local deletion, upstream removals, historical pristine hashes and unknown customized content; unmarked legacy Makefiles conservatively conflict for explicit region conversion; never advance a conflicted baseline or stamp to satisfy doctor.
- [x] 4.4 Implement explicit apply with clean committed Git preflight, changed-input detection, all-conflict validation, state handling, doctor and recovery reporting; verify zero writes on preflight failure and honest reporting of write/postcheck failures, including failure between content and state writes, affected paths and usable Git recovery instructions; retain offline doctor and separate Graft/eval follow-up.
- [x] 4.5 Replace legacy migration/update execution paths with shared-engine adapters, retaining supported argument forms and rejecting unsafe force behavior; verify old/new entry-point agreement using the same preservation/conflict fixtures, copied-runtime dependencies and downstream Python 3.11 isolation; replace only tests for intentionally changed overwrite contracts.
- [x] 4.6 Convert the starter inventory and mixed-ownership regions, activate doctor baseline validation, set completed template version 2.0.0 and make manifest refresh behavior; verify ordinary starter doctor health, deterministic regeneration and install/update fixture round trips; set 2.0.0 only after the complete acceptance matrix passes, without masking recorded customizations as corruption.
- [x] 4.7 Update FACTORY/HARNESS/setup/review documentation and lifecycle diagrams, build the Graft structural cache and refresh the manifest, and verify command instructions plus managed dependency completeness through static evals.
- [x] 4.8 Run targeted tests and formatting, obtain fresh maintainability review and verifier evidence covering doctor, graft check, make check, make harness-test and full static/behavioral evals; exercise timeout-protected public CLI malformed/special-file inputs across shared consumers, distinguish structural checks from consumer validation, report actual gaps and stop uncommitted for human review.
- [x] 4.9 Append group 4 results and the final Phase 2 acceptance summary to implementation-report.md, retaining the earlier group reports and listing delivered behavior, files, evidence, limitations, deferred work and deviations; verify every acceptance claim against recorded results without changing canonical specs or archiving implicitly.

Group 2 accepted fingerprint correction (2026-09-11): wrapper fingerprint
inspection removed by user decision; upstream owns cache selection/validation.
Application-root changes require an explicit build before review. The navigation
delta and design document the tradeoff. All 30 pinned Graft integration tests and
factory lint/format/type checks passed. Fresh independent verdicts on 2026-09-12:
maintainability PASS; verifier PASS. make check, 234 harness tests, 16 static evals,
focused prompt eval 106, all 101 template hashes and whitespace checks passed.
See the latest implementation-report.md entry for coverage gaps. Group 2 remains
uncommitted for human /review; groups 3 and 4 remain pending.


Group 4 final handoff (2026-09-15): fresh maintainability PASS and fresh verifier
PASS after both marker-line and legacy hash-history corrections. Independent
results: make check passed; 412 harness tests plus lint/format/types passed;
19 static evals passed; doctor passed; 70 targeted lifecycle/ownership tests
passed; all 114 distribution hashes and 108 owned baselines matched. Graft check
reports no application sources configured. Seven prompt evals, remote CI and
optional enrichment were not exercised. See verification-report.md for verbatim
current reports and implementation-report.md for history and Phase 2 acceptance.
Group 4 is uncommitted on feat/factory-phase2-g4 for human /review. No groups
remain unchecked; canonical specs have not been edited or archived.
