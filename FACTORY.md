# Software factory workflow

The factory owns routing, planning, human gates, implementation, verification,
and shipping. OpenSpec owns behavioral truth and its change artifacts. Scripts
and hooks enforce deterministic checks. Skills supply techniques when useful.
The agent runtime executes these responsibilities; it does not need a particular
product's context-forking feature. See [HARNESS.md](HARNESS.md) for the shipped
Claude Code implementation.

## Choose the size of the work

| Workflow | Use for | Path |
|---|---|---|
| FAST | Obvious fixes, tiny refactors, naming, localized maintenance with no product/spec impact | implement → verify → human review → commit/PR |
| STANDARD | Normal product or observable behavior changes | explore → intent gate → crystallize → spec/design/tasks gate → implement per group → verify → human review → commit/PR → archive |
| DEEP | Major architecture, substantial cross-module work, important unknowns, risky migration, new subsystem, hard-to-reverse decisions, multiple viable architectures, or many shippable slices | explore → intent gate → optional spike → crystallize → architecture/spec gate → shape-change → program-design/tasks gate → implement per group → verify → human review → commit/PR → archive |

`/explore` reports `Workflow: FAST | STANDARD | DEEP` and a one-sentence
`Reason:`. STANDARD and DEEP record these in `intent.md`; DEEP names the
uncertainties or design issues that justify it. Classification is advisory:
promote when new complexity appears. Never silently demote DEEP after major
architectural uncertainty has been identified; ask the human first.

FAST does not require an OpenSpec change for behavior-neutral work. Cosmetic
wording corrections qualify when meaning and behavior stay unchanged. Changes
to contractual output or observable behavior require STANDARD; unresolved
ambiguity also promotes FAST to STANDARD, or DEEP if the risk warrants it.

For FAST, create a `fix/<slug>`, `chore/<slug>`, or `docs/<slug>` branch with
`git switch -c`; branch existence remains the claim mutex. One independently
shippable change = one branch = one PR. Implement with targeted tests, format,
then dispatch a fresh verifier with **only the branch name**. It discovers the
diff against the configured base, including uncommitted and untracked work.
Stop before committing. The human runs `/review`, then `/commit-push-pr`.
There is no OpenSpec archive step for FAST.

## Artifacts and gates

| Stage | Durable output | Human decision / next stage |
|---|---|---|
| `/explore` (STANDARD/DEEP) | `openspec/changes/<slug>/intent.md` | Accept intent before `/crystallize` or an optional `/spike` |
| Optional `/spike` | Evidence and ADR, with architectural findings in `design.md` | Accept findings; unresolved decisions remain explicit |
| `/crystallize` STANDARD | `proposal.md`, delta `specs/`, `design.md`, `tasks.md` | Accept before `/dev-change <slug> <group>` |
| `/crystallize` DEEP | `proposal.md`, delta `specs/`, architectural `design.md`; no final tasks | Accept architecture/spec before `/shape-change <slug>` |
| `/shape-change` DEEP | `program-design.md`, `tasks.md` | Accept program design and vertical slices before implementation |
| `/dev-change` | Code, tests, completed claims in the selected task group | Graft preparation, fresh maintainability reviewer and verifier, then human `/review`; stop uncommitted |
| `/commit-push-pr` | Commit and PR after the final full gate | Human authorizes shipping and merges the PR |
| `/archive-change` | Delta specs merged into canonical specs; change folder archived | All groups merged, then human confirms the proposed spec diff |

Do not start the next phase until its artifacts are accepted. Artifact-writing
stages present their output for review; commits and PRs require human approval.
An explicit instruction to implement an already accepted design authorizes that
implementation, without repeating the same permission question.

`openspec/specs/` is canonical current-state truth. Never edit it directly;
only `/archive-change` applies accepted deltas through OpenSpec. Work in flight
lives in `openspec/changes/`. Archive semantics and its confirmation gate do not
change with workflow tier.

## Implementation slices

One `## N.` task group in `tasks.md` = one branch = one PR. Branch existence is
the mutex: `/dev-change` claims `feat/<slug>-g<N>` by creating it, and an
existing branch blocks another claim. Worktrees are optional (`--worktree`).

Every group must be independently shippable: include its behavior, integration,
and tests. A read-only user flow, a validated mutation, and migration/backfill
support may be separate groups when each can safely ship. Database/backend/
frontend/tests groups that cannot ship alone are not acceptable. Record any
prerequisite groups and merge them before claiming dependent work.

The task group is the implementation plan. Each new group includes a short
`Context:` list pointing to relevant delta-spec scenarios, design sections,
and (for DEEP) program-design sections. Load those sections, relevant feature
instructions, and needed source files; do not bulk-load the change or docs tree.
Existing STANDARD changes with populated `tasks.md` remain implementable without
a tier marker, Context list, or `program-design.md`. Discover their relevant
sections by headings/search; do not send them through `/shape-change`.

## Fresh sessions

Accepted artifact + repository state must be sufficient for the next phase.
Recommended fresh-session boundaries: after intent, after design/spec, after
program design, per implementation task group, verification/review, and archive.
No stage requires the exploration transcript or an earlier agent's reasoning.

The verifier receives only slug + group for STANDARD/DEEP, or branch name for
FAST. It discovers evidence independently, runs the full deterministic gate,
checks every relevant scenario and completed task claim, exercises changed
behavior and the nearest regression paths, and reports PASS/FAIL without edits.
If something cannot be exercised, report the gap rather than claim success.

STANDARD/DEEP completion follows targeted tests → Graft structural build → fresh
maintainability review → fresh verifier → human review. The maintainability
reviewer receives only slug + group, returns PASS/CONCERNS, and never fixes code.
Resolve concerns or obtain explicit human disposition before proceeding. FAST may
skip semantic maintainability review; deterministic growth checks remain required.
Application-only navigation and its no-application disposition are documented in
[HARNESS.md](HARNESS.md#application-navigation-with-graft). Tooling changes still
receive source review.

Use targeted tests during implementation. Run `make fmt` before verification
(and again if subsequent edits require it). The normal full-suite sequence is
verifier `make check` → human review → `/commit-push-pr` `make check`.
The implementer does not run a duplicate full gate immediately before the
verifier. See [HARNESS.md](HARNESS.md#developer-commands) for check mechanics.

Normal stages restart from artifacts. `/handoff` is an explicit utility for an
exceptional interruption: a compact restart packet with paths, not copied plans.
Do not create a `00-status.md` or another workflow-status database. State already
lives in artifacts, task checkboxes, branches, PRs, and the archive.

## Skills policy

| Category | Skills | Loading rule |
|---|---|---|
| Factory lifecycle | explore, crystallize, shape-change | At the matching lifecycle stage |
| Conditional engineering techniques | domain-modeling, prototype, python-standards, karpathy-guidelines, spike, security review | Only when the actual technique is needed |
| Explicit utilities / meta-workflows | gauntlet-loop, grilling, handoff, setup-update, rescan-docs | User-invoked only during normal implementation |

Exploration may invoke grilling when the user asks for deep interrogation.
Domain modeling applies when terminology or domain boundaries are being designed,
not merely because an ADR is written. A spike may use prototype when an executable
experiment is the cheapest way to resolve uncertainty.

Superpowers remains optional. Selected TDD, systematic-debugging, or verification
techniques may be useful. Do not invoke its brainstorming, writing-plans,
subagent-driven-development, worktree orchestration, or branch-finishing
workflows: the factory owns those responsibilities. No technique may bypass a
factory gate. Retain any existing installation until representative runs show
whether these remaining techniques justify it; the refactor does not uninstall
the dependency. Record measurements using
[the workflow run format](.harness/evals/workflow-runs.md).
