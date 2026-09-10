---
name: shape-change
description: >
  Translate accepted DEEP architecture and delta specs into program-design.md
  and independently shippable vertical task groups. Use /shape-change with a change slug
  after the crystallize architecture gate; not for FAST or existing STANDARD tasks.
---

# Shape change

Announce: **"Using shape-change to prepare `<slug>` for implementation."**

Read the change's intent, proposal, architectural design, and relevant delta
specs. Confirm the DEEP design/spec gate was accepted; if acceptance is unknown,
stop and ask. If architecture or behavior is still undecided, explain the issue,
why it blocks slicing, and a suggested next decision or spike. Do not guess.
Existing STANDARD changes with populated `tasks.md` go straight to `/dev-change`.
Do not overwrite existing accepted program design or final tasks without asking.

Inspect only source, feature instructions, and integration boundaries needed to
translate the accepted architecture. Do not invoke generic brainstorming,
writing-plans, or Superpowers orchestration. The factory owns decomposition.

## Write program-design.md

Create `openspec/changes/<slug>/program-design.md` with implementation-relevant
information only. Reference architecture/spec sections instead of copying them.
Use this structure, omitting migration details when irrelevant:

```markdown
# Program Design

## Code Shape
### Existing modules reused
- Path and reason
### New modules
- Path, responsibility and intended public surface
### Existing modules intentionally not extended
- Path and reason
### Expected implementation footprint
- Expected changed/created files and rough size/complexity, not exact LOC

## Implementation shape
### Files to create
- Path and responsibility
### Files to modify
- Path and intended change

## Important types and interfaces
- Type/interface/signature, responsibility, relevant invariants

## Data and control flow
1. Input, processing, state changes and output

## Integration boundaries
- Callers, external contracts, failure boundaries

## Test design
### Behavior tests
- Scenario → test and observable assertion
### Failure cases
- Failure → expected outcome
### Neighbouring regression risks
- Existing flow → why it could break and how to check it

## Migration / compatibility
- Safe rollout, backwards compatibility, rollback (if relevant)

## Least-confident decisions
- Decision, uncertainty, consequence if wrong
```

## Write tasks.md

Use `openspec instructions tasks --change <slug>`, then create
`openspec/changes/<slug>/tasks.md` with `## N.` groups and unchecked `N.M` tasks.
Each group is a vertical, independently shippable slice: one group = one branch
= one PR. Include its tests and integration, and explain the safe shipping
boundary. Record prerequisite groups; dependent groups wait for their merge.

Prefer complete read-only user flow, mutation with validation, migration/backfill
support when those can ship safely. Do not split database/backend/frontend/tests
into separate groups if none can ship independently. If independent slices are
impossible under the accepted design, stop and surface that constraint.

Each group includes a `Context:` list referencing exact relevant delta-spec
scenarios, design/program-design sections, and feature instructions. This makes
the group executable in a fresh session without loading the full program design.
Do not create another plan or workflow-status database.

Run `openspec validate <slug>`. Present both artifacts, the slice boundaries,
dependencies, and least-confident decisions for human review. Stop without
implementing or committing. After acceptance, the next command is
`/dev-change <slug> 1`. Artifacts plus repository state must suffice for that
fresh implementation session.
