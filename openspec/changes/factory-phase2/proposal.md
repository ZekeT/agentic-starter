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
- Generate a normalized Python source graph and compact Markdown/Mermaid
  `CODEMAP.md`; refresh it before independent reviews.
- Add one factory interface for doctor, map, adopt, and update, extending the
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
- `factory-codemap`: deterministic implementation navigation and lifecycle
  refresh, without assuming behavioral or architectural authority.
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
evals. Retains stdlib-only bootstrap tooling and the existing human shipping gate.
Source requirements are `idea.md`, amended by the decisions in `intent.md`.
