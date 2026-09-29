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

**Status:** implemented — independent verification pending

- [x] Investigate why generation (template build) and update (distribution manifest) disagree, and which set is correct for consumer projects (greenfield payload decisions in earlier tickets may apply; external migration tooling is intentionally not shipped to consumers).
- [x] Generation and update derive the consumer file set from one source.
- [x] A command-level test generates a project, then updates it from the same starter checkout, and asserts the update preview has no ADD/MERGE/REMOVE actions.
- [x] Existing consumer projects that already received extra files are handled explicitly (kept, or removed with preview), never silently.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

## Implementation and handoff

Branch: `fix/v3-1c-10-distributed-file-set`, based on `main` at `68490a0`,
which includes ticket 06 / PR #42.

Generation, manifest creation, adoption/update and legacy conversion resolve
consumer content from `.engineering/template/files.json`. The source mapping
selects the consumer Makefile and configuration; navigation content remains
installed by its dependency. Generated manifests retain distribution hash history
so the same-source update preserves metadata too. External migration tools,
skills, evals and historical baselines stay in the source checkout.

Command-level regressions in `.engineering/tests/test_template.py` cover an
unchanged preview and apply, explicit retirement of pristine extra files,
customization conflicts and preservation of unmanaged neighbors. Targeted
validation passed 60 template/installation/navigation tests and 29 legacy/template
tests. Typechecking and the maintainability gate passed (existing size warnings).

Independent verification: change `v3-1c-10`, plan
`.engineering/state/verification/v3-1c-10-plan.json`. Run
`./engineering verify status --change v3-1c-10` for current checks and independent
behavioral, maintainability and security reports. The unchecked full-check
criterion above remains pending until the record establishes complete PASS.
Human acceptance and publication are separate; neither is authorized by this
implementation request.
