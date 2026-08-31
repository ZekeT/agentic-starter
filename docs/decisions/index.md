# Decisions

Architectural decision records. **Append-only**: one decision per file, never
edited once merged. A decision that turns out wrong gets a *new* ADR that
supersedes the old one — the record of having been wrong is the point.

## Convention

- Filename: `NNNN-slug.md`, zero-padded, allocated in merge order
- Sections: **Context** (the forces, including what you didn't know) →
  **Decision** (what was chosen, in the active voice) → **Consequences** (what
  this costs, not just what it buys)
- Status: `Accepted` · `Superseded by NNNN` · `Deprecated`
- Write one when a choice constrains future changes. Routine choices that a
  future reader would never question don't need one.

An ADR records *why*. What the system currently does is `openspec/specs/`; what
shape it has is `docs/architecture.md`.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-adopt-openspec-change-loop.md) | Adopt the OpenSpec change loop | Accepted |
