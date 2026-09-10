# Program Design

## Implementation shape

### Files to create
- FACTORY.md: runtime-independent lifecycle policy.
- .claude/skills/shape-change/SKILL.md: DEEP implementation-readiness stage.
- .harness/scripts/lib/run_quiet.sh: reusable private-log command wrapper.
- .harness/scripts/cmd_check.sh and check_feature_docs.py: non-mutating gate.
- .harness/evals/cases/012–014 and 103–105: static invariants and routing prompts.
- .harness/evals/workflow-runs.md: measurement format and scenarios.
- .harness/tests/integration/test_factory_checks.py: executable gate/claim regressions.

### Files to modify
- Lifecycle skills and commands: tier ownership, selective loading, explicit gates.
- Verifier: independent identifier-based discovery, full gate, coverage reporting.
- Makefile: explicit formatting and compact non-mutating checks.
- Hook settings: retire repeating feature reminder; preserve security/env hooks.
- CLAUDE.md, HARNESS.md, README.md and affected setup/testing docs: remove overlap.
- Manifest generator and migration/update packaging: include new callers/helpers.
- openspec/config.yaml: align generated artifact guidance with tier ownership.

## Important types and interfaces
- `run_quiet label command args...`: returns command exit status; success prints
  one line, failure prints complete captured stdout/stderr. Optional VERBOSE=1.
- `cmd_check.sh [all|lint]`: source root from SRC, sequential checks, no source fixes.
- `check_feature_docs.py [source-root]`: exit 1 lists missing feature instructions;
  ignores empty scaffolds and caches, never writes state.
- Verifier inputs: slug + group or FAST branch only; no session narrative.

## Data and control flow
1. Accepted intent selects artifact path by tier.
2. STANDARD creates tasks; DEEP accepts architecture then creates program design/tasks.
3. Group claim atomically creates its branch and prints selective context references.
4. Implementer tests locally and formats; verifier discovers and checks independently.
5. Human reviews; shipping reruns the deterministic gate before committing.

## Integration boundaries
- Existing branch/base helpers remain authoritative; keep race-to-create mutex.
- OpenSpec CLI owns creation/validation/archive; canonical specs remain untouched.
- Manifest and migration copy paths must include dependencies of shipped commands.

## Test design

### Behavior tests
- Integration fixtures execute make check, run_quiet, branch claims and shipping failures.
- Static evals guard artifact split, skill triggers, canonical truth and gate ownership.
- Three routing prompts exercise FAST/STANDARD/DEEP classification.

### Failure cases
- Formatting or pytest failures propagate without source fixes or truncated evidence.
- Existing claim rejects a second claimant; DEEP without program design cannot claim.
- Missing feature docs fail consistently without creating a warning ledger.

### Neighbouring regression risks
- Legacy STANDARD tasks still claim and load without new metadata.
- Starter migration/update still copies instructions and dependencies safely.
- Existing secret/env/dangerous-command hooks retain their implementation and wiring.

## Migration / compatibility
See design.md Migration Plan. Keep pytest no-tests and empty-source behavior.

## Least-confident decisions
- Instruction-only routing cannot guarantee every model follows a tier; static
  checks plus representative prompt evals provide evidence, not a universal proof.
- Optional Superpowers value is unmeasured; retain installed techniques and
  collect representative workflow observations before removal.
