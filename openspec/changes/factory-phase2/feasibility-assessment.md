# Phase 2 feasibility assessment — 2026-09-14

Assessment: the accepted bounded end state is technically achievable, but the
complete phase is not implemented or proven yet. Group 3 diagnoses installations;
group 4 must still deliver the shared ownership, adoption, update and apply engine.
This assessment is source/design analysis plus the regression evidence recorded
in implementation-report.md, not independent verification or a release approval.

## What repeated findings tell us

The latest failures expose integration gaps. Migration preserved a version stamp
while initializing a different manifest version. Doctor interpreted eval fields
differently from the runner. Migration added an ignore-file write without applying
the path constraints used by doctor. Individually plausible implementations did
not establish a consistent installation contract.

Earlier passing gates were real observations, but their coverage did not justify
the broader confidence implied by repeated handoffs. Fresh-project fixtures also
underrepresented historical installations. Increasing test counts alone would
not solve this: consumer agreement and complete output round trips are the useful
evidence. Later fixes invalidated earlier independent verdicts; the current task
list correctly leaves 3.4 pending.

The corrections consolidate version reconciliation in installation.py and case
parsing in eval_config.py. Migration and doctor now share the former, doctor and
the runner share the latter. Regression fixtures include old stamp-only,
manifest-only and version-file installations, unsafe ignore destinations,
conflicting versions, public CLI refusal and copied-runtime execution.

## Achievable completion contract

| Boundary | Acceptance evidence | Current disposition |
|---|---|---|
| Offline health | Invalid installs fail actionably; no project commands, graph refresh or secret-file reads | Implemented; fixture coverage and starter checks exist |
| Legacy compatibility | Supported version records agree; custom configuration survives; unsafe destinations fail before writes | Latest regression fixes; full ownership conversion remains group 4 |
| Eval configuration | Doctor and runner interpret the same case bytes; copied runner includes its parser | Shared parser and cross-consumer fixtures |
| Read-only adoption/update | A local template and target produce explicit actions with unchanged target bytes | Planned, not implemented |
| Ownership | Full files, named sections and defined JSON settings have one explicit owner; surrounding project bytes survive | Planned, not implemented |
| Deterministic updates | Exercise unchanged, upstream-only, local-only, conflict, convergence, deletion and removal cases | Planned, not implemented |
| Safe application | Clean committed target, all-conflict preflight, input revalidation, postchecks, honest failure/recovery report | Planned, not implemented |
| Compatibility adapters | Both old entry points invoke the same engine and cannot bypass preservation with force | Planned, not implemented |

There is no requirement to solve arbitrary semantic merging. Unknown or ambiguous
customization produces a conflict with remediation. A valid outcome can be a
refused apply with zero writes. This accepted fallback makes the problem bounded.
The design also permits honest partial-write failure reporting and Git recovery;
it does not promise filesystem transactions or automatic rollback.

## Recommended completion sequence

1. Close group 3 on a stable tree with the regression matrix and fresh independent
   maintainability/verifier evidence. Do not treat implementer gates as those
   independent verdicts.
2. Within group 4's existing single shipping boundary, prove one vertical round
   trip first: clean Python project → adoption plan → apply → doctor → local
   template change → update plan → apply → doctor → repeat with no changes.
3. Extend that same engine to customized instructions/Makefile/settings, unknown
   legacy hashes, local deletion, conflicting edits, changed inputs and injected
   write/postcheck failures. Assert preserved bytes and recovery information.
4. Switch both legacy adapters to that engine and run the same cases through
   both interfaces. Remove duplicate mutation decisions rather than patching
   each adapter separately.
5. Convert the starter and verify the complete acceptance matrix before setting
   version 2.0.0. Preserve project overrides on repeated manifest regeneration.

Group 4 must explicitly distinguish the template release offered from the
installed baseline. Its state model becomes the installation authority; legacy
stamps are conversion inputs, not permanently competing authorities. Never
advance a baseline just to make doctor pass after a conflict.

Keep v1 limited to local templates, explicit ownership, supported Python tooling,
and conflict reporting for ambiguous setups. Add no general YAML/shell parser,
automatic semantic merge, new distribution service, or universal stack promise.
If the vertical round trip cannot preserve project bytes through a template
change, stop widening coverage and resolve that contract before continuing.

Remaining uncertainty is implementation correctness and integration cost,
especially mixed-file ownership and failures during apply. The current evidence
does not establish readiness for arbitrary production repositories or guarantee
that a later review will find no defects. It supports continuing with narrower,
observable completion criteria rather than abandoning the idea or declaring the
whole phase complete.

## Seventh review round: reassessment

The new OpenSpec finding reinforces the validation problem: a presence regex
accepted empty/null-like values and could read the next YAML key as its value.
The correction now checks an explicit inline schema-name form and documents what
it cannot establish. Before the fix, 23 negative fixtures incorrectly passed;
seven supported forms passed. All 30 pass their expected outcomes after the fix.
This proves the bounded schema check, not general YAML validity or custom-schema
availability. The installed OpenSpec consumer uses a YAML parser and requires a
nonempty string; doctor remains stdlib-only and never executes that consumer.

Seven review rounds are reason to lower confidence in readiness and change the
completion method. They do not establish that adoption/update is impossible.
The source and accepted design still provide a feasible construction: explicit
inventory, hashes, bounded sections, conservative JSON reconciliation and refusal
of ambiguous changes. There is no dependency on automatic semantic merging.
However, feasibility is conditional reasoning; group 4 has no implemented
planner/apply round trip yet, so its preservation and recovery claims are unproven.

Before extending implementation, use these decision gates:

| Risk | Required proof or decision |
|---|---|
| Validators overstate health | For each category, document the supported representation and test missing, empty, malformed, customized and conflicting inputs; distinguish structural checks from consumer validation |
| Competing version authorities | Define distribution version versus installed state and legacy stamp conversion before the first group 4 write; never repair conflicts by advancing a stamp |
| Mixed-file updates overwrite project work | Demonstrate instructions, Makefile and JSON customizations surviving the same adopt/update round trip, with byte preservation outside owned sections |
| Apply leaves misleading state | Inject a failure between content and state writes and during doctor; require failure status, affected paths and usable recovery instructions |
| Legacy entry points diverge | Run the same preservation/conflict fixtures through both adapters and the new CLI |

Recommendation: continue only within the current bounded scope. Close group 3's
fresh independent evidence, then use group 4's first vertical round trip as a
go/no-go checkpoint inside its existing shipping boundary. If it cannot preserve
custom content, refuse conflicts without writes and repeat without changes, pause
further features and revise that design. Do not set 2.0.0 or call the final state
achieved until the complete task-4 acceptance matrix runs successfully. This
reassessment does not authorize implementing group 4 on the current branch.


## Eighth review round: implementation and verifier audit

The FIFO manifest hang was reproduced through the public doctor CLI with a
three-second subprocess timeout before the correction. Doctor's manifest check
rejected the FIFO, but independent diagnosis continued into application_roots,
which reopened the same manifest without checking its file type. Error isolation
between categories therefore did not establish safe input handling within each
category. The settings-only special-file regression did not exercise this path.

The existing regular-file reader now lives in config.py and is shared by doctor,
doctor_wiring, application_roots, load_config and initialize_manifest. This fixes
the common read boundary instead of adding a doctor-only precheck. Existing
installation-version inspection already checks file type before reading. The
unreachable direct-execution import fallback in doctor was removed: preceding
relative imports already require the supported factory package entry point.

A separate CLI test module reuses the healthy installation fixture and checks
seven input paths against FIFOs, directories and dangling symlinks. Every case
requires a bounded nonzero exit, a category diagnostic and completion through the
freshness message. All 21 pass. This covers stationary malformed installations;
it does not make the stat/open sequence race-free under concurrent replacement.

Workflow audit findings (source inspection, not fresh agent verdicts):

| Location | Observation | Consequence and recommendation |
|---|---|---|
| `.claude/agents/verifier.md`, Independent full gate | Requires direct behavior and nearest-regression checks, but gives no concrete shared-input or bounded-execution criterion | For filesystem tooling, require a small input/consumer matrix and timeout-protected public CLI checks; report paths exercised, not just test counts |
| `.harness/scripts/cmd_review.sh:39` | Review inventory and diff use git diff, which omits untracked files | A reviewer following only the preamble can miss new runtime/tests; include non-ignored untracked inventory in review discovery. This session inspected git status and opened those files |
| `.harness/scripts/cmd_commit_push_pr.sh:62` | Unfinished tasks only print a warning; the script then runs make check | The shell does not enforce independent evidence or its freshness. Human/agent instructions remain the enforcement layer; make missing required evidence an explicit refusal in a separately scoped workflow correction |
| `.harness/evals/cases/013-independent-gates.yaml:19` | Static checks assert instruction strings and command wiring | A static PASS establishes those artifacts, not that an independent verifier ran or exercised adversarial cases. Retain that distinction in all completion claims |
| `tasks.md`, task 3.4 and latest report | Fresh independent evidence is explicitly pending | Do not describe eight review rounds as eight independent verification passes. Obtain new verdicts on the stable tree before closing group 3 |

These are observed process limitations; this audit does not establish that any
particular prior reviewer ignored instructions. The recorded evidence is
insufficient to attribute every earlier miss to a specific agent run.

Recommendation: pause feature expansion until group 3 has a stable input/consumer
matrix and fresh independent verdicts. Track the workflow corrections above as a
bounded follow-up rather than silently rewriting shipping policy here. Then use
the previously described group 4 adopt/update/repeat round trip as the next
technical decision point. Eight rounds lower confidence in implementation and
handoff quality; they do not demonstrate that explicit ownership, conservative
conflict refusal and bounded updates are infeasible. Readiness remains unproven.
