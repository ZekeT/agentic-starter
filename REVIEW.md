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

Require a fresh read-only maintainability review (PASS / CONCERNS) and behavioral
verification (PASS / FAIL). They independently discover the diff, expected
behavior, source and relevant tests. Never substitute an implementation agent's
narrative for their evidence. Record and resolve material concerns; label nits.

Run a read-only security review for authentication, authorization, secrets,
cryptography, untrusted input, privilege boundaries, payments, destructive
operations, sensitive storage, network exposure or dependency execution.
Trivial documentation changes do not require a security review.

Use `/show-me` for a design, request path, module boundary or diff that is hard
to understand. Visual explanations are normally ephemeral. No diagram is a gate.

Only the human authorizes shipping. Scope approval to the commit/push/PR or MR/
merge requested. Existing authorization need not be requested again. `/ship`
runs a final `make check` and respects the project's Git hosting provider.
