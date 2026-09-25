# Approved v3.1b implementation slices

Status: in progress — tickets 01–07 merged; ticket 08 implementing with all prerequisites integrated

Source: [specification](spec.md).

## Delivery status — reconciled 2026-09-25

| Ticket | Status | PR |
| --- | --- | --- |
| 01 | Completed / merged | [#22](https://github.com/ZekeT/agentic-starter/pull/22) |
| 02 | Completed / merged | [#23](https://github.com/ZekeT/agentic-starter/pull/23) |
| 03 | Completed / merged | [#24](https://github.com/ZekeT/agentic-starter/pull/24) |
| 04 | Completed / merged | [#25](https://github.com/ZekeT/agentic-starter/pull/25) |
| 05 | Completed / merged | [#26](https://github.com/ZekeT/agentic-starter/pull/26) |
| 06 | Completed / merged | [#27](https://github.com/ZekeT/agentic-starter/pull/27) |
| 07 | Completed / merged | [#28](https://github.com/ZekeT/agentic-starter/pull/28) |
| 08 | In progress; v3.1 issue 05 merged in #30, 05–07 delivered | — |

Merge evidence comes from local Git history. Individual tickets retain the
implementation evidence and delivery links.

Each slice includes its behavior, relevant policy/runtime integration, user
guidance, behavioral coverage and required verification. Documentation and evals
must remain consistent as each slice lands; the final journey slice is not a
reason to postpone those updates. Preserve pinned upstream skills unchanged.

1. **Verify a shippable change once and reuse its evidence**
   - Blocked by: None.
   - Deliver: implementation retains scoped local commits and hands off to fresh
     independent engineering verification. Review obtains missing/stale evidence
     and presents current results without repeating them. Local ignored records
     cover intended committed/uncommitted/new content, comparison base, check
     inputs and relevant tool/dependency versions. Content-preserving commits do
     not invalidate evidence. Missing independent execution produces an explicit
     fresh-session handoff, never PASS.
   - Demo: implement a small change, review it from a fresh session, and observe
     evidence reuse; modify content or a relevant input and observe revalidation.
   - Boundary: initially refuse verification when unrelated edits could contaminate
     its inputs; do not claim exact-scope proof until slice 02 supplies isolation.
     Existing shipping remains conservative until slice 04.

2. **Verify the proposed PR while preserving unrelated local work**
   - Blocked by: 01.
   - Deliver: construct an isolated verification checkout of the exact proposed
     content when unrelated edits could affect results. Include intended new and
     uncommitted files, run required checks/reviews there, and associate evidence
     with that content. Preserve the user's files without requiring stash/commit.
   - Demo: a test passes only because of an unrelated local edit; isolated
     verification correctly rejects the proposed change and leaves local work intact.

3. **Resolve review findings without reopening settled work**
   - Blocked by: 01.
   - Deliver: read-only review explains what/why/how/recommendation/rationale,
     separates concrete blockers from preference-only nits, and waits for human
     fix instructions. Authorized fixes rerun authoritative checks and receive
     independent inspection of affected behavior, preserving justified unaffected
     evidence. Present refreshed acceptance scope. Pause for focused grill-me on
     conflicting decisions or two failed attempts at the same finding; record the
     resolution before resuming. Material scope expansion returns to planning.
   - Demo: correct a finding without a new ticket; then exercise a proposed fix
     that would undo an agreed decision and observe the human decision checkpoint.

4. **Publish accepted content as an actual PR/MR**
   - Blocked by: 02, 03.
   - Deliver: ship consumes current verification and completed acceptance review;
     invocation authorizes the presented unchanged scope. Reuse implementation
     commits, commit only remaining accepted fixes, push, create the provider's
     PR/MR and report its URL. Enforce scope, blockers, hooks and freshness without
     repeating unchanged semantic review/checks. Respect narrower requests and
     separate merge/force-push authorization. Missing prerequisites return to the
     appropriate gate; unrelated work stays untouched.
   - Demo: an implementation commit plus verified uncommitted correction produces
     one PR through a fake provider; stale evidence and mutating hooks prevent
     publication of unverified content.

5. **Resume publishing after a failed push or PR request**
   - Blocked by: 04.
   - Deliver: report exactly which publication steps succeeded and resume using
     current evidence and existing authorization. A failed push after a local
     commit is retried without recreating the commit or reviewing unchanged work.
     Recognize completed pushes and existing PRs, including uncertain responses,
     to avoid duplicates. Never recover by automatic force-push.
   - Demo: simulate failed transport, restore it, rerun ship, and observe one
     commit and one PR with no unnecessary repeated verification.

6. **Start a migration-free application without manifest chores**
   - Blocked by: v3.1 issue 04 — clean consumer template.
   - Deliver: build the consumer payload without migration implementation, skills
     or legacy baselines, while setup, doctor and ordinary application gates still
     work. Preserve external brownfield migration from an Engineering checkout.
     Ordinary application edits require no manifest regeneration; retain maintainer
     distribution integrity. Do not strip existing installations automatically.
   - Demo: generate and initialize a fresh project, change application behavior,
     run normal gates without make manifest, and exercise external migration.

7. **Close an accepted brownfield migration explicitly**
   - Blocked by: v3.1 issue 03 — approved finalization.
   - Deliver: audit delivered finalization and add only missing accepted/cleanup
     pending/closed outcomes. Show exact temporary removal scope, honor human
     authorization and retained snapshots, refuse unsafe deletion of changed
     artifacts, and support safe retries. Ordinary development remains independent
     of migration artifacts. Preserve validation, rollback and unresolved-decision
     protections; no general migration redesign.
   - Demo: accepted migration closes by approved cleanup or explicit retention;
     changed artifacts are preserved and missing validation prevents completion.

8. **Prove and document the complete greenfield journey**
   - Blocked by: 05, 06, 07; v3.1 issue 05 — onboarding documentation/verification.
   - Deliver: lead the guide with onboarding, implement/review/ship, human-observable
     outcomes, corrections and failed-push recovery; place protocol/maintainer
     detail beneath it. Exercise the complete journey in a disposable generated
     application, including independent verification and a human-directed fix.
     Verify assembled policy/eval consistency and external brownfield guidance;
     record observed behavior and limits, not just static assertions.
   - Demo: a new user can follow the guide from setup to publishing handoff without
     migration scaffolding, manifest chores or duplicate gates.

## Dependency notes

Slices 01, 06 and 07 are separate work streams subject to the listed external
prerequisites. Slice 03 does not depend on isolation; its first demo can use a
checkout without unrelated edits. Slices 06 and 07 do not depend on each other:
external migration availability and migration closure are separate behaviors.
Final integration proves their compatibility with the daily loop.

v3.1 issue status text is not acceptance evidence. Confirm the required behavior
is delivered and integrate its changes before starting dependent work. Coordinate
shared-file edits even where there is no semantic blocking edge. Do not modify
v3.1's approved tickets or the parent specification while publishing this breakdown.
