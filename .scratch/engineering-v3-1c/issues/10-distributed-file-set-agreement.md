# 10: Make generation and update agree on the distributed file set

**Spec:** Split from ticket 08 at triage (2026-09-28); found by the ticket 05 behavioral review. Pre-existing on `main`.

**What to build:** Updating a freshly generated consumer project from the same
starter version changes nothing. Today `./engineering update` into a newly
generated project adds about 33 managed files (evals, the migrate package, the
migrate-from-openspec skill, the v2 baseline) and changes the Makefile section.
Ticket 03 rejects those as managed-implementation edits, so any consumer change
bundled with such an update is unverifiable. Establish one definition of the
distributed consumer file set used by both generation and update.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Investigate why generation (template build) and update (distribution manifest) disagree, and which set is correct for consumer projects (greenfield payload decisions in earlier tickets may apply; external migration tooling is intentionally not shipped to consumers).
- [ ] Generation and update derive the consumer file set from one source.
- [ ] A command-level test generates a project, then updates it from the same starter checkout, and asserts the update preview has no ADD/MERGE/REMOVE actions.
- [ ] Existing consumer projects that already received extra files are handled explicitly (kept, or removed with preview), never silently.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments
