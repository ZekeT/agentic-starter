---
description: Obtain current independent evidence and summarize it for human review.
---

Read REVIEW.md and .engineering/docs/verification.md. Discover the comparison
base, full intended committed/staged/unstaged/new scope and agreed request or
spec/ticket. Use .engineering/scripts/lib/change.sh for base discovery.

Inspect the saved verification plan against the actual request and scope; PASS
for another plan is not evidence for this change. Use engineering verify status.
Reuse current complete evidence without rerunning checks or reviews. If absent,
missing/stale or incomplete, prepare the current plan and launch fresh independent
maintainability and behavioral reviewers, plus security review when applicable.
The verifier runs engineering verify check and reports observed behavior
independently. Record their actual reports using the prepared snapshot; never
fabricate independent reports or turn implementer reasoning into proof.

If fresh execution is unavailable, report INCOMPLETE with the branch/request
pointer, plan and missing roles for a fresh session. Prepare creates an isolated
checkout of the exact proposed content, excluding unrelated working edits. All
reviewers inspect its reported checkout path; verify check runs there. Do not
stash or commit unrelated work. Preparation failures leave proof INCOMPLETE.

Summarize changed behavior, coverage, risks, actual checks, independent findings
and gaps. Missing proof is not PASS; PASS is not human acceptance. Use show-me
when useful. Do not edit application content, format, refresh Graft, rerun
upstream development methodology or ship. Local evidence/check artifacts are
permitted. Ship retains its existing final gate.

Apply REVIEW.md's finding format and bounded correction policy. Consult settled
decisions; keep preference-only alternatives non-blocking. Wait for human
instructions identifying fixes before editing. Subsequent authorized corrections
follow the incremental evidence procedure; present updated acceptance scope.
Pause after two unsuccessful attempts at one finding or before undoing a settled
decision, use focused `/grill-me`, and record the human-agreed resolution first.
Material scope expansion returns to `/to-spec` and `/to-tickets`.
