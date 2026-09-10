## Why

Maintenance currently incurs the full planning workflow while architectural work
lacks a distinct program-design boundary. Broad skill orchestration and repeated
full checks add context and cost without independent evidence.

## What Changes

- Route FAST, STANDARD, and DEEP without changing canonical OpenSpec ownership.
- Add DEEP shape-change and program design after architecture acceptance.
- Make implementation context selective and verifier context independent.
- **BREAKING**: `make check` stops auto-fixing source; developers run `make fmt`.
- Replace repeated feature-documentation reminders with a final stateless gate.
- Make successful checks concise while retaining full failures and exit status.
- Separate factory policy from harness mechanics and narrow skill triggers.
- Add static/behavioral evals and a lightweight workflow measurement format.

## Capabilities

### New Capabilities
- `factory-workflow`: tier routing, accepted artifact transitions and slice ownership.
- `factory-verification`: independent verification and deterministic check behavior.

### Modified Capabilities
None. Existing submission conventions and credential-free static eval requirements
are preserved; new factory invariants receive additional cases.

## Impact

Workflow: DEEP. Architecture-affecting: yes, factory orchestration boundaries.
Changes affect lifecycle skills, command preambles, verifier, Makefile helpers,
hook wiring, factory/harness docs, starter packaging and evals. No added framework
or runtime dependency. Existing STANDARD changes require no program-design migration.
