## Purpose

Validate and evolve software-factory installations while preserving project-owned
content and making every installation mutation reviewable and recoverable.

## ADDED Requirements

### Requirement: Unified versioned factory tooling
Doctor, maintainability, adopt, and update SHALL share one consistent interface and the
existing manifest/version convention. Factory tooling and project configuration
SHALL require Python 3.12+. Existing migration/update entry points SHALL use the
same lifecycle decisions and explain incompatible legacy options. No alternate
entry point SHALL bypass project-ownership preservation.

#### Scenario: Unsupported interpreter
- **WHEN** a lifecycle command is invoked on Python older than 3.12
- **THEN** it reports the requirement and exits before modifying the target

#### Scenario: Legacy force request
- **WHEN** legacy migration force mode would replace conflicting project content
- **THEN** it refuses that overwrite and directs the user to conflict resolution

### Requirement: Fast actionable installation health checks
Doctor SHALL validate manifest parsing and version, required directories,
commands, hook wiring, relevant executable bits, OpenSpec structure, gitignore
and environment protections, managed metadata consistency, maintainability
configuration and exceptions, Graft dependency/wiring configuration, and eval configuration.
Findings SHALL include severity and remediation. Doctor SHALL NOT mutate source
or invoke the full gate. The starter SHALL pass as an ordinary installation.

#### Scenario: Missing structure
- **WHEN** a required command or hook is missing
- **THEN** doctor fails and identifies the missing path and remediation

#### Scenario: Invalid configuration
- **WHEN** the manifest contains malformed configuration or an unsupported schema
- **THEN** doctor fails with an actionable diagnostic

#### Scenario: Stale navigation
- **WHEN** the local Graft graph is stale but installation structure is valid
- **THEN** doctor reports a warning directing the user to rebuild the local structural graph

### Requirement: Explicit ownership and preserved project configuration
Managed content SHALL have explicit full-file or bounded ownership and upstream
fingerprints. Application source, existing CI, and project documentation SHALL
remain project-owned. Mixed instruction/build files SHALL preserve content
outside managed regions. Project configuration overrides SHALL survive manifest
regeneration and update. Installation state SHALL NOT duplicate workflow status.

#### Scenario: Custom instructions
- **WHEN** adoption adds factory guidance to existing CLAUDE.md or AGENTS.md
- **THEN** project instructions remain intact outside an identified managed region

#### Scenario: Project thresholds survive an update
- **WHEN** factory metadata is refreshed in a project with custom thresholds
- **THEN** its configured warning, maximum, and growth values remain unchanged

### Requirement: Inspection-first non-destructive adoption
Adopt SHALL default to a read-only plan classifying ADD, MERGE, PRESERVE, CONFLICT,
and SKIP. It SHALL inspect supported language/tool signals, canonical checks,
instructions, hooks, CI, gitignore, and repository structure. It SHALL propose
only evidenced commands and preserve canonical project tooling. Apply SHALL be
explicit, revalidate current inputs, and refuse unresolved conflicts before writes.

#### Scenario: Plan leaves target unchanged
- **WHEN** adopt runs without apply against an existing repository
- **THEN** it prints its inspection and proposed actions without modifying any target file

#### Scenario: Existing canonical check
- **WHEN** an existing repository defines make check
- **THEN** adoption preserves that command and proposes compatible factory integration

#### Scenario: Uncertain build tooling
- **WHEN** inspection cannot determine a supported check command
- **THEN** the plan states the unresolved configuration rather than inventing a command

### Requirement: Fingerprint-based deterministic updates
Update SHALL compare local and incoming owned content against its recorded
upstream baseline. It SHALL replace unchanged local content when upstream changes,
preserve local changes when upstream does not change, and report dual-change
conflicts without overwriting them. Already converged content SHALL be recognized.
Locally deleted owned files SHALL be treated as local changes. Unknown legacy
customizations SHALL NOT be assigned a pristine baseline without evidence.

#### Scenario: Safe upstream replacement
- **WHEN** local owned content matches its baseline and upstream changes
- **THEN** the update plan proposes replacing that owned content

#### Scenario: Local customization only
- **WHEN** local owned content changes and upstream matches its baseline
- **THEN** update preserves the customization

#### Scenario: Dual-change conflict
- **WHEN** local and upstream content both diverge from the baseline and each other
- **THEN** update reports a conflict without overwriting or advancing that entry's baseline

#### Scenario: Managed section update
- **WHEN** an unchanged owned section receives upstream changes
- **THEN** update replaces only the section and preserves surrounding project content

### Requirement: Recoverable and validated application
Adopt/update apply SHALL require a clean committed Git target unless an equally
safe recovery path is explicitly implemented. Plans SHALL reject unsafe paths,
symlink escapes, and malformed ownership regions. Applied changes SHALL remain
uncommitted, with recovery baseline and affected paths reported. Successful apply
SHALL run doctor and report relevant Graft freshness/eval follow-up. Failed postchecks or
partial writes SHALL be reported as failures, not successful installation.

#### Scenario: Dirty target
- **WHEN** apply targets a repository with uncommitted changes
- **THEN** it refuses mutation and explains how to prepare a recoverable target

#### Scenario: Conflict before application
- **WHEN** a plan contains an unresolved conflict
- **THEN** apply writes no target files and identifies the required resolution

#### Scenario: Post-apply validation fails
- **WHEN** doctor fails after files are applied
- **THEN** the operation reports failure, affected paths, and recovery information

### Requirement: Deterministic installation regression coverage
Static evals and fixture tests SHALL cover invalid doctor inputs, safe adoption
planning, instruction preservation, fingerprint update outcomes, and starter
health. Static evaluation SHALL require no credentials. Maintainer documentation
SHALL describe manifest refresh, Graft structural build/check, doctor, full gates, and evals
without recursive command dependencies.

#### Scenario: Credential-free lifecycle validation
- **WHEN** the static factory suite runs without model credentials
- **THEN** deterministic installation checks run and report their actual outcomes
