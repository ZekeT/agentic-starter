<!--
GitHub loads this automatically for every PR. /commit-push-pr fills it in.

Delete any section that genuinely does not apply, and say why in one line —
an empty heading tells a reviewer nothing, and a deleted one with no reason
looks like an oversight.
-->

## What & why

<!-- What changes, and the problem it solves. The diff shows what; this says why. -->

**Change:** `<slug>` · task group `<N>`
<!-- Or "none — <reason>" for a hotfix or chore outside the change loop. -->

## How this was tested

<!-- REQUIRED. A reviewer must be able to tell what was actually verified.
     "Tested locally" is not evidence. Delete the categories that don't apply. -->

**Automated**

- [ ] `make check` passes
- Unit: <!-- which tests cover the new behaviour, by name or path -->
- Integration: <!-- which boundaries this exercises for real, if any -->

**Manual**

<!-- Only where automation isn't practical. Record steps AND the observed
     result, so someone else could repeat it:

     1. `make run`, opened http://localhost:8000/invoices
     2. Submitted an invoice for -5.00
     3. Observed: rejected with "Amount must be positive"; no DB row written
-->

_Not applicable — <reason>._

**Not covered**

<!-- Be honest about what this change does NOT verify. This is the most useful
     line in the template: it tells the reviewer where to actually look. -->

## Spec compliance

<!-- The pass this harness exists to enable — see REVIEW.md Pass 3. -->

- [ ] Every `#### Scenario:` in the change's delta specs is satisfied
- [ ] The diff does nothing the specs don't describe (or the extra is called out above)
- [ ] `tasks.md` updated in the same commit if implementation departed from it
- [ ] `openspec/specs/` not edited directly (it changes only via `/archive-change`)

## Risk

<!-- What breaks if this is wrong, and how it's rolled back. One or two lines.
     "Low risk" on its own is not an assessment. -->

**Breaking changes:** <!-- none / describe the migration path -->
