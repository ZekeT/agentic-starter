# Intent: software-factory

Workflow: DEEP
Reason: Cross-cutting lifecycle ownership and context boundaries affect every stage and downstream starter updates.

## Classification
New capabilities `factory-workflow` and `factory-verification`. Existing
canonical change-submission and harness-evals requirements remain intact.

## Problem
The single heavy workflow imposes planning/context costs on small fixes and
mixes factory ownership with broad Superpowers orchestration. Verification and
shipping instructions disagree about ownership of repeated full checks.

## Proposed outcome
Implement the software-factory refactor specified in the user's `instruct.md`:
three workflow tiers, architecture then program design for DEEP, independent
verification, compact checks, progressive skills, and durable stage boundaries.

## Accepted decisions
The user authorized implementation of the supplied design and confirmed:
- `make check` becomes non-mutating; `make fmt` explicitly fixes source before
  verification and again if subsequent edits need it.
- Cosmetic wording corrections can be FAST when meaning and behavior stay
  unchanged; contractual output changes require STANDARD.
- FAST verifier input is only the branch name. STANDARD/DEEP input is only
  change slug and task group, with no implementation narrative.

## Constraints
Preserve canonical specs, archive semantics, branch/task ownership, human gates,
and deterministic security/env/git protections. Keep existing STANDARD tasks
usable. Retain installed Superpowers pending measurement. Do not add telemetry
or duplicate workflow state. Commits and PRs remain subject to human review.

## Open questions
No remaining design decision identified at intent acceptance. Runtime prompt
eval authentication and actual historical token measurements must be reported
from evidence, never assumed.
