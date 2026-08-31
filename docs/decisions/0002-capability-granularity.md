# 0002 — Capability granularity

- **Status**: Accepted
- **Date**: 2026-08-31
- **Supersedes**: the capability-granularity heuristic in [0001](0001-adopt-openspec-change-loop.md) (that ADR stands in every other respect)

## Context

ADR-0001 left one question open, and said so: how big is a capability in
`openspec/specs/`? Its working heuristic was *a capability is something you would
plausibly rewrite or delete as a unit*, explicitly flagged as untested and to be
pressure-tested on the first two real changes.

Two changes have now landed. The heuristic held for one and failed for the other.

`harness-evals` passes: two requirements, a one-sentence purpose, and if the eval
suite were dropped both would go together.

`contribution-conventions` fails, and its own Purpose sentence gives it away —
"how work in this project is tested, **and** committed, **and** proposed for
review." Under the heuristic, *"switch from Conventional Commits to gitmoji"* is a
realistic change touching one of its four requirements and none of the others.
Test layout and commit format have independent reasons to change and different
audiences: whoever writes a test, versus whoever opens a PR.

Two things are worth recording about that failure. The signal was present at
authoring time, in the capability's own first sentence, and was not acted on — so
the problem is not that the heuristic is unusable but that nothing prompted anyone
to run it. And the heuristic asks an *implementation* question (would you rewrite
this code together?) about a *behaviour* artifact. Code and behaviour do not share
seams, which is why the answer can be misleading.

The stakes are retrieval, not tidiness. The capability is the unit of lookup: the
entire argument for the change loop is answering "what is currently true about X?"
from `openspec list --specs` plus one named file. A capability spanning three
unrelated topics forces every reader to load all three to learn one.

## Decision

Replace the single heuristic with three tests, applied in order of cost. A
capability is right-sized when it passes all three.

**1. The naming test.** The Purpose must be one sentence that does not use "and"
to join unrelated activities, and the name must not be a generic container noun —
`core`, `platform`, `utils`, `management`, `handling`, `common`. Run this before
committing a new capability; it costs nothing and catches most cases, including
the one above.

**2. The independent-change test.** Try to name a realistic change that touches
exactly one subset of the requirements and none of the others. If you can, that
subset is a separate capability. This is the decisive test, and it replaces
"rewrite or delete as a unit" — it asks about behaviour changing, not code
changing.

**3. The touch-count test.** Across `openspec/changes/archive/`, count capabilities
touched per change. Mostly one is healthy. Mostly three or more means capabilities
are too fine. Changes repeatedly touching a small slice of one large capability
means it is too coarse. This is the only signal that is empirical rather than a
matter of taste, and it needs history before it says anything.

Two supporting rules:

**Capabilities are not modules.** One capability may span modules; one module may
serve several. If the capability list mirrors the directory tree exactly, the
specs describe the implementation, and they will churn on every refactor without
any behaviour having changed.

**Start coarse; split when a change reveals the seam.** Seams are not knowable in
advance. A too-coarse capability announces itself loudly, in its own purpose
sentence. A too-fine taxonomy is quietly annoying forever and multiplies —
twenty wrong small capabilities is a worse mess than four slightly large ones.

Nesting (`domain/capability`) earns its keep once the flat list stops scanning,
around eight to ten entries. Nest by domain (`billing/invoicing`), never by layer
(`api/billing`) — layers are implementation.

## Consequences

**Gained.** A test that runs at authoring time, in the `crystallize` skill's
classification step, rather than a principle recalled after the fact. The
touch-count test gives a measurable health signal as history accumulates.

**Cost.** Three tests instead of one aphorism. Test 3 is useless early, when
`archive/` is nearly empty — which is exactly when the taxonomy is being set. The
naming test carries the load until then.

**Applied immediately.** `contribution-conventions` splits into
`test-organisation` and `change-submission`, with requirement text moved
unchanged so the diff reads as a re-partition rather than a rewrite.

**Observed while doing it — a capability cannot be retired by a delta.** The
first attempt expressed the retirement as a `REMOVED` delta covering all four
requirements. `openspec archive` refused it:

```
Validation errors in rebuilt spec for contribution-conventions (will not write changes):
  ✗ Spec must have at least one requirement
Aborted. No files were changed.
```

The abort is clean — nothing partially applied — but it means **splitting a
capability is two operations, not one**: archive the change that ADDs the new
capabilities, then `git rm` the old spec directory by hand in the same commit.
A `REMOVED` delta works for dropping *some* requirements; it cannot empty a
capability. Anyone planning a split should know this before writing the delta,
because the failure arrives at archive time, after the specs are written.

**Still unresolved.** The touch-count thresholds are asserted, not derived. Both
changes so far touched exactly one capability, which is consistent with a healthy
taxonomy but is also what you would expect from two changes designed by someone
who already knew the capability. Revisit once ten changes have archived.
