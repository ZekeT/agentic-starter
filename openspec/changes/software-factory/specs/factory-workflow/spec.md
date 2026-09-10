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
