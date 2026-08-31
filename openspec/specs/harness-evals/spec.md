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
