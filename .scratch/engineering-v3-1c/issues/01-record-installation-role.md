# 01: Record the installation role

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Every installation states whether it is the maintainer
checkout or a consumer project. Generation and adoption record `consumer`; this
repository records `maintainer`; updating an existing installation records its
role automatically. Verification refuses to plan without a recorded role and
tells the developer how to fix it, so classification is never guessed (ADR 0001).

**Blocked by:** None (can start immediately).

**Status:** implemented — awaiting independent verification

- [x] A generated consumer project records the consumer role in its committed install state.
- [x] An adopted project records the consumer role identically.
- [x] This repository's install state records the maintainer role.
- [x] Updating an existing installation without a role records it through an Engineering migration, visible in the update preview.
- [x] Verification planning with no recorded role fails with an actionable next step; no default role is assumed.
- [x] An invalid role value fails visibly.
- [x] Command-level fixture tests cover generation, adoption, update migration and the missing-role blocker.
- [x] Verification and onboarding documentation describe the role; affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

- 2026-09-27 implementation (branch `feat/v3-1c-01-record-installation-role`):
  install state carries `role`; setup (`init-installation`), adoption and legacy
  conversion write `consumer`; `make manifest` writes `maintainer` for this
  checkout; `update` keeps a recorded role and records `consumer` for role-less
  state as a visible "Engineering migration" preview line. `verify prepare`
  fails INCOMPLETE with the update/`make manifest` next step when the role is
  missing, and rejects unknown values. Required checks are unchanged (ticket 03).
  Implementer-run evidence, not verification: `make check`, `make
  engineering-test` (322 passed) and `make engineering-evals` (11/11 static)
  passed. Remaining: fresh independent review and verification, human acceptance,
  publication and merge.
- 2026-09-27 human-authorized review corrections: (1) `verify` now reads the
  role from the materialized proposed checkout, so prepare, status, check and
  record use the committed install state (or its working bytes only when the
  path is in plan scope); an out-of-scope working edit can neither supply nor
  remove the role. Command-level fixture test added; verification.md wording
  made precise. (2) `.engineering/manifest.json` and install state regenerated
  once from `main`, so `previous` lists carry no never-committed intermediate
  hashes; role stays `maintainer`. (3) Merged the duplicated `prepare_status`
  test helper into `prepare`. Implementer-run checks only, not verification.
  Remaining: fresh independent review and verification of the corrections,
  human acceptance, publication and merge.
