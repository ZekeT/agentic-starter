# Agentic Starter — Software Factory Refactor

## Objective

Refactor this repository from a single heavy coding-agent workflow into a lightweight **software factory blueprint**.

Do not replace the existing system.

Preserve its strongest primitives:

* OpenSpec current-state specifications as canonical product/system truth.
* OpenSpec change artifacts for work in flight.
* One independently shippable task group = one branch = one PR.
* Branch existence as the concurrency mutex.
* Human gates before commit/PR and before archive.
* Fresh-context verification.
* Deterministic hooks and shell scripts for safety and validation.
* Harness behavioral/static evals.

The goal is to reduce unnecessary context and token consumption while making the factory suitable for small fixes, ordinary features, and large architectural work.

---

# Architectural principle

The layers should have distinct responsibilities:

```text
Agent runtime
Claude Code / Codex / HumanLayer / similar
        │
        ▼
Factory
workflow routing, gates, lifecycle, context boundaries
        │
        ├── OpenSpec
        │   behavioral/system truth
        │
        ├── deterministic scripts/hooks
        │   enforcement and backpressure
        │
        └── optional skills
            specialized techniques
```

Superpowers must not be a second workflow engine.

If Superpowers remains installed, use individual techniques only where they provide unique value.

---

# 1. Introduce workflow tiers

The factory needs three workflow sizes.

## FAST

Use for:

* obvious bug fixes
* tiny refactors
* naming changes
* localized implementation changes with no product/spec impact

Flow:

```text
implement
→ verify
→ review
→ commit/PR
```

FAST must not require an OpenSpec change if observable system behavior is unchanged.

If the work changes observable behavior or uncovers ambiguity, promote it to STANDARD.

---

## STANDARD

Use for normal product/behavior changes.

Flow:

```text
/explore
→ intent.md
→ human gate

/crystallize
→ proposal.md
→ delta specs
→ design.md
→ tasks.md
→ human gate

/dev-change
→ verifier
→ human /review
→ /commit-push-pr

after all groups merge:
/archive-change
```

This should remain close to the current workflow.

---

## DEEP

Use when any of these are true:

* major architectural impact
* substantial cross-module change
* important unknowns
* risky migration
* new subsystem
* hard-to-reverse technical decision
* several viable architectural approaches
* implementation likely spans many independently shippable slices

Flow:

```text
/explore
→ intent.md

optional /spike
→ research / experiment
→ ADR
→ design evidence

/crystallize
→ proposal
→ delta specs
→ architecture/design
STOP

/shape-change
→ program-design.md
→ independently shippable vertical task groups

/dev-change per group
→ verifier
→ review
→ PR

/archive-change
```

Do not force DEEP ceremony onto STANDARD or FAST tasks.

---

# 2. Modify `/explore`

Keep `intent.md`.

Do not expand this skill into a planning system.

Add a lightweight classification:

```text
Workflow: FAST | STANDARD | DEEP
Reason: <one sentence>
```

FAST should normally stop without creating an OpenSpec change unless behavior changes.

STANDARD should preserve the existing intent workflow.

DEEP should explicitly note which uncertainty/design issues justify the deeper path.

The classification is advisory and may be promoted later when new complexity appears.

Never silently demote a DEEP change after major architectural uncertainty has been identified.

---

# 3. Modify `/crystallize`

Make its behavior depend on workflow tier.

For STANDARD:

Keep approximately the existing behavior:

```text
intent
→ proposal
→ delta specs
→ design
→ task groups
```

For DEEP:

Generate:

```text
proposal.md
delta specs
design.md
```

but DO NOT generate final `tasks.md`.

Instead, stop at a human gate and direct the user to:

```text
/shape-change <slug>
```

`design.md` for DEEP work should cover architectural approach and decisions, not implementation-by-file detail.

---

# 4. Add `/shape-change`

Create a new command/skill for DEEP changes.

Purpose:

Translate an accepted architecture/design into an implementation-ready program design and independently shippable vertical slices.

Create:

```text
openspec/changes/<slug>/program-design.md
openspec/changes/<slug>/tasks.md
```

`program-design.md` must contain only implementation-relevant information.

Recommended structure:

```markdown
# Program Design

## Implementation shape

### Files to create
- ...

### Files to modify
- ...

## Important types and interfaces
- type/interface/signature
- responsibility
- relevant invariants

## Data and control flow
1. ...
2. ...
3. ...

## Integration boundaries
- ...

## Test design

### Behavior tests
- ...

### Failure cases
- ...

### Neighbouring regression risks
- ...

## Migration / compatibility
- if relevant

## Least-confident decisions
- decision
- uncertainty
- consequence if wrong
```

Then create `tasks.md`.

Task groups must remain vertical and independently shippable.

Do not create groups such as:

```text
1. database
2. backend
3. frontend
4. tests
```

when none can ship independently.

Prefer groups such as:

```text
1. complete read-only user flow
2. mutation path with validation
3. migration/backfill support
```

when those can each be reviewed and shipped safely.

Preserve:

```text
one task group = one branch = one PR
```

---

# 5. Simplify `/dev-change`

The task group is already the implementation plan.

Do not re-plan it.

Do not invoke generic planning or brainstorming methodologies.

Remove mandatory dependence on broad Superpowers workflows.

Individual techniques such as TDD may be used when useful, but the factory owns orchestration.

During implementation:

* load only the claimed task group
* relevant delta specs
* relevant design/program-design section
* relevant local feature instructions
* files needed for the implementation

Do not load the entire OpenSpec tree or documentation tree.

Use targeted tests while coding.

Do not run the full `make check` immediately before dispatching a verifier that will run the same check.

At completion, dispatch the fresh `verifier`.

Stop without committing.

---

# 6. Make the verifier the independent full gate

Keep the verifier read-only and fresh-context.

Its responsibilities should be:

```text
1. Run the full deterministic check suite.
2. Verify every relevant delta-spec scenario.
3. Verify every completed task claim.
4. Exercise changed behavior directly where possible.
5. Exercise the nearest likely regression paths.
6. Report PASS or FAIL without editing anything.
```

The verifier should receive:

```text
change slug
task group number
```

It should discover the required artifacts itself.

Do not send it the implementation session's reasoning or narrative.

That information contaminates the independent review.

---

# 7. Make command output context-efficient

Implement a reusable shell helper such as:

```text
run_quiet "<label>" <command>
```

Behavior:

On success:

```text
✓ format
✓ lint
✓ types
✓ tests
```

On failure:

```text
✗ tests

<complete relevant command output>
```

Apply this to `make check`.

Do not hide useful failures.

Do hide routine successful output.

The human terminal may optionally support a verbose mode, but the default agent-facing command should be concise.

---

# 8. Preserve a final pre-commit gate

`/commit-push-pr` should still run the deterministic full gate before committing.

This protects against edits made after the verifier ran.

Therefore the normal expensive full-suite sequence becomes:

```text
verifier:
make check

human review

commit-push-pr:
make check
```

not:

```text
implementer:
make check

verifier:
make check

commit-push-pr:
make check
```

---

# 9. Reduce root `CLAUDE.md`

Treat root `CLAUDE.md` as scarce context.

It should contain only instructions useful in most coding sessions.

Keep:

```text
build/check command
canonical OpenSpec truth rule
simplicity rule
retrieval/lazy-loading rule
branch/task invariant
.env prohibition
important stop/escalation rules
```

Move detailed lifecycle explanations to factory documentation.

Remove or shorten duplicated explanations already contained in command/skill files.

Do not globally recommend loading `karpathy-guidelines`.

Do not state that Superpowers is a required methodology.

Replace that section with approximately:

```text
Skills are progressive disclosure. Load specialized skills only when their trigger applies. The factory workflow in this repository owns planning, implementation stages, verification, and shipping.
```

Aim for a root instruction file that can be understood in roughly one screenful to two screenfuls.

Do not delete essential invariants merely to hit an arbitrary line count.

---

# 10. Reposition `HARNESS.md`

The repository is a software factory blueprint implemented using an agent harness.

Reflect that distinction in documentation.

Preferred structure:

```text
README.md
    explains what the project is:
    a portable software-factory starter

FACTORY.md
    workflow tiers
    artifacts
    lifecycle
    human gates
    context/session model

HARNESS.md
    Claude Code implementation details:
    commands
    hooks
    agents
    shell scripts
    skills
```

If adding `FACTORY.md` creates too much duplication, refactor `HARNESS.md` into the factory document first and defer the rename.

Do not maintain two copies of the same rules.

---

# 11. Context boundaries are first-class

Design every major artifact so the next stage can begin in a fresh session.

The intended property is:

```text
accepted artifact + repository state
=
sufficient context for next phase
```

A new implementation agent should not need the original brainstorming transcript.

A verifier should not need the implementation conversation.

An archive agent should not need either.

Explicitly document the recommended fresh-session boundaries:

```text
after intent
after design/spec
after program design
per implementation task group
verification/review
archive
```

Do not require a specific agent product's context-forking feature.

The repository artifacts must remain sufficient on their own.

---

# 12. Demote Superpowers

Do not remove Superpowers simply for the sake of removing a dependency.

First eliminate workflow overlap.

The factory owns:

```text
exploration
planning
architecture
program design
task decomposition
worktree/branch ownership
review lifecycle
shipping
```

Superpowers may provide selected techniques such as:

```text
TDD
systematic debugging
verification techniques
```

only when useful.

Do not invoke:

```text
brainstorming
writing-plans
subagent-driven-development
worktree orchestration
branch-finishing workflows
```

from Superpowers when the factory already provides those responsibilities.

After this refactor, evaluate whether the remaining Superpowers usage justifies keeping the dependency.

Do not remove it before measuring.

---

# 13. Skills policy

Classify skills into three categories.

## Factory lifecycle

These participate directly in the lifecycle:

```text
explore
crystallize
shape-change
```

## Conditional engineering techniques

Load only when applicable:

```text
domain-modeling
prototype
python-standards
karpathy-guidelines
spike
security review
```

## Explicit utilities / meta-workflows

Never auto-trigger during normal implementation:

```text
gauntlet-loop
grilling
handoff
setup-update
rescan-docs
```

`grilling` may be explicitly invoked from exploration when the user asks for deep interrogation.

`prototype` may be invoked from a spike when an executable experiment is the cheapest way to resolve uncertainty.

`domain-modeling` should activate only when terminology/domain boundaries are actually being designed.

---

# 14. Repurpose `handoff`

Make `handoff` about context transfer rather than another planning methodology.

Its output should be a compact restart packet containing:

```text
Goal
Current stage
Accepted artifacts
Current branch/change/group
Decisions already made
Open blockers
Exact next action
Files the next agent should read first
```

Do not copy large artifact contents into the handoff.

Reference paths.

The handoff exists for exceptional interruptions; normal factory stages should already be restartable from their artifacts.

---

# 15. Hooks

Preserve deterministic enforcement:

```text
pre_tool_dangerous.py
pre_tool_env_guard.py
post_tool_secrets.py
```

Keep `post_tool_lint.py` lightweight:

* edited Python file only
* non-mutating
* silent on success
* useful error output on failure

Review `post_tool_feature_claude_reminder.py`.

Do not repeatedly inject the same reminder after every edit.

Prefer either:

* emit the reminder once per affected feature/session, or
* enforce missing feature documentation during the final deterministic check.

Choose the simpler implementation.

Do not introduce persistent project state merely to remember that a warning was shown.

---

# 16. Factory evals

Expand `.harness/evals/` so these architectural properties are regression-tested.

Add static evals for at least:

```text
FAST does not require OpenSpec for behavior-neutral changes.
STANDARD crystallize generates tasks.
DEEP crystallize does not generate final tasks.
DEEP points to shape-change.
shape-change creates program-design + vertical task groups.
dev-change does not invoke Superpowers planning workflows.
dev-change does not run a redundant full make check before verifier.
verifier runs the deterministic full gate.
commit-push-pr retains its final gate.
root CLAUDE.md does not globally require Superpowers.
gauntlet-loop remains user-invocable-only.
handoff remains user-invocable-only.
canonical openspec/specs rule remains intact.
branch-existence mutex remains intact.
```

Add a small number of behavioral prompt evals for workflow routing.

Example cases:

```text
"Fix typo in error message"
→ FAST

"Add password reset behavior"
→ STANDARD

"Replace persistence architecture while maintaining compatibility"
→ DEEP
```

Do not add large numbers of LLM evals if static assertions can enforce the same property.

---

# 17. Add token/context observability

We suspect the current system is token-heavy, but do not optimize purely from intuition.

Add lightweight documentation or tooling that makes it possible to compare representative workflow runs.

Record at minimum:

```text
workflow tier
number of agent/subagent sessions
number of full check runs
number of skill invocations
approximate context/token usage when available
number of tool calls when available
result: success/failure
```

Create representative scenarios:

```text
tiny bug
normal feature
large architectural feature
```

Compare before/after behavior if historical data is available.

Do not build a telemetry platform.

A simple eval/result format is sufficient.

---

# 18. Do not introduce redundant state

Do NOT add a `00-status.md` or equivalent workflow-status database.

State already exists in:

```text
OpenSpec artifacts
tasks.md checkboxes
git branches
PR state
archive state
```

Do not create another artifact that must remain synchronized with those.

---

# 19. Do not copy HumanLayer or the Software Factory skill wholesale

Borrow principles, not file structures.

From the Software Factory approach, incorporate:

```text
program design before implementation for large changes
file/type/interface/test-level planning
vertical slices
explicit uncertainty
```

From HumanLayer/context-engineering practice, incorporate:

```text
artifact boundaries
fresh-context sessions
context isolation
progressive disclosure
compact successful tool output
human review before expensive mistakes
```

Retain this repository's stronger existing mechanisms where they already solve the problem.

---

# 20. Implementation order

Implement this in small commits.

Recommended sequence:

```text
1. Add factory terminology and FAST/STANDARD/DEEP routing.
2. Add shape-change + program-design artifact.
3. Split DEEP crystallize behavior.
4. Simplify dev-change and verifier ownership.
5. Add compact make-check output.
6. Reduce CLAUDE.md.
7. Adjust skill auto-trigger policy / Superpowers references.
8. Reduce feature-CLAUDE reminder repetition.
9. Update HARNESS/FACTORY/README documentation.
10. Add/update static and behavioral evals.
11. Run full eval suite and make check.
```

Avoid rewriting unrelated scripts.

Preserve backwards compatibility with existing active OpenSpec changes where reasonable.

Existing STANDARD changes with a populated `tasks.md` must remain usable by `/dev-change`.

Do not force them through `/shape-change`.

---

# Acceptance criteria

The refactor is complete when all of the following are true:

```text
A tiny maintenance change has a clearly documented FAST path.

A normal behavior change can still follow the current
intent → spec/design/tasks → implementation → archive lifecycle.

A large change has an explicit architecture/design gate followed by
program design before implementation.

Each implementation task group remains independently shippable and maps
1:1 to a branch and PR.

A fresh implementation session can start from durable artifacts without
the exploration transcript.

A fresh verifier can determine correctness without implementation-session
reasoning.

Successful full checks emit compact output; failures retain useful details.

The implementation lifecycle no longer invokes overlapping planning
methodologies.

Superpowers is optional/specialized rather than the factory coordinator.

Canonical OpenSpec current-state specs and archive semantics are unchanged.

Deterministic security/env/git protections remain intact.

Harness evals enforce the important factory invariants.

Existing STANDARD changes remain implementable.

`make check` and the repository's eval suite pass.
```

---

# Final deliverable

When implementation is complete, report:

```text
1. Files added
2. Files modified
3. Files removed, if any
4. Old workflow vs new workflow
5. Superpowers responsibilities removed/retained
6. Context/token-efficiency changes
7. Backwards-compatibility considerations
8. Eval results
9. Any unresolved decisions
```

Do not add additional frameworks unless required to implement the design above.

Prefer deleting duplicated instructions over adding another abstraction.

The target is a **smaller, more composable factory**, not a larger harness.
