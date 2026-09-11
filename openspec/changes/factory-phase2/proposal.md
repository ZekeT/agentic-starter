## Why

The factory cannot currently detect harmful file growth, generate implementation
navigation, or validate an installation. Its separate migration/update paths and
whole-file template ownership make preserving downstream customizations harder.

## What Changes

- Add a short maintainability contract, configurable code-line growth checks,
  reasoned exceptions, and a fresh read-only maintainability reviewer.
- Default to a 300-code-line warning, 500-code-line maximum, and 150 net added
  code lines for substantial growth of existing oversized files.
- Require Code Shape planning for new DEEP program designs; surface structural
  divergence as review concerns rather than behavioral failures.
- Integrate upstream Graft through `/graft` and its CLI for implementation
  navigation of the project application only, excluding factory and harness tooling.
  Build its local structural cache before reviews; use on-demand
  change-impact reports or visualization rather than a committed CODEMAP.
- Remove the proposed in-house analyzer, graph schema, renderer and annotation
  store. Keep semantic enrichment optional and independent reviews non-mutating.
- Add one factory interface for doctor, maintainability, adopt, and update, extending the
  existing lifecycle implementation and manifest rather than replacing them
  with a parallel framework.
- Add explicit full-file, bounded-section, and preserve ownership plus
  installation-specific upstream fingerprints.
- **BREAKING**: require Python 3.12+ for the project and factory tooling.
- **BREAKING**: legacy migration force mode must no longer bypass protection of
  project-owned or conflicting content; report actionable conflicts instead.

## Capabilities

### New Capabilities

- `factory-maintainability`: source-growth enforcement, exceptions, code-shape
  planning, and independent maintainability review.
- `factory-navigation`: Graft-backed navigation, local-cache freshness and
  review evidence, without assuming behavioral or architectural authority.
- `factory-installation`: healthy installation validation, ownership-aware
  adoption, and safe factory updates.

### Modified Capabilities

None of the current canonical capabilities changes. The Phase 1 workflow and
verification deltas remain in their existing change until separately archived;
the new capabilities add requirements without rewriting those pending deltas.

## Impact

Workflow: DEEP. Architecture-affecting: yes, shared lifecycle ownership and new
verification/navigation boundaries. Affects harness scripts, template packaging,
agent instructions, workflow docs, Python configuration, CI, and static/fixture
evals. Factory-owned tooling remains stdlib-only; navigation adds the external
`@nanonets/graft` package and Node.js 20+. Preserve the existing human shipping
gate. Pin and validate the dependency during integration, rather than implicitly
tracking upstream latest.
Source requirements are `idea.md`, amended by the decisions in `intent.md`.

### Approved skill-only integration — 2026-09-11

Graft 0.18.0's Claude installer adds hooks despite `--no-hooks`. The user approved
installing only its unchanged upstream skill and isolated CLI. Preview skill
installation, preserve customized skill files, and do not run upstream `init`.
The generated skill stays upstream-owned and ignored; `make graft-install`
regenerates it from the locked package without hooks, MCP or global agent wiring.

The factory's `.harness/bin/graft` launcher delegates through `factory navigation`
to the thin `graft.py` boundary. `project.navigation.application_roots` in the
existing manifest records the explicit application input list (empty in this
starter), forwarded as upstream `--only-dir` options. Graft still owns all graph
and cache formats. The launcher checks the pinned release, disables dotenv and
query refresh, and detects a mismatch with upstream's cached scope metadata.
This input list is not an alternate graph/configuration store. Supported review
commands are check, ask, grep, skeleton, callers, map and blast; structural build
and explicit optional `build --deep` belong to the implementer. Upstream visual
exports remain optional, outside the required read-only command surface.
