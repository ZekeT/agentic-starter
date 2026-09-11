## Purpose

Keep implementation growth and module boundaries reviewable through configurable
deterministic checks and independent, actionable maintainability review.

## ADDED Requirements

### Requirement: Configurable code-line growth policy
The factory SHALL default to warning above 300 code lines and a maximum of 500
code lines. It SHALL define substantial growth as at least 150 net added code
lines. All three values and enabled state SHALL be project-configurable. Python
code-line counts SHALL exclude blank lines, comment-only lines, and docstring-only
lines. Existing files above the maximum SHALL fail for substantial growth; new
files above the maximum SHALL fail. Smaller growth of existing oversized files
SHALL warn rather than fail solely because of size.

#### Scenario: New oversized source
- **WHEN** a new handwritten Python file contains 501 code lines without an exception
- **THEN** the check fails and identifies its size, maximum, and remediation

#### Scenario: Warning boundary
- **WHEN** a new file has 301 code lines under default configuration
- **THEN** the check warns without failing solely because of size

#### Scenario: Existing substantial growth boundary
- **WHEN** an existing file grows from 600 to 750 code lines without an exception
- **THEN** the check fails because it exceeds the maximum and gained 150 code lines

#### Scenario: Existing smaller growth
- **WHEN** an existing file grows from 600 to 749 code lines
- **THEN** the size check warns rather than failing solely because of size

#### Scenario: Documentation is excluded
- **WHEN** only blank lines, comments, or Python docstrings enlarge a file
- **THEN** its reported code-line growth remains zero

### Requirement: Diff-aware evidence and explicit analysis scope
Verification SHALL compare changed source with the configured merge base and
include staged, unstaged, and non-ignored untracked source. Output SHALL identify
file, current count, available base count, growth, and threshold status. Missing
history and unsupported analysis SHALL be explicit. Unrelated pre-existing large
files SHALL NOT cause unrelated changes to fail. Invalid Python source SHALL NOT
be treated as a zero-line successful analysis.

#### Scenario: Untracked file is checked
- **WHEN** verification includes a new non-ignored untracked source file
- **THEN** the growth check evaluates it as new source

#### Scenario: Unrelated large file
- **WHEN** a change leaves an existing 1100-code-line file unchanged
- **THEN** that file does not cause the change to fail

#### Scenario: Renamed file
- **WHEN** Git identifies an unchanged oversized source file as a rename
- **THEN** verification retains its existing-file baseline rather than failing it as new

### Requirement: Reasoned checked-in exceptions
Exceptions SHALL require unique repository-contained existing file paths and
nonempty reasons. Doctor SHALL reject malformed entries, nonexistent paths, and
wildcard exceptions. Valid exceptions SHALL be visible in check output. Invalid
threshold types or ordering SHALL fail configuration validation.

#### Scenario: Generated source exception
- **WHEN** a 1500-line generated file has a valid path-specific reasoned exception
- **THEN** size enforcement exempts it and reports the reason

#### Scenario: Invalid exceptions
- **WHEN** exceptions contain a duplicate path, missing path, empty reason, or wildcard
- **THEN** doctor fails with the offending entry and an actionable correction

### Requirement: Code-shape planning and narrow independent review
New DEEP program designs SHALL describe reused modules, new responsibilities and
public surfaces, existing modules intentionally not extended, and rough expected
footprint. STANDARD designs SHALL permit an abbreviated form. A fresh read-only
maintainability reviewer SHALL inspect the diff, relevant accepted design, nearby
modules, and static output without implementation narrative. It SHALL report PASS
or CONCERNS, with identifiers, locations, problems, consequences, and specific
suggested directions. Structural drift SHALL be a review concern, not automatic
proof of behavioral failure. Recommendations SHALL avoid speculative abstraction
and meaningless file fragmentation.

#### Scenario: Implementation diverges structurally
- **WHEN** accepted design separates responsibilities but implementation concentrates them in one large module
- **THEN** the reviewer reports the divergence, consequence, and suggested boundary without editing code

#### Scenario: No actionable concern
- **WHEN** independent review finds no maintainability concern requiring review
- **THEN** it reports PASS with a concise explanation

### Requirement: Maintainability joins existing completion boundaries
STANDARD and DEEP completion SHALL run targeted tests, Graft structural build, maintainability
review, fresh behavioral verification, and human review in that order. Concerns
SHALL return to the implementer or human. FAST SHALL permit skipping semantic
maintainability review, while deterministic growth checks remain in the full gate.
Policy SHALL be referenced rather than copied into every instruction document.

#### Scenario: FAST completion
- **WHEN** a truly small FAST change skips the semantic reviewer
- **THEN** its full verification gate still runs deterministic growth checks

#### Scenario: Reviewer raises concerns
- **WHEN** maintainability review reports CONCERNS
- **THEN** control returns for resolution or an explicit human disposition before shipping
