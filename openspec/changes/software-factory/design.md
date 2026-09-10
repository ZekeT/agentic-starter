## Context

See proposal.md for motivation. The user supplied the architecture in instruct.md
and accepted the refinements recorded in intent.md before implementation.

## Decisions

- The factory owns stages and human gates. OpenSpec remains canonical behavioral
  truth, scripts provide deterministic enforcement, and techniques load only
  when useful. A second planning engine would duplicate accepted task groups.
- FAST verification discovers a branch diff; STANDARD/DEEP verification discovers
  group artifacts. This preserves independence without inventing FAST specs.
- DEEP architecture acceptance precedes program design and vertical slicing.
  Existing STANDARD tasks continue without new metadata or program design.
- The full source gate is non-mutating. Formatting is explicit; the verifier and
  pre-commit gate each run the full suite. The implementer uses targeted checks.
- A private temporary command log gives concise success and complete failure
  output. The original exit status must survive. No persistent log/state store.
- A final feature-doc check replaces the per-edit reminder. This is simpler than
  maintaining a per-session warning ledger and requires no persistent state.
- Keep workflow policy in FACTORY.md, runtime mechanics in HARNESS.md, and only
  everyday invariants in CLAUDE.md. Optional techniques remain installed pending
  evidence from representative runs.

## Risks / Trade-offs

- Existing Makefile callers expecting auto-fixes must call make fmt explicitly.
- Existing feature directories missing CLAUDE.md will fail the new final gate.
- Prose evals assert instructions, not all model behavior; a small prompt suite
  exercises routing separately from deterministic tests.
- Actual token savings require comparable workflow runs; no historical usage
  data is provided, so the check-count reduction is a prescribed-flow comparison.

## Migration Plan

Ship lifecycle instructions, check helpers, docs, hook wiring and evals together.
Regenerate the template manifest; update guidance explains removal of the retired
hook while preserving local customizations. Never modify current-state specs here;
archive only after the implementation PR merges and the human accepts the diff.
