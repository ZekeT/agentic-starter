## Purpose

Provide compact, deterministic implementation navigation for humans and fresh
agents without replacing behavioral specifications or architectural rationale.

## ADDED Requirements

### Requirement: Deterministic navigation generation
The factory map command SHALL produce a machine-readable source graph and
CODEMAP.md from supported source and optional semantic annotations. Stable inputs
SHALL produce byte-stable outputs without timestamps. Check mode SHALL detect
missing or stale artifacts without writing files.

#### Scenario: Stable generation
- **WHEN** map generation runs twice with unchanged supported source and annotations
- **THEN** both the graph and Markdown outputs are identical

#### Scenario: Stale map check
- **WHEN** supported source changes after map generation
- **THEN** map --check returns failure for stale output without rewriting it

### Requirement: Python implementation surfaces are discoverable
Python analysis SHALL expose modules, imports, top-level functions and classes,
public signatures where available, line counts, discoverable entry points, and
supported static call relationships. Approximate relationships SHALL be labeled.
Unsupported dynamic calls SHALL NOT be presented as proven edges. Unsupported
languages and analysis failures SHALL be reported explicitly.

#### Scenario: Python fixture discovery
- **WHEN** a fixture contains a public function, class, imported local call, and main entry point
- **THEN** analysis exposes those modules, symbols, import, supported call, and entry point

#### Scenario: Dynamic dispatch
- **WHEN** a call target cannot be resolved from supported static evidence
- **THEN** the map does not assert an exact relationship for that call

### Requirement: Compact diagrams and capability navigation
CODEMAP SHALL include System at a Glance, Entry Points, Major Flows, Modules,
Important Data / Contracts, Where Should I Look If..., and Generated Metrics.
It SHALL include bounded Mermaid module diagrams and flows for discoverable
entry points. Primary diagrams SHALL exclude stdlib and third-party nodes.
Semantic annotations SHALL support responsibilities, boundary contracts, and
capability navigation without manually duplicating symbol inventories.

#### Scenario: External dependency exclusion
- **WHEN** a local module imports both another local module and a third-party package
- **THEN** the primary dependency diagram includes the supported local edge and excludes the third-party node

#### Scenario: Large repository
- **WHEN** the repository exceeds diagram limits
- **THEN** diagrams group or limit nodes and disclose the omitted scope

### Requirement: Navigation has a distinct documentation role
CODEMAP SHALL declare itself a non-canonical navigation aid. Instructions SHALL
distinguish OpenSpec behavioral truth, design rationale, source implementation,
and CODEMAP navigation. Agents SHALL retrieve relevant sections progressively.
Completion SHALL refresh the map after targeted tests and before reviews, not
after every edit. Human review SHALL include relevant CODEMAP changes.

#### Scenario: Unfamiliar capability
- **WHEN** an agent needs to change unfamiliar behavior
- **THEN** instructions direct it to relevant specs, relevant CODEMAP sections, and identified source before broader retrieval

#### Scenario: Completion refresh
- **WHEN** implementation reaches the review boundary
- **THEN** CODEMAP is refreshed and supplied as navigation evidence rather than correctness proof
