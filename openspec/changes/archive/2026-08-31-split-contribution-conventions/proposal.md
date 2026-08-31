## Why
`contribution-conventions` bundles two capabilities with independent change
axes. Its Purpose sentence needs "and" twice to describe itself, which is the
cheapest available signal that a capability is too coarse — and it was visible
when the capability was written, one change ago.

Splitting now is deliberate timing: the file holds four requirements, so the
re-partition is small and reviewable. Every requirement added before the split
makes it larger and less likely to happen.

## What Changes
- **BREAKING** for anyone referencing the capability path: `contribution-conventions`
  is retired. Its requirements move, unchanged, into two new capabilities.
- `test-organisation`: how tests are separated and selected.
- `change-submission`: how a change is committed and proposed for review.
- Records the sharpened granularity rule in `docs/decisions/0002`, superseding
  the heuristic stated in ADR-0001.
- Adds the rule to the `crystallize` skill's classification step, which is the
  moment a capability actually gets named.
- Not architecture-affecting.

## Capabilities

### New Capabilities
- `test-organisation`: how tests are separated by what they touch, and selected by marker
- `change-submission`: how work is committed and proposed for review

### Modified Capabilities

None. Retiring `contribution-conventions` cannot be expressed as a delta:
`openspec archive` refuses to write a spec with zero requirements, so a `REMOVED`
delta covering all four aborts the archive. The capability is therefore retired
by deleting its spec file by hand after the archive, as a separate step in the
same commit.

## Impact
`openspec/specs/` only, plus `.claude/skills/crystallize/SKILL.md` and
`docs/decisions/`. No source, no tests, no runtime behaviour. Requirement text
is moved verbatim so the diff shows a re-partition rather than a rewrite.
