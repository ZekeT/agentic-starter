# 01: Record the installation role

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Every installation states whether it is the maintainer
checkout or a consumer project. Generation and adoption record `consumer`; this
repository records `maintainer`; updating an existing installation records its
role automatically. Verification refuses to plan without a recorded role and
tells the developer how to fix it, so classification is never guessed (ADR 0001).

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] A generated consumer project records the consumer role in its committed install state.
- [ ] An adopted project records the consumer role identically.
- [ ] This repository's install state records the maintainer role.
- [ ] Updating an existing installation without a role records it through an Engineering migration, visible in the update preview.
- [ ] Verification planning with no recorded role fails with an actionable next step; no default role is assumed.
- [ ] An invalid role value fails visibly.
- [ ] Command-level fixture tests cover generation, adoption, update migration and the missing-role blocker.
- [ ] Verification and onboarding documentation describe the role; affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments
