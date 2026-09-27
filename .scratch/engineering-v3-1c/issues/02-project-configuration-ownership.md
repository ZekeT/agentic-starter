# 02: Make Engineering configuration project-owned

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** The Engineering configuration file becomes project
configuration. A developer's values survive starter updates; updates validate
them and apply schema migrations but never overwrite them. Managed
implementation keeps its current ownership, so a consumer edit to it is still
reported as an update conflict.

**Blocked by:** None (can start immediately).

**Status:** completed — merged in [PR #34](https://github.com/ZekeT/agentic-starter/pull/34)

- [x] Generated and adopted projects record the configuration file as project-owned rather than whole-file managed.
- [x] Updating keeps customised configuration values unchanged.
- [x] Updating across a configuration schema change migrates values and reports the migration in its preview.
- [x] Invalid project configuration makes update and doctor fail visibly.
- [x] Existing installations whose manifest still marks the file as managed are migrated to project ownership without losing values.
- [x] A consumer edit to managed implementation is still reported as an update conflict and never overwritten.
- [x] The template copy of the configuration remains maintainer source in the maintainer checkout.
- [x] Command-level fixture tests cover preservation, schema migration, ownership migration and the managed-edit conflict.
- [x] Installation/update documentation reflects the ownership; affected evals updated.
- [x] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

- Implementation (branch `feat/v3-1c-02-project-configuration-ownership`):
  `.engineering/config.toml` uses the existing `preserve` ownership and is
  seeded like other project configuration, from `.engineering/template/config.toml`
  when the template is the maintainer checkout. Update/adopt planning validates
  it (invalid stops the plan), applies ordered schema migrations from
  `settings.MIGRATIONS` as a `MIGRATE` preview action, and reports previously
  managed entries as `PRESERVE … Now project-owned` while dropping their state
  baseline. No schema change exists yet; the migration test injects one.
  Remaining: independent verification and review, human acceptance, publication.
- Review corrections (human-authorized): `settings.validate` is now the single
  configuration validity rule and returns the maintainability `Config`;
  `config.load_config` delegates to it, so update and doctor share it. A missing
  or failed starter schema migration raises `settings.MigrationGap`, and update
  reports it as a starter defect ("update the starter or report the missing
  migration") instead of asking the project to repair its configuration; covered
  by `test_missing_schema_migration_blames_the_starter`. Status unchanged:
  implemented — awaiting independent verification.

- 2026-09-27: Rebased onto ticket 01; independent behavioral, maintainability and security review PASS (snapshot d2156027…); human-accepted and published as PR #34; merged into main (6d67c3a).
