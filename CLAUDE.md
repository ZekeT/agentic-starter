# CLAUDE.md

## Commands

```bash
make fmt        # automatic formatting/import fixes; run before verification
make check      # non-mutating source gate: format, lint, types, tests, feature docs
make evals      # static factory evals (starter configuration changes)
make harness-test  # maintainer script tests (starter tooling changes)
make manifest   # after editing template-owned files
```

A non-zero gate is a failure to fix, never to bypass. Use targeted tests while
coding; the fresh verifier owns the full gate, and `/commit-push-pr` repeats it
before committing. Run `make fmt` again if later edits need formatting.

## Rules

- `openspec/specs/` is **canonical** current-state product/system truth.
  **Never edit `openspec/specs/` directly.** Changes live in
  `openspec/changes/` and reach canonical specs only via `/archive-change`.
- Choose FAST for behavior-neutral maintenance, STANDARD for normal behavior
  changes, DEEP for architecture/risk/important unknowns. Cosmetic wording with
  unchanged meaning can be FAST; contractual output changes cannot. Routing,
  lifecycle and human gates: [FACTORY.md](FACTORY.md), loaded when needed.
- One independently shippable task group = one branch = one PR.
  **Branch existence is the mutex**: claim `feat/<slug>-g<N>` by creating it.
  FAST uses `fix/<slug>`, `chore/<slug>`, or `docs/<slug>` without OpenSpec.
  Worktrees are opt-in. Never take over an existing claim silently.
- The task group is the plan. Implement it directly, update its checkboxes and
  any changed task text with the implementation. Stop before commit/PR for
  human review; archive also requires human confirmation.
- If a spec assumption proves wrong, amend the active delta for a small
  correction or propose a new change for a large one. If unclear, stop and ask.
  Stop for unresolved architecture, contradictory requirements, security
  tradeoffs, or a bug attempted twice unsuccessfully. Explain what, why and a
  suggested next step. Never silently demote a DEEP change.
- **Never read `.env`.** Read `.env.template` for variable names; use
  `os.environ` or settings objects. Never bypass security/env/git hooks.

## Simplicity and retrieval

Build the minimum solution. No speculative features, single-use abstractions,
extra configuration, or error handling for impossible cases.

For current behavior, start with `openspec list --specs`, then read only named
relevant capabilities. Never bulk-read `openspec/` or `docs/`. Implementation
loads only the claimed group, relevant spec/design/program-design sections,
local feature instructions, and needed code. Each feature under `src/` has a
small `CLAUDE.md`: purpose, entry points, invariants, gotchas, never task status.
Do not import feature instructions into this file.

Skills are progressive disclosure. Load specialized skills only when their
trigger applies. The factory workflow owns planning, implementation stages,
verification, and shipping. Runtime mechanics: [HARNESS.md](HARNESS.md).

Python tooling uses `uv` and `pyproject.toml`. Commit/PR conventions are in
`.harness/docs/commits-and-prs.md`; review policy is `REVIEW.md`. Resolve the
base from `--base`, `git config harness.baseBranch`, or the remote default
(`main` fallback), and diff against its merge base, never its moving tip.
