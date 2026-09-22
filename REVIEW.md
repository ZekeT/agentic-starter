# Human review

Automate formatting, lint, types, tests, documentation and size checks. Spend
human attention on correctness, design judgment, assumptions and consequences.

Review in this order:

1. What behavior changed?
2. Does it match the agreed ticket, spec, or request?
3. What architectural boundaries changed?
4. What could break? Use Graft blast-radius evidence when useful.
5. Were unnecessary abstractions introduced?
6. Were unrelated files touched?
7. What did automated and independent verification prove?
8. What remains unverified?

Require current evidence from a fresh read-only maintainability review
(PASS / CONCERNS) and behavioral verification (PASS / FAIL). Reuse matching
evidence under [.engineering/docs/verification.md](.engineering/docs/verification.md);
fresh context does not mean repeating an unchanged review at every later gate. They independently discover the diff, expected
behavior, source and relevant tests. Never substitute an implementation agent's
narrative for their evidence. Record and resolve material concerns; label nits.

Run a read-only security review for authentication, authorization, secrets,
cryptography, untrusted input, privilege boundaries, payments, destructive
operations, sensitive storage, network exposure or dependency execution.
Trivial documentation changes do not require a security review.

Use `/show-me` for a design, request path, module boundary or diff that is hard
to understand. Visual explanations are normally ephemeral. No diagram is a gate.

Invoking `/implement` authorizes scoped local commits, not acceptance or
publication. After completed acceptance review, `/ship` accepts the unchanged
presented scope and authorizes remaining scoped commits, push and actual PR/MR
creation when blockers are resolved. It cannot supply missing review. Honor
narrower requests and existing authorization; merge/force-push remain separate.
Reuse current proof without duplicate checks. See
[publication](.engineering/docs/publication.md) for the provider-independent flow.

## Findings and human-directed corrections

Review is read-only for application content. Present changed behavior, requirement
coverage, consequences, risks and gaps. For each finding provide **what** is wrong,
**why** it matters, **how** to address it, your **recommendation and rationale**,
and concrete evidence (path/line, observed failure or requirement). Identify a
violated requirement, demonstrated defect or concrete risk. Consult the settled
spec, ADRs and recorded human decisions. Label preference-only alternatives as
non-blocking; they do not justify a CONCERNS/FAIL verdict by themselves.
Wait for human instructions identifying which fixes to make before editing.

Authorized ordinary corrections need no new spec, tickets or dedicated fix
command. Preserve agreed behavior and decisions; corrections may remain
uncommitted. After code fixes, format and prepare current evidence, rerun
authoritative checks and obtain independent inspection of the fix and affected
behavior. Reviewers may retain evidence for unchanged areas only with an explicit
scope justification; scope or architecture changes require broader review.
Follow the incremental evidence procedure in
[verification.md](.engineering/docs/verification.md#review-corrections).
Present updated acceptance scope, checks, findings and gaps. Prior acceptance
does not automatically transfer to changed content.

Pause edits after two unsuccessful attempts at one finding, or before a fix would
undo a settled decision. Explain the conflict, evidence, alternatives and behavior
to preserve; route to focused `/grill-me`. Record the human-agreed resolution in
the relevant decision/spec or ticket before resuming and reverifying. Material
scope expansion returns to `/to-spec` and `/to-tickets`. This bounds attempts at a
finding, not the number of legitimate findings reviewers may raise.
