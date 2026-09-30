# Explicit installation role decides maintainer verification

Status: accepted (2026-09-27)

Every installation records its installation role — maintainer checkout or consumer project — and verification requires the maintainer suites only when the role is maintainer and a changed path is maintainer source according to its manifest ownership. A missing role blocks verification; a migration records it for existing installations. Consumer projects cannot independently change managed implementation through verification. Ticket 08 adds a bounded exception: update output may match a fetched, pinned starter distribution named explicitly in the verification plan. Proposed manifest digests alone remain insufficient. The recorded installation role still determines which suites apply.

## Considered options

Recorded so the decision is not reopened in a loop:

- **Path prefix (`.engineering/`)** — the original rule. Rejected: consumer projects legitimately edit project configuration under that prefix, which demanded maintainer suites they do not have.
- **Existence of a Make target or template source** — rejected: inference from whatever happens to be present; deleting a file would silently downgrade verification.
- **Missing role defaults to consumer** — rejected for the same downgrade reason; the role must be present.
