# 03: Derive verification requirements from role and ownership

**Spec:** [Consumer verification and optional navigation](../spec.md)

**What to build:** Verification planning decides required checks from the
installation role and each changed path's ownership instead of the path prefix.
A consumer project can change its configuration and verify it with its normal
checks plus Engineering health checks. Editing managed implementation in a
consumer project is rejected with the supported route. Maintainer source in the
maintainer checkout still requires the maintainer suites.

**Blocked by:** 01 (Record the installation role), 02 (Make Engineering configuration project-owned).

**Status:** ready-for-agent

- [ ] A generated consumer project changes application roots or maintainability settings and prepares a valid plan with `make check` and `make engineering-check`, requiring no nonexistent target.
- [ ] Invalid project configuration fails verification visibly.
- [ ] A consumer change to managed implementation is rejected with an explanation and the update/upstream route; the outcome is INCOMPLETE, never PASS.
- [ ] Maintainer source changes in the maintainer checkout still require `make engineering-test` and `make engineering-evals`.
- [ ] The maintainer checkout's own configuration change requires only `make check` and `make engineering-check`.
- [ ] Removing a maintainer Make target cannot lower the required checks.
- [ ] Generated and adopted consumer projects classify identically.
- [ ] Requirements never depend on which Make targets happen to exist.
- [ ] Command-level `verify prepare` fixture tests cover each case above.
- [ ] Verification documentation, `/review` guidance and project instructions describe role-based requirements; affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

### Decisions (grilled 2026-09-27, human-approved)

- **Recorded role is trusted.** No extra check refuses `maintainer` outside the starter repository (ADR 0001 rejects inference). A wrong role fails closed: a consumer declaring `maintainer` is required to run maintainer suites it lacks; a maintainer checkout declaring `consumer` has its tooling edits rejected as managed-implementation edits. Document this; a role change is visible in the PR diff.
- **Project configuration = every manifest `preserve` entry** (currently `.engineering/config.toml`, `.engineering/dependencies.toml`, Graft package pins, `docs/agents/domain.md`, `docs/agents/issue-tracker.md`). Required: `make check` plus `make engineering-check`.
- **`section` and `hooks` files** (`CLAUDE.md`, `AGENTS.md`, `Makefile`, `.gitignore`, `.claude/settings.json`) are treated like project configuration: `make check` plus `make engineering-check`. Doctor already detects tampered managed sections or inactive hooks, so no second section parser is added.
- **Maintainer source (role `maintainer` only)** = all `file`-mode manifest entries plus non-distributed starter tooling (`.engineering/template/**`, `.engineering/tests/**`, `.engineering/evals/**`, `.engineering/scripts/**`, `.engineering/migrations/**`). Requires `make engineering-test` and `make engineering-evals` in addition. `preserve`/`section`/`hooks` paths follow the same rules in both roles.
- **Consumer edits to `file`-mode managed implementation** are rejected with the supported update/upstream route; outcome INCOMPLETE.
