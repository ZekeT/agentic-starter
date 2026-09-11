## Purpose

Provide implementation navigation through Graft while retaining factory review
boundaries, local-cache ownership, and independent behavioral verification.

## ADDED Requirements

### Requirement: Upstream navigation replaces custom CODEMAP tooling
The factory SHALL integrate Graft's upstream skill and CLI for code navigation.
It SHALL NOT require a factory-owned navigation analyzer, graph schema, renderer,
annotation store, factory map command, or committed CODEMAP artifact. The existing
Python maintainability counter and configurable growth policy SHALL be preserved.

#### Scenario: Navigation integration
- **WHEN** group 2 is installed
- **THEN** agents can use /graft and its CLI without depending on the retired custom CODEMAP implementation

### Requirement: Tested dependency and bounded installation
The integration SHALL select and validate a pinned Graft release and its required
Node runtime separately from application dependencies. Installation SHALL preview
repository-local changes, preserve existing project instructions and statusline,
disable automatic Graft hooks, and avoid global agent configuration changes.
Missing or incompatible dependencies SHALL produce actionable diagnostics.

#### Scenario: Existing agent configuration
- **WHEN** Graft is installed into a repository with custom instructions and hooks
- **THEN** the integration preserves them and introduces only reviewed repository-local wiring

#### Scenario: Unsupported dependency
- **WHEN** the installed Graft release or runtime does not satisfy the tested integration contract
- **THEN** validation identifies the incompatibility instead of reporting successful navigation

### Requirement: Structural navigation uses a local cache
Graft's generated graph SHALL remain an ignored, locally regenerable cache.
Mandatory navigation preparation SHALL use structural processing without model
credentials. Deep semantic enrichment SHALL remain explicitly opt-in and outside
mandatory gates. The factory SHALL NOT duplicate Graft's cache or configuration
with its own graph or semantic annotation store.

#### Scenario: Fresh checkout
- **WHEN** a developer or CI prepares navigation in a fresh checkout
- **THEN** a structural build creates the local graph without requiring committed graph files or model credentials

#### Scenario: Optional enrichment becomes stale
- **WHEN** previously enriched source changes and a structural build updates the graph
- **THEN** the mandatory freshness check passes if the structure is current, reports stale optional summaries or deep content without blocking, and preserves enrichment without requiring model credentials
- **AND** missing graphs, structural drift and invalid upstream check results still fail

### Requirement: Read-only review does not refresh navigation
Implementation completion SHALL build the structural graph after targeted tests
and before maintainability review and fresh behavioral verification. Reviewers
SHALL check freshness and disable query auto-refresh. Missing or stale graphs
SHALL return control to the implementer rather than causing reviewer mutations.

#### Scenario: Current graph
- **WHEN** a reviewer checks and queries a current graph with refresh disabled
- **THEN** source, configuration and graph contents remain unchanged

#### Scenario: Stale graph
- **WHEN** source changes after the completion-boundary build
- **THEN** the freshness check reports the stale graph and the reviewer requests implementer preparation without rebuilding it

### Requirement: Navigation remains distinct from behavioral truth
Instructions SHALL distinguish OpenSpec requirements, design rationale, source
implementation and Graft navigation. Agents SHALL use targeted retrieval and
expand scope only when needed. Human review SHALL use relevant on-demand impact
reports or optional visualization exports when structural evidence is useful;
it SHALL NOT require a committed CODEMAP diff or treat graph output as proof of
correctness. Analysis limitations SHALL be explicit.

#### Scenario: Structural change review
- **WHEN** a change moves responsibilities across modules
- **THEN** the reviewer compares relevant Graft evidence and source against accepted Code Shape and reports significant divergence

### Requirement: Integration tests validate the actual boundary
Factory tests SHALL cover the selected Graft release on representative repository
fixtures, including application Python sources, factory/harness exclusion, freshness failures,
non-mutating queries, installation preservation and credential-free structural
operation. They SHALL test integration behavior rather than reimplement or claim
complete coverage of upstream language analysis.

#### Scenario: Starter compatibility
- **WHEN** a selected release is evaluated for installation
- **THEN** its actual navigation coverage and side effects are checked before the factory claims that release is supported

### Requirement: Application-only graph scope
Navigation graphs SHALL cover the main project implementation and SHALL exclude
factory and harness tooling, including tooling outside dot-prefixed directories.
This exclusion SHALL NOT narrow the existing source-growth policy or independent
source review of tooling changes.

#### Scenario: Mixed application and factory repository
- **WHEN** navigation is prepared for a repository containing application and factory sources
- **THEN** application sources are indexed and factory/harness sources are excluded

#### Scenario: No application sources configured
- **WHEN** a repository has no application sources configured
- **THEN** navigation reports `not applicable: no application sources configured`, while growth and behavioral checks remain required and integration tests use an application fixture

#### Scenario: Application roots change
- **WHEN** configured application roots change
- **THEN** the implementer SHALL run an explicit structural build before review to apply the new scope
- **AND** upstream owns fingerprint selection and validation; the wrapper SHALL NOT inspect fingerprint files or require a single fingerprint
- **AND** freshness checks use the last-built scope rather than detecting manifest scope changes
