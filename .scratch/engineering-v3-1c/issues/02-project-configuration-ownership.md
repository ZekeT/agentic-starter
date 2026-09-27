# 02: Make Engineering configuration project-owned

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** The Engineering configuration file becomes project
configuration. A developer's values survive starter updates; updates validate
them and apply schema migrations but never overwrite them. Managed
implementation keeps its current ownership, so a consumer edit to it is still
reported as an update conflict.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Generated and adopted projects record the configuration file as project-owned rather than whole-file managed.
- [ ] Updating keeps customised configuration values unchanged.
- [ ] Updating across a configuration schema change migrates values and reports the migration in its preview.
- [ ] Invalid project configuration makes update and doctor fail visibly.
- [ ] Existing installations whose manifest still marks the file as managed are migrated to project ownership without losing values.
- [ ] A consumer edit to managed implementation is still reported as an update conflict and never overwritten.
- [ ] The template copy of the configuration remains maintainer source in the maintainer checkout.
- [ ] Command-level fixture tests cover preservation, schema migration, ownership migration and the managed-edit conflict.
- [ ] Installation/update documentation reflects the ownership; affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments
