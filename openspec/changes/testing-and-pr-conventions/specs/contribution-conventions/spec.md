## Purpose
Defines how work in this project is tested, committed, and proposed for review,
so that every change arrives in a shape a reviewer can check without asking the
author what they ran.

## ADDED Requirements

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
