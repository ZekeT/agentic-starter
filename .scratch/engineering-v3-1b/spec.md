# Engineering v3.1b — Greenfield development without repeated gates

Status: ready-for-agent — shared understanding and testing boundaries approved

## Problem Statement

Developers using the starter for a new application encounter repeated checks,
unclear review and shipping handoffs, maintainer-only chores, and unnecessary
migration tooling. Review corrections can trigger many rounds of further review,
sometimes undoing working behavior or reopening settled decisions. A local commit
can be mistaken for verification, while uncommitted review fixes can escape the
evidence used to publish a PR.

The primary need is a simpler greenfield development journey. Brownfield cleanup
is a bounded follow-on to existing migration work, not the center of this change.

## Solution

Make `/implement → /review → /ship` the canonical daily loop. Separate Build,
Verify, Accept and Publish responsibilities while allowing commands to obtain
missing prerequisite evidence. Later gates consume current earlier evidence
instead of repeating it.

Preserve upstream implementation behavior, including local commits. Obtain
independent verification of the complete proposed PR content. Present findings
clearly, wait for human direction, fix only the authorized scope, and reverify the
affected behavior. Publish the accepted content through an actual PR/MR, resuming
safely after transport failures. Fresh templates contain ordinary application
engineering support; migration capabilities remain available externally.

## User Stories

1. As a greenfield developer, I want a clear implement, review and ship loop, so that I can develop without learning internal protocols first.
2. As a developer, I want upstream planning skills to define demoable slices, so that the harness does not become another ticket planner.
3. As a reviewer, I want a shippable change to identify the complete proposed PR scope, so that verification and acceptance refer to the same result.
4. As a human tester, I want a runnable demonstration or observable behavior where practical, so that I can assess a change directly.
5. As a developer, I want `/implement` to retain its local commit behavior, so that the starter works with upstream skills.
6. As a project owner, I want local commits distinguished from acceptance and publication, so that implementation cannot silently authorize shipping.
7. As a developer, I want independent verification after implementation, so that implementation-agent confidence is not the only evidence.
8. As a reviewer, I want verification to cover committed, staged, unstaged and intended new files, so that unfinished commit bookkeeping cannot hide changes.
9. As a developer, I want `/review` to obtain missing or stale verification, so that I do not manually orchestrate the handoff.
10. As a developer, I want current evidence reused, so that later gates do not repeat completed work.
11. As a developer changing sessions, I want local evidence to survive, so that a fresh agent can continue the same change.
12. As an application maintainer, I want harness bookkeeping excluded from application commits, so that PRs contain relevant changes.
13. As a developer in another checkout, I want absent evidence regenerated, so that unavailable local state cannot masquerade as proof.
14. As a human reviewer, I want findings explained as what, why, how, recommendation and its rationale, so that I can decide what to do.
15. As a project owner, I want review to wait before editing code, so that I control which findings are fixed.
16. As a developer, I want ordinary review corrections handled without new specs or tickets, so that small fixes stay inexpensive.
17. As a reviewer, I want fixes independently reverified, so that acceptance covers the corrected result.
18. As a project owner, I want settled behavior and decisions preserved during fixes, so that reviewers do not repeatedly move the goalposts.
19. As a developer, I want preference-only findings distinguished from defects and concrete risks, so that stylistic alternatives do not become arbitrary blockers.
20. As a project owner, I want disputed or repeatedly unsuccessful fixes routed to focused `/grill-me`, so that a resolution is agreed before more editing.
21. As a developer, I want unrelated working files preserved and excluded from verification inputs, so that they cannot accidentally make the proposed PR pass.
22. As a reviewer, I want unavailable independent review reported explicitly, so that missing proof is never presented as PASS.
23. As a project owner, I want `/ship` after completed review to accept and publish the presented unchanged scope, so that I do not repeat authorization.
24. As a developer, I want `/ship` to commit accepted review fixes and create an actual PR/MR, so that publishing finishes the job.
25. As a developer, I want publishing to reuse verification when committing identical content, so that a new commit identifier alone does not trigger another review.
26. As a developer whose push fails, I want to restore connectivity and retry without duplicate commits or checks, so that transport failure does not restart development.
27. As a developer, I want partial publication reported and resumed without duplicate PRs, so that retries are predictable.
28. As a project owner, I want merge and force-push separately authorized, so that normal publication stays within its scope.
29. As a greenfield developer, I want migration code, skills and legacy baselines omitted automatically, so that a new project contains only relevant capabilities.
30. As an application developer, I want normal gates to work without `make manifest`, so that starter distribution maintenance is not my responsibility.
31. As a brownfield owner, I want migration available from a separate Engineering checkout, so that a clean consumer payload does not remove the migration path.
32. As a brownfield owner, I want accepted migration distinguished from closed migration, so that pending cleanup remains visible.
33. As a brownfield owner, I want explicit artifact retention respected and ordinary development independent of migration state, so that migration scaffolding is temporary by default.
34. As a starter maintainer, I want distribution integrity and existing migration protections preserved, so that simplifying the user journey does not weaken installation safety.

## Implementation Decisions

### Responsibilities and upstream integration

- Build implements the agreed scope. Verify produces independent engineering
  evidence. Accept is the human's judgment of that scope. Publish turns the
  accepted content into a PR/MR. These are responsibilities, not an application
  state machine or a rigid one-command/one-gate mapping.
- The unit is a shippable change: a bounded proposed PR scope that may span
  tickets and should ideally be demonstrable by running something. Upstream
  `/to-spec` and `/to-tickets` own specification, vertical slicing and dependencies.
- Preserve pinned upstream skills unchanged and preserve `/implement` behavior
  as much as possible. Invocation authorizes local commits within the requested
  scope, not push, PR creation or merge. A commit is neither proof nor acceptance.
- Use project-owned policy and thin runtime integration for the engineering
  handoff. The installed upstream implementation skill invokes review before
  committing, while its review examines committed changes. Consequently its
  invocation alone cannot certify uncommitted implementation. Obtain evidence
  covering the actual final content; reuse upstream evidence only when its scope
  and freshness satisfy the engineering contract.
- Prefer automatic independent verification after implementation. `/review`
  obtains missing or stale evidence before presenting acceptance information.
  Preserve fresh read-only maintainability and behavioral review, with security
  review when applicable. Reviewers reconstruct evidence from change and
  requirement pointers, without implementation-session reasoning or self-review.
- Formatting and applicable explicit Graft preparation precede verification.
  The behavioral verifier runs authoritative checks. If independent execution
  is unavailable, report incomplete proof and provide a concise fresh-session
  handoff. Publication cannot substitute implementer self-review.

### Evidence and freshness

- Pair readable evidence with minimal machine-checkable records in ignored local
  Engineering state, linked to the change. Record intended scope/content,
  comparison base, commands/results, independent findings and coverage gaps.
  Put useful summaries and test evidence in the PR. Missing local records in
  another checkout require regeneration rather than assumed success.
- Bind evidence and acceptance to proposed content, including intended uncommitted
  and new files. Track comparison base, check configuration and relevant
  dependency/tool versions. Changes invalidate affected evidence; time passing,
  failed network transport, or a content-preserving commit alone do not.
- Verify the exact proposed PR content. If unrelated edits could affect results,
  use an isolated temporary checkout containing only that content. Preserve the
  user's working files without requiring them to stash or commit unrelated work.
- Machine checks establish freshness and required results, not semantic truth.
  Do not fingerprint the entire machine or introduce a general workflow engine.

### Acceptance and bounded correction

- Review is read-only with respect to application content; verification may
  produce local evidence and test artifacts. Explain behavior, requirement
  coverage, consequences, risks and unverified areas. Use selective adversarial
  inspection where uncertainty warrants it rather than repeating full review.
- Each finding explains what is wrong, why it matters, how it could be addressed,
  the recommendation and why that option is preferred. Cite concrete evidence
  and distinguish blockers from nits. Wait for human instructions before fixes.
- Findings identify a violated requirement, demonstrated defect or concrete risk.
  Reviewers consult settled decisions; a different preference alone is
  non-blocking. Each correction preserves previously agreed behavior and decisions.
- Authorized bounded fixes may remain uncommitted. Rerun authoritative automated
  checks after code fixes and obtain independent inspection of the fix and its
  affected behavior. Retain valid review evidence for unchanged areas with an
  explicit scope justification. Scope or architecture changes require broader
  review. Present the updated acceptance summary; prior acceptance does not
  silently transfer to changed content.
- Pause editing after two unsuccessful attempts at the same finding, or before
  a fix would undo a settled decision. Explain the conflict and use focused
  `/grill-me` to examine evidence, alternatives and behavior to preserve. Record
  the human-agreed resolution before fixing and reverifying. This is not a cap
  on legitimate findings. Ordinary corrections need no new planning ceremony;
  materially expanded scope returns to `/to-spec` and `/to-tickets`.

### Publishing and recovery

- `/ship` following completed review expresses acceptance of the presented
  unchanged scope and authorization to commit remaining accepted fixes, push
  and create a PR/MR when blockers are resolved. It cannot supply a missing
  acceptance review. Honor narrower explicit requests and existing authorization.
- Publishing checks intended paths/content, current evidence, branch/base/remote,
  authorization and unresolved findings. Stage only accepted paths. Reuse existing
  implementation commits, commit remaining accepted changes when needed, push,
  create the actual PR/MR with the configured provider, and report its URL.
- Do not repeat semantic review or unchanged authoritative checks during shipping.
  Changed content or evidence inputs return to the responsible earlier gate.
  Hooks remain enforced; content mutations from hooks require reassessment before
  publishing. Never bypass a failed gate.
- Report partial progress accurately. The primary recovery case is a successful
  local commit followed by failed push: restore connectivity, then retry without
  recreating the commit or redoing unchanged review. Also recognize successful
  pushes and existing PRs after later failures. Avoid duplicate commits/PRs and
  retain scoped authorization. Merge and force-push require separate authorization.
- Preserve provider independence; publishing support must not require GitHub for
  every project. A drafted PR body is not successful PR creation.

### Greenfield payload, ownership and brownfield closure

- Build fresh templates without migration implementations, migration skills or
  legacy baselines. Brownfield migration runs from a separate Engineering checkout.
  This deliberately revises v3.1's self-contained consumer migration decision;
  integrate with its packaging work rather than silently editing its accepted
  tickets. Existing installations are not automatically stripped of code.
- Reuse the positive distribution inclusion mechanism and keep remaining consumer
  setup, doctor and ordinary gates functional without excluded components.
  Starter/template maintainers own fingerprints. Ordinary application changes
  require neither `make manifest` nor fingerprint repair; correct ownership
  boundaries rather than teaching consumers to regenerate distribution evidence.
- Reuse v3.1 migration inventory, reconciliation, finalization, rollback and
  validation. Add only missing completion/cleanup behavior. Migration accepted
  means validated and human-accepted; migration closed means temporary artifacts
  are removed or explicitly retained by the human.
- Keep pending cleanup visible in the migration handoff without blocking ordinary
  development. Show exact temporary removal scope and retention choices, preserve
  removal authorization and retry safety, and do not silently delete changed
  artifacts. Unresolved semantic decisions or failed validation cannot be labeled
  complete. No normal development gate depends on migration evidence or receipts.
- Lead user documentation with onboarding, the canonical loop, expected outputs,
  review corrections and publishing recovery. Place protocol and maintainer detail
  below or behind links. Coordinate shared policy, commands, reviewer guidance and
  evals so old final-check/commit rules do not contradict the new journey.

## Testing Decisions

The user approved three externally observable boundaries. Prefer existing
integration patterns and high-level command behavior over internal helper tests.

1. **User-facing commands in disposable Git repositories.** Reuse existing
   subprocess-based check fixtures, fake executable toolchains and committed
   migration fixture patterns. Exercise evidence reuse and invalidation, missing
   review or acceptance, intended new/uncommitted files, content-preserving commits,
   changed base/configuration/dependencies, and hook mutations. Prove isolated
   verification excludes unrelated local edits and preserves their bytes. Use
   fake hosting tools to demonstrate actual publication calls, failed-push retry,
   partial progress and duplicate avoidance without publishing real test PRs.
   Observe results and invocation counts to establish that current checks and
   reviews are reused rather than repeated.
2. **Generated template and external migration commands.** Extend v3.1's payload
   and migration test boundaries after integration. Generate a fresh project,
   verify migration components are absent, initialize it and run ordinary gates
   after an application change without manifest regeneration. Confirm external
   migration still works and cleanup distinguishes acceptance, pending cleanup,
   closure and requested retention. Extend existing preservation, stale-input and
   retry coverage only where behavior changes; do not rebuild the migration suite.
3. **Workflow evaluation and a disposable end-to-end journey.** Update existing
   verification and shipping policy evals for scoped local-commit authorization,
   evidence consumption, human-controlled fixes, findings explanation format,
   unavailable independent review and focused grilling escalation. Include a
   scenario where a proposed correction would undo an agreed decision. Static
   checks establish instruction consistency, not model judgment or independence.
   Exercise implementation, independent review, a human-directed fix, reverification
   and publishing handoff on a disposable project; record real observations and
   limits. Keep authenticated model evals explicit and optional under repo policy.

For implementation, run repository-required formatting, checks, starter tests and
static evals, followed by the required fresh independent reviews. Preserve
conditional security review for sensitive operations. Tests should establish user
behavior and failure recovery, not mirror implementation structure or Matt's
internal workflow.

## Out of Scope

Another framework rewrite; a new tracker or application lifecycle database;
forking upstream skills; replacing upstream ticket planning; restoring retired
factory commands; reimplementing v3.1 migration or packaging; automatic deletion
from existing installations; automatic expiry of migration artifacts; compulsory
grilling for routine fixes; treating a commit or generated report as acceptance;
bypassing hooks or failed checks; automatic merge or force-push; real remote
publication during this specification task.

## Further Notes

Shared understanding was confirmed after grilling; the testing boundaries were
subsequently approved. The intent document remains the discussion record; this
specification synthesizes the final decisions and supersedes earlier conflicting
proposals, including exclusive commit ownership by ship and one command per gate.

This work complements v3.1 but is not conflict-free. Integrate shared template,
migration and onboarding surfaces after the corresponding v3.1 work. Preserve its
approved safeguards and audit delivered behavior before extending cleanup.

Next, `/to-tickets` proposes independently demoable vertical slices and blocking
edges for human approval. No ticket breakdown or runtime implementation is created
by this specification, and its future authorization rules do not themselves change
the current repository policy.
