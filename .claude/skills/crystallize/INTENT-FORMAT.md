# intent.md Format

The shape of the first commit's artifact. Loaded when you reach §4, not before —
the classification and separation passes do not need it.

Every section is filled from the separation pass in §3. An empty **Open questions**
is almost always a sign the input was not interrogated, not that nothing is open.

```markdown
# Intent: <slug>

## Problem
What is wrong today. Observable, not aspirational. If you can't state the
problem without naming the solution, you don't have one yet.

## Proposed outcome
What is true after this ships. Still no implementation.

## Affected users and systems
Who notices, and what else this touches.

## Constraints
Budget, compatibility, deadline, regulatory — anything that bounds the solution.

## Open questions
The unknowns from step 3. Empty is a red flag on anything non-trivial.

## Areas of concern
Conflicts with existing ADRs, specs, or policies encoded in skills. State them
here even if you think they're acceptable — this is the section a reviewer
reads first.
```
