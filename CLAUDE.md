<!-- engineering:integration:begin -->
# Project agent instructions

## Read first

[ENGINEERING.md](ENGINEERING.md) explains setup, upstream skills, verification,
updates and migration. `.claude/` is a runtime adapter; core policy is portable.
Read relevant feature instructions and ADRs as needed, not entire doc trees.

## Implementation defaults

- Understand the existing code before editing. Use `.engineering/bin/graft`
  for non-trivial application navigation; inspect tooling source directly.
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
it is non-mutating and authoritative. Starter tooling changes also require
`make engineering-test` and `make engineering-evals`. Graft build/check are
explicit preparation steps, outside `make check`.

Reviewers are read-only and receive only a branch/ticket/spec/request pointer.
Do not pass implementation-session reasoning or a self-review narrative to them.
Security review applies to security-sensitive changes, including dependency
execution and destructive operations. Human review follows [REVIEW.md](REVIEW.md). Wait for human fix instructions;
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
See [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md).

### Domain docs

Durable context lives in `docs/context/`; architectural reasons in `docs/adr/`.
See [docs/agents/domain.md](docs/agents/domain.md). Tests and code establish
current executable behavior. Keep feature-local instructions small and stable.
<!-- engineering:integration:end -->
