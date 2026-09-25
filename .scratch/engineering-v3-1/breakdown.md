# Proposed implementation slices

Status: in progress — issues 01–03 recorded as implemented and verified; issue 04 merged; issue 05 implemented, awaiting human acceptance

The architecture decisions are recorded in spec.md. These slices preserve the
guide's implementation order while making each slice independently verifiable.

1. **Prepare OpenSpec inventory without removing source**
   - Blocked by: none.
   - Deliver the openspec-project preview/preparation commands and deprecated
     alias, deterministic inventory and indexes, temporary workspace, Git/source
     evidence, and clean-tree/path protection. Legacy-starter preserves OpenSpec
     and advertises the semantic handoff; adoption detects OpenSpec. Include
     regression coverage and command documentation.
2. **Produce evidence-based semantic reconciliation handoffs**
   - Blocked by: Prepare OpenSpec inventory without removing source.
   - Deliver the project-owned migration skill, all canonical and active-change
     classifications, human-review plan and structured application contract.
     Include static boundary evals and six representative fixture scenarios.
     Explicitly distinguish authored fixture decisions from model behavior.
3. **Finalize only accepted, current migration outputs**
   - Blocked by: Produce evidence-based semantic reconciliation handoffs.
   - Deliver previewable finalization, exact approved docs/removals, conflict and
     stale-input refusal, committed-history preservation, rollback/idempotency,
     validation reports and removable temporary evidence. Cover destructive
     behavior with regression tests and security review.
4. **Build and initialize a clean consumer template**
   - Blocked by: Finalize only accepted, current migration outputs.
   - Audit tracked files into one positive inclusion manifest; build deterministic
     output with consumer README/Makefile/configuration, project-owned migration
     skill and required runtime. Keep maintainer suites/history out. Bootstrap
     missing install state at setup without resetting existing baselines. Test
     integrity, fresh initialization and consumer commands.
   - Ordering follows the requested phases so the payload packages the completed
     migration surface; there is no inherent architectural dependency on finalization.
5. **Document and prove all onboarding paths**
   - Blocked by: Build and initialize a clean consumer template.
   - Finish upstream/consumer/maintainer documentation; place retained history
     with maintainers; exercise normal adoption, legacy upgrade, a realistic
     semantic migration and fresh-template setup. Run required gates and fresh
     independent reviews. Record actual evidence and any remaining human decisions.
   - Remote template publication remains deferred by the accepted decision.

## Delivery status — reconciled 2026-09-25

| Ticket | Status |
| --- | --- |
| 01–03 | Implemented and verified per ticket evidence; human-review status not independently reconciled |
| 04 | Completed / merged in [PR #26](https://github.com/ZekeT/agentic-starter/pull/26), local merge `0f4d2af` |
| 05 | Implemented; awaiting human acceptance; current proof under verification change `onboarding` |

This updates delivery tracking only; the approved slice scope below is unchanged.

## Approval

The user approved the public-command/filesystem test boundaries, ticket sizes and
phase ordering in this conversation.
