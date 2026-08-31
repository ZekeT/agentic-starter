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
