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

**Status:** completed — merged in [PR #43](https://github.com/ZekeT/agentic-starter/pull/43), observed at `86c3df2`

- [x] Investigate why generation (template build) and update (distribution manifest) disagree, and which set is correct for consumer projects (greenfield payload decisions in earlier tickets may apply; external migration tooling is intentionally not shipped to consumers).
- [x] Generation and update derive the consumer file set from one source.
- [x] A command-level test generates a project, then updates it from the same starter checkout, and asserts the update preview has no ADD/MERGE/REMOVE actions.
- [x] Existing consumer projects that already received extra files are handled explicitly (kept, or removed with preview), never silently.
- [x] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

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
behavioral, maintainability and security reports. Current evidence is kept in
that record; the dated entries below preserve historical verification outcomes.
Human acceptance and publication are separate; neither is authorized by this
implementation request.

### Independent review (2026-09-30)

Implementation head `11e1645`, snapshot
`6a0b0940153c29b72ef0e930892db657be2affebb5598d20174a60b0352f80c8`:
maintainability PASS and security PASS, with no material findings. Behavioral
FAIL: `make check`, `make engineering-check` and `make engineering-evals` passed,
but `make engineering-test` finished with 511 passed and two failed in 768.92s.
The eval run passed 13 static cases and skipped five optional prompt cases.

The failures are `test_configuration_seeds_from_maintainer_template_copy`
(`.engineering/tests/test_installation.py:435`), whose source fixture lacks the
new configuration mapping, and
`test_migration_skill_and_contract_are_in_distribution`
(`.engineering/tests/test_semantic_fixtures.py:94`), which still expects the
external migration skill in the consumer manifest. The new no-op preview/apply
and retired-file safety tests passed.

Recommended correction: declare the configuration source mapping in the
maintainer fixture and assert that the migration skill/contract stay available
externally while absent from consumer distribution. Human direction was requested
under REVIEW.md before editing these tests. The full-check criterion remains
unchecked. Reports and check output are preserved under change `v3-1c-10`.

This tracking-only update follows review and changes snapshot identity; the
results above describe the named implementation snapshot. After authorized
correction, prepare the complete scope and obtain current independent evidence.
Human acceptance, publication and merge remain outstanding.

### Authorized corrections (2026-09-30)

The human authorized both test updates. The configuration-seeding fixture now
declares its consumer configuration mapping and also verifies that adoption
leaves the customized maintainer configuration unchanged. The migration test
checks that both skill and contract remain present in the external checkout
and absent from the consumer manifest. Production behavior is unchanged.

Fresh verification is pending under the same change and plan. The prior failed
run remains historical evidence; the full-check criterion stays unchecked until
the current evidence record reports PASS.

### Correction verification and handoff (2026-09-30)

Correction head `572db89`, snapshot
`7d9e59afb93cafd363149b142dbdd3f7b662a999c799c80757e6392d17925a59`:
all four authoritative checks passed, including 513 tests in 790.87s and
13 static evals (five optional prompt cases skipped). Independent behavioral,
maintainability and security reviews passed. Both historical findings are
resolved; production code was unchanged by the corrections.

The full-check criterion is satisfied by that independent run. This final
tracking update is included in the prepared scope for re-verification; use
`./engineering verify status --change v3-1c-10` for current snapshot and proof.
No further tracker edits are needed to report the evidence tool's outcome.
Human acceptance, publication and merge remain separate and outstanding.

### Publication (2026-09-30)

The human accepted the reviewed scope with `/ship`. Published
[PR #43](https://github.com/ZekeT/agentic-starter/pull/43) from head `b2a8676`.
Published verification snapshot
`fdf5693510d0dbd2c2bc3a97092774870f6f38b605675530af9bf5adfe7ea4c5`
has PASS for all four required commands and all three independent reviews:
513 tests passed in 774.40s; 13 static evals passed and five optional prompt
cases were skipped. Shipping reused this proof without repeating checks.

This delivery update and the matching breakdown status are local bookkeeping
outside the published verified head. They change the local snapshot and require
evidence reassessment before any later publication. Merge remains pending.

### Merge observed (2026-09-30)

Fetched `origin/main` contains merge commit `86c3df2` for PR #43. Ticket 10
is complete and ticket 08’s prerequisite is satisfied.
