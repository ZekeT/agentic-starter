# Engineering v3.1b intent — Greenfield development friction

Status: synthesized — shared understanding and testing boundaries approved

The completed grilling discussion is synthesized in [spec.md](spec.md). This
document preserves the intent and discussion history; the specification carries
the final decisions where earlier proposals below differ.

## Implementation feedback — checkout preference

After ticket 01, the user found reviewing a separate worktree inconvenient and
stated a preference to work in the current Git checkout, seldom in parallel.
Default subsequent implementation to the current checkout. Separate worktrees
are not the normal user journey; use them only when requested or when concrete
isolation requirements make them necessary, explaining that need. Temporary
verification isolation from ticket 02 remains distinct from relocating the
developer's implementation workspace. No automatic branch switch, merge or
worktree removal is implied by this feedback.

## Workflow and scope correction

This document was prematurely named spec.md. The current activity is
`/grill-with-docs`; `/to-spec` will synthesize the settled discussion into a new
spec.md, followed by `/to-tickets` for approved, verifiable vertical slices.
The proposed implementation details below remain discussion input unless
explicitly settled here. No implementation or ticket breakdown is approved.

The primary problem is friction experienced in a GREENFIELD starter project.
Fresh projects should automatically receive a payload without unnecessary
migration code, not merely an empty migration workspace. Brownfield completion
and cleanup remain relevant to projects actually undergoing migration.

This deliberately revises a v3.1 distribution decision: its approved
open-decisions.md includes migration tooling in the consumer runtime. For v3.1b,
fresh templates will exclude migration implementations, migration skills and
legacy baselines; brownfield migration runs from a separate Engineering checkout.
Integrate this packaging change after v3.1 rather than silently altering its
approved work. Do not delete code from existing installations during grilling.

## Settled in grilling — round 1

- The unit is a shippable change: a bounded proposed PR scope, ideally verifiable
  by a human running something and observing behavior/output. `/to-spec` captures
  the requirement; upstream `/to-tickets` owns decomposition into demoable slices
  and their dependencies. The harness must not become another ticket planner.
- Use human-readable evidence plus minimal machine-checkable records to detect
  stale content and missing results; do not build a general workflow engine.
- `/ship` after completed review expresses acceptance of the presented unchanged
  scope and authorization to commit, push and create a PR, provided blockers are
  resolved. It cannot substitute for a missing acceptance review. Merge remains
  separately authorized. This is intended future behavior, not current policy.
- Distinguish migration accepted from migration closed. Closed means temporary
  scaffolding has been removed or explicitly retained. Cleanup pending remains
  visible in the migration handoff without blocking ordinary development.

## Grilling — round 2

- Q5 accepted: migration-free greenfield distribution with externally available
  brownfield tooling, as described above.
- Q6 correction: preserve upstream `/implement` behavior as much as possible,
  including its implementation commit. A commit is neither verification nor
  acceptance. Independent review remains necessary. Review findings may be fixed
  in place without a commit; `/ship` can commit those fixes before publishing.
- The earlier suggestion that `/ship` must exclusively own all commits was not
  accepted. Future repository authorization policy must accommodate implementation
  commits without treating them as authorization to publish. Current policy has
  not changed during this interview.
- Verify the intended final content, whether committed or
  uncommitted; independently reverify fixes before acceptance/publication. A
  commit that preserves that content should not itself invalidate evidence.

## Settled in grilling — round 3

- Q7 accepted: prefer automatic independent verification after implementation.
  `/review` obtains missing or stale verification before presenting acceptance
  information, and consumes valid evidence without repeating its work. Four gates
  express distinct responsibilities, not an inflexible command-to-gate mapping.
- Q8 accepted: future policy treats invocation of `/implement` as authorization
  for local commits within the requested scope, preserving upstream behavior.
  This does not authorize push or PR creation. Review fixes may stay uncommitted
  until `/ship`, but must be independently verified before it commits them.

## Settled in grilling — round 4

- Q9 accepted: reusable verification records live in ignored local Engineering
  state, linked to the change. Human summaries and test evidence belong in the
  PR. A checkout without those records regenerates verification. Do not require
  application commits to carry harness bookkeeping.
- Q10 clarified and accepted: review is read-only. Explain findings as WHAT the
  issue is, WHY it matters, HOW it could be addressed, and a RECOMMENDATION with
  WHY that option is preferred. Include concrete evidence and distinguish
  blockers from nits. Wait for the human to instruct which findings to fix.
  Authorized bounded fixes trigger fresh verification and an updated acceptance
  summary; ordinary corrections need no new spec, tickets or fix command.
- Q11 accepted: if independent execution is unavailable, verification remains
  explicitly incomplete. Provide a concise handoff to a fresh reviewer session;
  never substitute implementer self-review. Publication waits for required proof.

## Settled in grilling — round 5

- Q12 accepted: after code fixes, rerun authoritative automated checks and obtain
  independent inspection of the fix and affected behavior. Retain valid review
  findings for unchanged areas. Scope/architecture changes require broader review.
  Shipping does not repeat current verification.
- User experience: review/fix cycles have sometimes reached roughly ten rounds;
  fixes can undo previously implemented behavior or reopen prior decisions. The
  correction loop needs explicit protection against this churn, not merely fewer
  checks. The proposed boundary below still needs agreement.
- Q13 accepted: verification covers exactly the proposed PR content. When unrelated
  local edits could affect results, use an isolated temporary checkout containing
  the proposed change. Preserve working files without demanding a stash/commit.
- Q14 accepted: report completed publishing steps and resume safely with existing
  authorization and current evidence; avoid duplicate commits/PRs and force-push.
  Primary real-world case: local commit succeeds, network/push fails, human
  resolves connectivity, then retries push or `/ship`. Do not recreate the commit
  or repeat review solely because transport failed. Push-success/PR-failure is
  another recovery case, not the motivating user experience.

## Settled in grilling — round 6

- Q15 accepted: findings identify a violated requirement, demonstrated defect or
  concrete risk. Reviewers consult settled decisions; preference alone is
  non-blocking. Fixes preserve existing agreed behavior and decisions. Evidence
  challenging a settled decision is explained to the human before redesign.
- Q16 accepted: two unsuccessful attempts at the same finding, or a proposed fix
  undoing a settled decision, pauses editing for a human decision. This is not a
  blanket limit on the number of legitimate findings.
- User proposes `/grill-me` for these conflicts so the selected fix is thought
  through. The installed skill delegates to the same grilling discipline used
  here. Proposed handoff: explain the conflict and evidence, then focus grilling
  on the disputed decision, preserved behavior and alternatives. Record the
  agreed resolution against the existing change before implementing it and
  independently reverifying. Routine corrections do not need grilling. If scope
  grows materially, return to `/to-spec` and `/to-tickets` instead of disguising
  new work as a fix. Confirm this handoff in the closing discussion.
- Q17 accepted: evidence freshness includes proposed content, comparison base,
  check configuration and relevant dependency/tool versions. Changed inputs
  invalidate affected evidence; elapsed time and network failures alone do not.
  Do not attempt to fingerprint the whole machine.

## Remaining handoff before /to-spec

- Project-owned integration of immutable upstream skills: preserve implementation
  commits while ensuring independent review covers the actual changed content.
  Upstream implement invokes code-review BEFORE committing, but that review uses
  a committed-only diff. It already spawns independent Standards/Spec agents;
  independence alone does not establish coverage of uncommitted work.
- Confirm shared understanding, including focused `/grill-me` for conflicted or
  repeatedly unsuccessful fixes. `/to-spec` will synthesize the settled intent
  and check the proposed testing seams; it has not been invoked yet.

## Problem

Day-to-day use of the starter exposes duplicated review/check work, unclear
handoffs, maintainer-only chores, and an ambiguous end to brownfield migration.
Simplify the user journey without another framework rewrite or an application
workflow state machine. Later gates consume evidence from earlier gates instead
of routinely repeating them.

The canonical greenfield loop is `/implement → /review → /ship`, with automatic
independent verification between implementation and acceptance. Planning remains
compositional: use upstream discussion, spec and ticket skills when needed.

## Four gate responsibilities

| Gate | Question | Owner | Result |
| --- | --- | --- | --- |
| Build | Did we implement what was specified? | `/implement` | Bounded implementation and targeted tests |
| Verify | Does independent evidence say it works? | Automatic post-implementation engineering gate | Independent review and behavioral evidence |
| Accept | Am I comfortable shipping this change? | `/review` + human | Acceptance of a specific scope, with risks and gaps understood |
| Publish | Can the accepted tree be safely turned into a PR? | `/ship` | Commit, push, and actual PR/MR creation within authorization |

Gates have distinct responsibilities. Build hands off to Verify; it does not
certify itself. `/review` ensures current verification exists before presenting
acceptance information, obtaining missing/stale evidence when necessary.
Acceptance is a human decision; a generated summary cannot grant it. Publishing
checks evidence and repository mechanics without conducting semantic review.

## Intended behavior

1. **Automatic engineering verification.** After targeted tests, formatting and
   applicable explicit Graft preparation, use fresh read-only maintainability
   review and behavioral verification, plus security review when applicable.
   Preserve the existing independent-context boundary. The verifier runs the
   authoritative checks; implementation reasoning is not reviewer evidence.
   If independent execution is unavailable, report missing proof rather than PASS.

2. **Reusable evidence.** Keep reusable records in ignored local Engineering
   state, linked to the request/spec/ticket, with scope, reviewed content identity, comparison
   base, check commands/results, independent findings, coverage gaps and unresolved
   concerns. Put human summaries and test evidence in the PR. A checkout without
   local records regenerates verification. Define a minimal format during design; do not create a new
   tracker or workflow engine. Evidence must cover intended uncommitted and new
   files, not just HEAD. Bind human acceptance to the same content and scope.
   Missing or stale evidence routes back to Verify; it cannot be silently reused.

3. **Human-facing `/review`.** Explain changed behavior, requirements coverage,
   design consequences, material risks and known gaps using existing evidence.
   Explain findings as what, why, how, recommendation and its rationale. Review
   is read-only and waits for human direction before fixes. Selective adversarial inspection focuses on uncertainty, sensitive boundaries
   and suspicious omissions. Do not routinely repeat full independent review or
   checks. Findings are actionable and distinguish blockers from nits. Acceptance
   must not be inferred from silence or a successful automated gate.

4. **Cheap findings loop.** Record a finding, make a bounded fix, rerun affected
   checks and obtain independent reinspection where the fix invalidates evidence,
   then return for acceptance. Preserve unaffected evidence only with an explicit
   scope justification. Changes invalidating an authoritative whole-tree check
   require that check again. A broad change falls back to full verification.
   Fixes invalidate acceptance of the changed content; no stale PASS shortcut.
   Use existing upstream implementation/bug-fixing capabilities rather than
   copying their methodology or requiring a new planning cycle for every finding.

5. **Deterministic `/ship`.** Consume current verification and human acceptance.
   Check intended paths, tree identity, branch/base/remote, authorization, and
   unresolved findings. Stage only accepted paths, commit, push, and create an
   actual PR/MR through the configured provider; report its URL. Do not stop at
   drafting a PR body when publication is authorized. Do not repeat semantic
   review or an unchanged authoritative gate solely because shipping started.
   Changed content or invalidated evidence returns to the responsible earlier
   gate. Hooks remain enforced; hook mutations require freshness reassessment.
   Retries recognize completed commits/pushes/PRs and avoid duplicates, reporting
   partial progress and a concrete recovery step on failure. Preserve provider
   independence, explicit narrower shipping requests, and separate merge/force
   push authorization. Define invocation/authorization wording before changing
   the command; existing explicit authorization must not be requested again.

6. **Manifest ownership.** Ordinary application development never needs
   `make manifest` or fingerprint repair. Starter/template maintainers own
   distribution fingerprints. If application edits currently invalidate a
   consumer gate, fix that ownership boundary rather than teaching users to
   regenerate evidence. Reuse v3.1's source/template split and safeguards.

7. **Migration completion and cleanup.** Extend v3.1's finalization contract only
   where a gap remains. Distinguish preparation, validated finalization pending
   human acceptance, accepted migration with cleanup pending, and cleanup
   completed (or explicitly retained artifacts). These are migration lifecycle
   descriptions, not application workflow states. Never claim completion while
   semantic decisions or validation failures remain. Make cleanup an explicit
   final handoff with exact temporary paths and retained-snapshot choices;
   preserve v3.1's human authorization for removal. Retries are safe and changed
   artifacts are not silently deleted. Normal development never depends on the
   workspace, inventory, parser or receipt after migration. Do not add automatic
   expiry/deletion or a permanent migration service merely to enforce tidiness.

8. **Journey-first documentation.** Lead `ENGINEERING.md` with onboarding and the
   canonical loop, expected outputs, findings fixes and publication. Move detailed
   verification/protocol/maintainer material below or into linked documentation.
   Keep brownfield entry paths prominent and maintain one policy source of truth.

## Current repository observations

- `CLAUDE.md` and `ENGINEERING.md` already require independent verification and
  human shipping control; keep those invariants while simplifying handoffs.
- `.claude/commands/review.md` is already a thin evidence summary. Extend its
  acceptance/finding behavior rather than replace it with another full review.
- `.claude/commands/ship.md` and `REVIEW.md` explicitly require a final
  `make check`; replacing that repetition needs coordinated policy and eval edits.
- `.engineering/docs/commits-and-prs.md` still references `/commit-push-pr` and
  `/dev-change`; reconcile those references with the canonical commands.
- There is no current root `FACTORY.md`. The user's factory concepts are intent
  context, not an instruction to restore retired factory orchestration.
- Managed upstream skills remain pinned and unchanged. Put portable handoff
  policy and thin runtime integration in project-owned surfaces.

## Boundary with v3.1

Related change: [brownfield migration and template hygiene](../engineering-v3-1/spec.md).

This draft is isolated in a new scratch directory. Implementation is conceptually
complementary, but shared files are not guaranteed to merge without conflicts.

| Area | v3.1 owns | v3.1b owns / sequencing |
| --- | --- | --- |
| Migration | Inventory, reconciliation, approved finalization, rollback and validation | Audit the delivered finalizer first; add only missing completion/cleanup UX |
| Distribution | Positive payload selection, clean template, initialization | Consume that split to remove manifest chores from everyday development |
| Onboarding docs | Four entry paths and source/consumer documentation | Reorganize the resulting docs around the daily journey after v3.1 issue 05 |
| Daily gates | Existing policy remains in force | Evidence handoff, acceptance/fix loop, deterministic publishing |

Do not alter v3.1 tickets or expand their acceptance criteria. Design of the daily
gates can proceed independently. Rebase/integrate before changing shared policy,
template inputs, migration runtime or final onboarding documentation. v3.1 issues
04 and 05 are still marked ready-for-agent; migration issues 01–03 are marked
implemented and verified, awaiting human review. Status labels are planning
context, not proof that the whole release is accepted.

## Acceptance scenarios

- A normal verified change moves through `/review` and authorized `/ship` without
  duplicate semantic review or redundant checks of unchanged inputs.
- Missing evidence, changed intended files, changed comparison base, unresolved
  blockers, or content-mutating hooks prevent stale evidence from authorizing PR
  creation and name the necessary return gate.
- A review finding is fixed and independently reverified at the affected scope;
  the user sees the delta and grants fresh acceptance without redoing planning.
- Shipping creates a real PR/MR when authorized, reports its URL, preserves
  unrelated work, and resumes safely after partial publish failures.
- A consumer application change passes its normal gates without running
  `make manifest`; maintainer distribution integrity remains enforced.
- A migrated project reaches an explicit accepted/cleanup outcome, preserves
  requested snapshots, and develops normally without migration scaffolding.
- A new user can find setup, implement, review, fix findings and ship at the top
  of the guide without learning the internal protocol first.

## Proposed implementation order

1. Settle the minimal evidence/freshness contract and shipping authorization
   wording; map every existing gate/check to its single owner.
2. Implement post-build evidence handoff and acceptance/findings UX together.
3. Implement publishing preflight, actual PR creation and resumable failures.
4. Integrate v3.1 template ownership and audit remaining migration cleanup gaps.
5. Rewrite journey documentation and reconcile policy, adapters and evals.

Create execution-sized tickets after the design is settled. This list is a
proposed sequence, not approved implementation tickets.

## Verification plan for implementation

Use behavioral tests at evidence invalidation and publishing boundaries, with
temporary repositories and fake hosting tools for failures/retries. Cover changed
content, unrelated files, missing acceptance, hook mutations and duplicate PR
avoidance. Extend migration tests only for newly introduced cleanup behavior.
Use static evals for command responsibility and policy consistency; they do not
prove real model independence. Run repository-required formatting, independent
review, checks, starter tests and evals for the eventual tooling changes. Exercise
the complete user journey on a disposable project and record actual outcomes.

## Non-goals

Another framework rewrite; restoring FACTORY.md or legacy commands; new tracker,
branch naming protocol or application lifecycle database; forking Matt skills;
reimplementing v3.1 migration or packaging; bypassing hooks/checks; automatic human
acceptance; unauthorized publication or merge. This draft does not modify current
runtime policy or authorize implementation, commits, pushes or PR creation.
