# Legacy OpenSpec Migration: software-factory

## Status
Unmigrated / Requires review
Evidence classification: UNKNOWN (all tasks checked; merge not inferred)

## Original sources
- `openspec/changes/software-factory/.openspec.yaml`
- `openspec/changes/software-factory/design.md`
- `openspec/changes/software-factory/idea.md`
- `openspec/changes/software-factory/implementation-report.md`
- `openspec/changes/software-factory/intent.md`
- `openspec/changes/software-factory/program-design.md`
- `openspec/changes/software-factory/proposal.md`
- `openspec/changes/software-factory/specs/factory-verification/spec.md`
- `openspec/changes/software-factory/specs/factory-workflow/spec.md`
- `openspec/changes/software-factory/tasks.md`

## Original intent

### Source: openspec/changes/software-factory/intent.md

# Intent: software-factory

Workflow: DEEP
Reason: Cross-cutting lifecycle ownership and context boundaries affect every stage and downstream starter updates.

## Classification
New capabilities `factory-workflow` and `factory-verification`. Existing
canonical change-submission and harness-evals requirements remain intact.

## Problem
The single heavy workflow imposes planning/context costs on small fixes and
mixes factory ownership with broad Superpowers orchestration. Verification and
shipping instructions disagree about ownership of repeated full checks.

## Proposed outcome
Implement the software-factory refactor specified in the user's `instruct.md`:
three workflow tiers, architecture then program design for DEEP, independent
verification, compact checks, progressive skills, and durable stage boundaries.

## Accepted decisions
The user authorized implementation of the supplied design and confirmed:
- `make check` becomes non-mutating; `make fmt` explicitly fixes source before
  verification and again if subsequent edits need it.
- Cosmetic wording corrections can be FAST when meaning and behavior stay
  unchanged; contractual output changes require STANDARD.
- FAST verifier input is only the branch name. STANDARD/DEEP input is only
  change slug and task group, with no implementation narrative.

## Constraints
Preserve canonical specs, archive semantics, branch/task ownership, human gates,
and deterministic security/env/git protections. Keep existing STANDARD tasks
usable. Retain installed Superpowers pending measurement. Do not add telemetry
or duplicate workflow state. Commits and PRs remain subject to human review.

## Open questions
No remaining design decision identified at intent acceptance. Runtime prompt
eval authentication and actual historical token measurements must be reported
from evidence, never assumed.


### Source: openspec/changes/software-factory/proposal.md

## Why

Maintenance currently incurs the full planning workflow while architectural work
lacks a distinct program-design boundary. Broad skill orchestration and repeated
full checks add context and cost without independent evidence.

## What Changes

- Route FAST, STANDARD, and DEEP without changing canonical OpenSpec ownership.
- Add DEEP shape-change and program design after architecture acceptance.
- Make implementation context selective and verifier context independent.
- **BREAKING**: `make check` stops auto-fixing source; developers run `make fmt`.
- Replace repeated feature-documentation reminders with a final stateless gate.
- Make successful checks concise while retaining full failures and exit status.
- Separate factory policy from harness mechanics and narrow skill triggers.
- Add static/behavioral evals and a lightweight workflow measurement format.

## Capabilities

### New Capabilities
- `factory-workflow`: tier routing, accepted artifact transitions and slice ownership.
- `factory-verification`: independent verification and deterministic check behavior.

### Modified Capabilities
None. Existing submission conventions and credential-free static eval requirements
are preserved; new factory invariants receive additional cases.

## Impact

Workflow: DEEP. Architecture-affecting: yes, factory orchestration boundaries.
Changes affect lifecycle skills, command preambles, verifier, Makefile helpers,
hook wiring, factory/harness docs, starter packaging and evals. No added framework
or runtime dependency. Existing STANDARD changes require no program-design migration.


## Decisions already made

### Source: openspec/changes/software-factory/design.md

## Context

See proposal.md for motivation. The user supplied the architecture in instruct.md
and accepted the refinements recorded in intent.md before implementation.

## Decisions

- The factory owns stages and human gates. OpenSpec remains canonical behavioral
  truth, scripts provide deterministic enforcement, and techniques load only
  when useful. A second planning engine would duplicate accepted task groups.
- FAST verification discovers a branch diff; STANDARD/DEEP verification discovers
  group artifacts. This preserves independence without inventing FAST specs.
- DEEP architecture acceptance precedes program design and vertical slicing.
  Existing STANDARD tasks continue without new metadata or program design.
- The full source gate is non-mutating. Formatting is explicit; the verifier and
  pre-commit gate each run the full suite. The implementer uses targeted checks.
- A private temporary command log gives concise success and complete failure
  output. The original exit status must survive. No persistent log/state store.
- A final feature-doc check replaces the per-edit reminder. This is simpler than
  maintaining a per-session warning ledger and requires no persistent state.
- Keep workflow policy in FACTORY.md, runtime mechanics in HARNESS.md, and only
  everyday invariants in CLAUDE.md. Optional techniques remain installed pending
  evidence from representative runs.

## Risks / Trade-offs

- Existing Makefile callers expecting auto-fixes must call make fmt explicitly.
- Existing feature directories missing CLAUDE.md will fail the new final gate.
- Prose evals assert instructions, not all model behavior; a small prompt suite
  exercises routing separately from deterministic tests.
- Actual token savings require comparable workflow runs; no historical usage
  data is provided, so the check-count reduction is a prescribed-flow comparison.

## Migration Plan

Ship lifecycle instructions, check helpers, docs, hook wiring and evals together.
Regenerate the template manifest; update guidance explains removal of the retired
hook while preserving local customizations. Never modify current-state specs here;
archive only after the implementation PR merges and the human accepts the diff.


### Source: openspec/changes/software-factory/program-design.md

# Program Design

## Implementation shape

### Files to create
- FACTORY.md: runtime-independent lifecycle policy.
- .claude/skills/shape-change/SKILL.md: DEEP implementation-readiness stage.
- .harness/scripts/lib/run_quiet.sh: reusable private-log command wrapper.
- .harness/scripts/cmd_check.sh and check_feature_docs.py: non-mutating gate.
- .harness/evals/cases/012–014 and 103–105: static invariants and routing prompts.
- .harness/evals/workflow-runs.md: measurement format and scenarios.
- .harness/tests/integration/test_factory_checks.py: executable gate/claim regressions.

### Files to modify
- Lifecycle skills and commands: tier ownership, selective loading, explicit gates.
- Verifier: independent identifier-based discovery, full gate, coverage reporting.
- Makefile: explicit formatting and compact non-mutating checks.
- Hook settings: retire repeating feature reminder; preserve security/env hooks.
- CLAUDE.md, HARNESS.md, README.md and affected setup/testing docs: remove overlap.
- Manifest generator and migration/update packaging: include new callers/helpers.
- openspec/config.yaml: align generated artifact guidance with tier ownership.

## Important types and interfaces
- `run_quiet label command args...`: returns command exit status; success prints
  one line, failure prints complete captured stdout/stderr. Optional VERBOSE=1.
- `cmd_check.sh [all|lint]`: source root from SRC, sequential checks, no source fixes.
- `check_feature_docs.py [source-root]`: exit 1 lists missing feature instructions;
  ignores empty scaffolds and caches, never writes state.
- Verifier inputs: slug + group or FAST branch only; no session narrative.

## Data and control flow
1. Accepted intent selects artifact path by tier.
2. STANDARD creates tasks; DEEP accepts architecture then creates program design/tasks.
3. Group claim atomically creates its branch and prints selective context references.
4. Implementer tests locally and formats; verifier discovers and checks independently.
5. Human reviews; shipping reruns the deterministic gate before committing.

## Integration boundaries
- Existing branch/base helpers remain authoritative; keep race-to-create mutex.
- OpenSpec CLI owns creation/validation/archive; canonical specs remain untouched.
- Manifest and migration copy paths must include dependencies of shipped commands.

## Test design

### Behavior tests
- Integration fixtures execute make check, run_quiet, branch claims and shipping failures.
- Static evals guard artifact split, skill triggers, canonical truth and gate ownership.
- Three routing prompts exercise FAST/STANDARD/DEEP classification.

### Failure cases
- Formatting or pytest failures propagate without source fixes or truncated evidence.
- Existing claim rejects a second claimant; DEEP without program design cannot claim.
- Missing feature docs fail consistently without creating a warning ledger.

### Neighbouring regression risks
- Legacy STANDARD tasks still claim and load without new metadata.
- Starter migration/update still copies instructions and dependencies safely.
- Existing secret/env/dangerous-command hooks retain their implementation and wiring.

## Migration / compatibility
See design.md Migration Plan. Keep pytest no-tests and empty-source behavior.

## Least-confident decisions
- Instruction-only routing cannot guarantee every model follows a tier; static
  checks plus representative prompt evals provide evidence, not a universal proof.
- Optional Superpowers value is unmeasured; retain installed techniques and
  collect representative workflow observations before removal.


## Known unresolved questions
Not inferred. Review the original sources and current code.

## Existing design constraints
Not inferred. Review the original sources and current code.

## Existing task status

### Source: openspec/changes/software-factory/tasks.md

## 1. Deliver a coherent tiered factory workflow

Shipping boundary: lifecycle instructions, check ownership, helpers and packaging
ship together so no intermediate release dispatches a read-only verifier to a
mutating gate or points DEEP work to an unavailable stage. One branch
`feat/software-factory-g1`, one reviewed PR. No prerequisite groups.

Context:
- specs/factory-workflow/spec.md: all scenarios
- specs/factory-verification/spec.md: all scenarios
- design.md: Decisions, Risks / Trade-offs, Migration Plan
- program-design.md: interfaces, integration boundaries and test design

- [x] 1.1 Add FAST/STANDARD/DEEP routing and shape-change with vertical tasks; verify static artifact-routing evals.
- [x] 1.2 Simplify implementation context and independent verifier inputs; verify legacy and DEEP branch-claim integration tests.
- [x] 1.3 Separate formatting from full gates, preserve command failures, and replace feature reminders; verify executable check integration tests.
- [x] 1.4 Update documentation, conditional/explicit skill policies, and downstream packaging; verify policy and manifest evals plus migration tests.
- [x] 1.5 Add routing prompt cases and workflow measurement format; verify eval discovery and required measurement fields.
- [x] 1.6 Run full evals, make check and harness tests, then obtain fresh verifier evidence and stop for human review without committing.


## Existing behavioral requirements

### Source: openspec/changes/software-factory/specs/factory-verification/spec.md

## Purpose

Provide independent evidence of correctness with concise deterministic checks that preserve failure details and human shipping gates.

## ADDED Requirements

### Requirement: Verification is fresh and read-only
The verifier SHALL receive only change slug plus task group for STANDARD/DEEP, or only branch name for FAST. It SHALL discover relevant artifacts and repository state independently, run the full deterministic gate, verify every relevant scenario and completed claim, exercise changed behavior and nearby regression paths, and report PASS or FAIL without edits. Required checks that cannot run SHALL prevent PASS.

#### Scenario: FAST verification without change artifacts
- **WHEN** a verifier receives a FAST branch name
- **THEN** it discovers the base-relative diff including uncommitted and untracked work and checks relevant existing behavior without requiring OpenSpec artifacts

#### Scenario: Completed group verification
- **WHEN** a verifier receives a change slug and group
- **THEN** it checks the group claims and relevant spec scenarios without implementation-session reasoning

### Requirement: Full gates check without fixing source
The full deterministic gate SHALL check formatting, lint, types, tests and required feature documentation without automatically editing source. The implementer SHALL use targeted tests and explicit formatting before verification. The verifier SHALL run the full gate and shipping SHALL repeat it after human review; implementation SHALL NOT run a redundant full gate immediately before verifier dispatch.

#### Scenario: Formatting failure
- **WHEN** source formatting fails the full check
- **THEN** the gate fails without fixing the source and the implementer must apply formatting explicitly

#### Scenario: Shipping check fails
- **WHEN** the pre-commit full gate fails
- **THEN** shipping stops with a failing exit status and no commit is made

### Requirement: Successful checks are compact and failures complete
Each successful check SHALL emit a concise labeled status by default. A failed check SHALL retain its complete captured command output and failing status. Verbose mode SHALL allow successful details to be shown.

#### Scenario: Quiet success
- **WHEN** a check succeeds in default mode
- **THEN** routine successful command output is replaced by its labeled success line

#### Scenario: Command failure
- **WHEN** a check emits output on both streams and fails
- **THEN** all captured output is reported with the failing label and status

### Requirement: Feature documentation is enforced without repeated reminders
The final gate SHALL report missing feature instruction files without maintaining per-session warning state or issuing reminders after every edit.

#### Scenario: Undocumented feature
- **WHEN** a feature has implementation files but lacks its instruction file
- **THEN** the final check fails and identifies the missing documentation without creating tracking state


### Source: openspec/changes/software-factory/specs/factory-workflow/spec.md

## Purpose

Route factory work through appropriately sized, reviewable artifact stages while preserving independent shipping and fresh-session continuity.

## ADDED Requirements

### Requirement: Workflow size follows behavior and risk
The factory SHALL classify work as FAST, STANDARD or DEEP with a one-sentence reason. FAST SHALL not require an OpenSpec change for behavior-neutral maintenance. Observable behavior or contractual output changes SHALL use at least STANDARD. Important architectural uncertainty SHALL use DEEP and SHALL NOT be silently demoted.

#### Scenario: Cosmetic maintenance
- **WHEN** a typo correction changes neither meaning nor contractual output
- **THEN** the factory routes FAST without requiring a new OpenSpec change

#### Scenario: Normal behavior change
- **WHEN** a normal product behavior is added without architectural unknowns
- **THEN** the factory routes STANDARD through accepted intent and spec/design/tasks

#### Scenario: Architectural replacement
- **WHEN** persistence architecture is replaced with compatibility and migration uncertainty
- **THEN** the factory routes DEEP and records the design issues justifying it

### Requirement: DEEP separates architecture from implementation readiness
STANDARD crystallization SHALL produce proposal, delta specs, design and tasks. DEEP crystallization SHALL produce proposal, delta specs and architectural design, then stop at a human gate without final tasks. After acceptance, shaping SHALL produce implementation-relevant program design and vertical, independently shippable task groups.

#### Scenario: DEEP architecture awaits acceptance
- **WHEN** DEEP crystallization finishes
- **THEN** it stops for architecture/spec review and directs the user to shape-change without generating final tasks

#### Scenario: Accepted architecture is shaped
- **WHEN** the human accepts the DEEP architecture and requests shaping
- **THEN** program design records files, types, interfaces, flows, tests and uncertainties, and tasks include shippable vertical slices

### Requirement: Artifacts preserve independent work and restartability
The factory SHALL maintain one independently shippable task group per branch and PR, using branch existence as its claim mutex. Accepted artifacts plus repository state SHALL suffice for a fresh session. Implementation SHALL load relevant group context selectively and SHALL NOT invoke a competing planning workflow. Existing STANDARD tasks SHALL remain implementable without new program-design artifacts.

#### Scenario: Legacy task group is claimed
- **WHEN** an existing STANDARD change has unchecked tasks but no tier marker or program design
- **THEN** its group remains claimable and implementation reads only relevant context

#### Scenario: Concurrent claimant
- **WHEN** a group branch already exists
- **THEN** another session cannot create a second claim for that branch

#### Scenario: Human gates remain
- **WHEN** implementation finishes or archive is requested
- **THEN** implementation stops before commit/PR for review and archive requires human confirmation before changing canonical specs


## Suggested next action
Run /grill-with-docs on this package. For architectural uncertainty use /wayfinder; once decisions are resolved use /to-spec, then /to-tickets and /implement. A human may instead abandon/archive the work. No tasks have been implemented or published by migration.

This is a migration aid, not an approved spec. Complete originals remain in the snapshot or recorded Git commit.
