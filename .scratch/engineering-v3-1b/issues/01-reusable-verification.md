# 01: Verify a shippable change once and reuse its evidence

**Spec:** [Greenfield development without repeated gates](../spec.md)

**What to build:** Preserve upstream implementation and scoped local commits,
then obtain independent engineering verification of the complete intended
change. Review obtains missing or stale evidence and reuses current results
across sessions instead of repeating them.

**Blocked by:** None (can start immediately).

**Status:** completed — merged in [PR #22](https://github.com/ZekeT/agentic-starter/pull/22)

- [x] Keep pinned upstream skills unchanged. Project-owned policy authorizes
  scoped local commits from `/implement`, without authorizing publication or
  treating commits as verification or acceptance.
- [x] Prefer automatic independent verification after implementation; `/review`
  obtains missing/stale evidence before presenting acceptance information. Do not
  mistake upstream committed-only review for coverage of uncommitted work.
- [x] After formatting and applicable explicit Graft preparation, obtain fresh
  read-only maintainability and behavioral review, plus security review when
  applicable. Reviewers receive change/requirement pointers, not implementer
  reasoning; the verifier runs authoritative checks.
- [x] Store readable evidence and minimal machine-checkable records in ignored
  local Engineering state, linked to the change. Include intended scope/content,
  comparison base, check commands/results/configuration, relevant dependency/tool
  versions, independent findings and coverage gaps.
- [x] Cover intended committed, staged, unstaged and new files. Changed inputs
  invalidate affected evidence; content-preserving commits, elapsed time and
  network failures alone do not. A checkout without records regenerates evidence.
- [x] Missing independent execution produces incomplete proof and a fresh-session
  handoff, never self-review as PASS. Refuse proof when unrelated edits could
  contaminate verification until ticket 02 supplies isolation.
- [x] Demonstrate a small change reviewed from a fresh session with no repeated
  verification, then demonstrate stale-content/input detection and revalidation.
  Cover externally observable behavior using disposable Git repositories.
- [x] Update affected guidance and evals coherently and pass required checks and
  independent reviews. Existing shipping remains conservative until ticket 04.

## Comments

Published following human approval of the eight-ticket breakdown. No implementation
or publication is performed by creating this ticket.

## Implementation evidence — 2026-09-21

- Implemented on `feat/engineering-v3-1b-01` in the isolated worktree
  `/tmp/agentic-starter-v3-1b-01`, preserving the ongoing v3.1 checkout and its
  uncommitted planning work. Local implementation commit: `bbb4c66`.
- Added public `engineering verify prepare/check/record/status` commands and
  ignored local evidence. Scope includes intended committed/staged/unstaged/new
  files; freshness covers working content, base/tip, check inputs and tool versions.
- Added project-owned automatic handoff/review instructions and scoped local
  commit authorization without modifying pinned upstream skills. Missing or stale
  evidence cannot pass; unrelated work is refused pending ticket 02 isolation.
  Shipping retains its existing final gate pending ticket 04.
- `make fmt` and starter-maintainer `make manifest` completed. Independent
  behavioral verifier ran and recorded `make check`, `make engineering-test`
  (234 passed), and `make engineering-evals` (7/7 static cases passed).
- Fresh independent maintainability, behavioral and security reports all PASS.
  Graft is not applicable because application roots are empty. Three authenticated
  prompt evals were not run; no live dependency advisory audit was performed.
- Reviewer execution was interrupted by a usage limit; resumed reviewers consumed
  the saved successful checks and completed their reports without rerunning them.
- All reports were imported and current evidence was PASS for snapshot
  `5511905725605fc7e84656dc7832df34a5b5a5f3fa756b7ee8e82cdc6a3bef11`.
  The post-commit freshness check retained the same PASS and snapshot.
  Evidence lives in the worktree's ignored local verification state. The tool
  validates freshness/attestation structure; it does not authenticate reviewer
  identity or prove hermetic external/environment inputs.
- Subsequently pushed `feat/engineering-v3-1b-01` to origin at the user's request
  for remote review. At that point no PR had been created and human acceptance remained outstanding;
  the subsequent merge is recorded below.

## Delivery reconciliation — 2026-09-22

- Merged in [PR #22](https://github.com/ZekeT/agentic-starter/pull/22)
  on 2026-09-21; local merge commit `3b39cac` is in the current checkout history.
- GitHub API access was unavailable during reconciliation; the merge record
  and landed repository content establish delivery.
