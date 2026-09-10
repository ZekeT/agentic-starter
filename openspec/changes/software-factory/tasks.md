## 1. Deliver a coherent tiered factory workflow

Shipping boundary: lifecycle instructions, check ownership, helpers and packaging
ship together so no intermediate release dispatches a read-only verifier to a
mutating gate or points DEEP work to an unavailable stage. One branch
`feat/software-factory-g1`, one reviewed PR. No prerequisite groups.

Context:
- specs/factory-workflow/spec.md: all scenarios
- specs/factory-verification/spec.md: all scenarios
- design.md: Decisions, Risks / Trade-offs, Migration Plan
- program-design.md: interfaces, integration boundaries and test design

- [x] 1.1 Add FAST/STANDARD/DEEP routing and shape-change with vertical tasks; verify static artifact-routing evals.
- [x] 1.2 Simplify implementation context and independent verifier inputs; verify legacy and DEEP branch-claim integration tests.
- [x] 1.3 Separate formatting from full gates, preserve command failures, and replace feature reminders; verify executable check integration tests.
- [x] 1.4 Update documentation, conditional/explicit skill policies, and downstream packaging; verify policy and manifest evals plus migration tests.
- [x] 1.5 Add routing prompt cases and workflow measurement format; verify eval discovery and required measurement fields.
- [x] 1.6 Run full evals, make check and harness tests, then obtain fresh verifier evidence and stop for human review without committing.
