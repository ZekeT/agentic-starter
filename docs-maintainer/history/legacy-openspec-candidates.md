# Legacy context candidates — requires review

These are unclassified source excerpts, not current behavior documentation. Retain only durable product/domain context that cannot be inferred from code. Promote clear architectural decisions to docs/adr/ after review; deduplicate existing ADRs. Delete this candidate once reconciled.

## Original source: openspec/specs/change-submission/spec.md

# change-submission Specification

## Purpose
Defines how a change is committed and proposed for review, so a reviewer can
check what was verified without asking the author what they ran.

## Requirements

### Requirement: Pull requests state how the change was verified
Every pull request SHALL state how the change was tested, covering automated
tests and any manual verification. Where a change was verified manually, the PR
SHALL record the steps taken and the observed result, not merely assert that
checking occurred.

#### Scenario: A change with no automated test
- **WHEN** a change cannot be covered by an automated test
- **THEN** the PR states why, and records the manual steps and their result

#### Scenario: Reviewer checks the compliance pass
- **WHEN** a reviewer runs `REVIEW.md`'s Pass 4
- **THEN** the PR body already names which tests cover the new behaviour

### Requirement: Commits follow Conventional Commits
Commit subjects SHALL follow `type(scope): description` in the imperative mood.
The body SHALL explain why the change was made where that is not obvious from
the diff.

#### Scenario: A commit that only restates the diff
- **WHEN** a commit body describes what changed rather than why
- **THEN** it is incomplete: the diff already shows what changed


## Original source: openspec/specs/harness-evals/spec.md

# harness-evals Specification

## Purpose
Defines how the harness regression-tests its own agent configuration, and how
that suite is kept honest over time.

## Requirements

### Requirement: Every eval case states what it guards against
Each case SHALL carry a `why` field naming the concrete failure it prevents, so
a reviewer can judge whether it still earns its runtime.

#### Scenario: Case missing a why field
- **WHEN** a case file omits `why`
- **THEN** the runner fails to parse it and reports the offending file

### Requirement: Static cases run without credentials
Static cases SHALL NOT require an API key, so CI can gate every PR on them.

#### Scenario: CI runs with no Anthropic credentials
- **WHEN** the static suite runs in CI
- **THEN** it completes and reports pass or fail without authenticating


## Original source: openspec/specs/test-organisation/spec.md

# test-organisation Specification

## Purpose
Defines how tests are separated by what they touch, so the fast suite stays
trustworthy offline and any category can be run on its own.

## Requirements

### Requirement: Tests are separated by what they touch
Test suites SHALL be split into `tests/unit/`, `tests/integration/`, and
optionally `tests/e2e/`, with the boundary decided by what a test touches rather
than by what it is named. A unit test SHALL NOT perform I/O, network, database,
or subprocess access.

#### Scenario: Fast suite runs without external dependencies
- **WHEN** a developer runs the unit suite with no database, no network, and no
  external service available
- **THEN** every test in `tests/unit/` passes

#### Scenario: A test that crosses a real boundary is placed correctly
- **WHEN** a test exercises a real database, filesystem, HTTP call, or subprocess
- **THEN** it lives under `tests/integration/` and carries the `integration` marker

### Requirement: Test categories are selectable
The project SHALL register pytest markers so any category can be included or
excluded without knowing directory paths.

#### Scenario: Excluding slow tests during development
- **WHEN** a developer runs pytest with `-m "not integration and not e2e"`
- **THEN** only fast, dependency-free tests execute, and no marker warning is emitted

