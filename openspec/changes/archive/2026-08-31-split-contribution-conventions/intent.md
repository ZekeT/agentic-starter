# Intent: split-contribution-conventions

## Problem
`contribution-conventions` is too coarse, and its own Purpose sentence says so:
"how work in this project is tested, **and** committed, **and** proposed for
review."

Applying ADR-0001's stated heuristic — *a capability is something you would
plausibly rewrite or delete as a unit* — the four requirements do not qualify.
"Switch from Conventional Commits to gitmoji" is a realistic change touching
requirement 4 alone and none of the others. Test layout and commit format have
independent reasons to change and different audiences: whoever writes a test,
versus whoever opens a PR.

This matters beyond tidiness. The capability is the unit of retrieval — the
whole argument for the change loop is answering "what is currently true about X?"
from the index plus one named file. A capability spanning three unrelated topics
means every reader loads all three to learn one.

## Proposed outcome
Two capabilities with single-sentence purposes and independent change axes:
`test-organisation` and `change-submission`. `contribution-conventions` retires.

The granularity rule that caught this is recorded durably, so the next capability
gets named against a test rather than an instinct.

## Affected users and systems
`openspec/specs/` only, plus the `crystallize` skill where capabilities are
actually named, and a new ADR. No code, no tests, no runtime behaviour.

## Constraints
- Requirement text must survive the move unchanged. This is a re-partition, not
  a rewrite: any edit to the text would hide the structural change inside a
  content diff.
- Must not lose the archived history of how these requirements arrived.

## Open questions
How OpenSpec handles a capability whose requirements are all REMOVED — whether
the spec file is deleted, or left empty and needing manual cleanup. Unknown
until the archive runs; this change is also the experiment that answers it.

## Areas of concern
This supersedes a rule stated in ADR-0001 six changes into the harness's life.
ADRs are append-only, so the correction is a new ADR rather than an edit —
the record of having been wrong is the point, and the sequence intent -> spec ->
implementation -> archive is what makes the mistake legible.
