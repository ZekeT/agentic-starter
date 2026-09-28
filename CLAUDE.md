<!-- engineering:integration:begin -->
# Project agent instructions

## Read first

[ENGINEERING.md](ENGINEERING.md) explains setup, upstream skills, verification,
updates and migration. `.claude/` is a runtime adapter; core policy is portable.
Read relevant feature instructions and ADRs as needed, not entire doc trees.

## Implementation defaults

- Understand the existing code before editing: search and read the relevant
  source directly, following any navigation section below.
- Surface material assumptions. Stop for contradictory requirements,
  unresolved architecture, security tradeoffs, or two unsuccessful bug fixes.
  Explain what, why, how, and your recommendation with its reason.
- Prefer the minimum sufficient design, surgical changes, coherent modules,
  and verifiable results. Avoid unrelated refactors and speculative abstractions.
- Matt's upstream skills own discussion, planning, TDD, implementation and review.
  For large coding work: `/wayfinder` → `/to-spec` → `/to-tickets` → `/implement`.
  Inspect Wayfinder through the configured tracker. Use a fresh implementation
  session per ticket. Create/switch to the intended branch before `/implement`.
- Follow [.engineering/docs/maintainability.md](.engineering/docs/maintainability.md).
- Never read `.env` or secret variants. Read `.env.template` for names only;
  use environment/settings objects. Never bypass protection hooks or failed gates.

## Verification and human control

Use targeted tests while building. Run `make fmt` before fresh independent
maintainability review and behavioral verification. The verifier runs `make check`;
it is non-mutating and authoritative. Required checks follow the installation
role and path ownership in the verification guide.

Reviewers are read-only and receive only a branch/ticket/spec/request pointer.
Do not pass implementation-session reasoning or a self-review narrative to them.
Plans declare a review tier at or above the computed floor; the tier sets the
required reviewer roles. One fresh session may file both ordinary reports;
sensitive changes need a separate fresh session per role, including security.
Human review follows [REVIEW.md](REVIEW.md). Wait for human fix instructions;
preserve settled decisions. Pause after two unsuccessful attempts at one finding
or before undoing a settled decision; use focused `/grill-me` and record the
agreed resolution. Independently reverify authorized corrections.
Invocation of `/implement` authorizes local commits within the requested scope;
a commit is neither verification nor human acceptance. Never infer push, PR/MR
or merge authorization from implementation. Other commits require human request.
`/ship` after completed review accepts the unchanged presented scope and authorizes
remaining scoped commits, push and PR/MR creation. Honor narrower requests and
existing authorization; reuse current proof without duplicate checks. See
[publication](.engineering/docs/publication.md). Merge/force-push remain separate.

After implementation, automatically hand off to fresh independent reviewers when
the runtime supports them. Keep pinned upstream skills unchanged. Their committed
diff review alone cannot certify uncommitted work. Follow
[verification evidence](.engineering/docs/verification.md): prepare exact scope,
have the verifier run recorded checks, and record independent reports. `/review`
obtains missing/stale proof and reuses current evidence. If fresh reviewers are
unavailable, report INCOMPLETE and give a fresh-session handoff; never self-certify.

## Agent skills

### Issue tracker

Local Markdown is the default, independent of Git hosting provider.
See [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md). During ticket-based
implementation, update task checkboxes as acceptance criteria are satisfied and
keep ticket status and the existing breakdown in sync before each handoff. Record
evidence and remaining work; distinguish implementation, verification, human
acceptance, publication and merge. Update delivery links after authorized shipping
and observed merges. This is agent bookkeeping, not an automatic tracker service;
keep pinned upstream skills unchanged.

### Domain docs

Durable context lives in `docs/context/`; architectural reasons in `docs/adr/`.
See [docs/agents/domain.md](docs/agents/domain.md). Tests and code establish
current executable behavior. Keep feature-local instructions small and stable.
<!-- engineering:integration:end -->
<!-- engineering:navigation:begin -->
## Navigation

Graft navigation is enabled. For non-trivial application navigation, use
`.engineering/bin/graft` (map, skeleton, callers, grep, ask, blast) before broad
source reads; inspect tooling source directly. Graft build/check are explicit
preparation steps, outside `make check`.
<!-- engineering:navigation:end -->
