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
