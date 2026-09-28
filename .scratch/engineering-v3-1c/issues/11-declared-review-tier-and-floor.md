# 11: Declare a review tier checked against a starter-rule floor

**Spec:** [Review tiers and carried evidence](../spec-b-review-tiers.md) (slice B)

**What to build:** Verification plans declare a review tier (`documentation`,
`ordinary` or `sensitive`) with a reason instead of the `security_required`
boolean. The verification-requirements module computes a tier floor from the
starter-owned rules and rejects plans that declare less, naming the paths and
rules behind the floor. The tier decides the required reviewer roles; one fresh
session may file two reports for an ordinary change but never for a sensitive
one. Evidence records and `verify status` show what the evidence proves, and
`/ship` refuses stale classification. The project `[review]` settings do not
exist yet, so no path is documentation and the floor is at least ordinary: main
never becomes weaker than today's review, apart from the combined ordinary
session the spec asks for.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] Plans require `tier` (one of the three values) and nonempty `tier_reason`; a plan with `security_required`/`security_reason` or missing the new fields is invalid with a message naming the replacement.
- [ ] One deep function in the verification-requirements module returns required checks, tier floor, per-category paths and required roles for a (checkout, plan); callers do not assemble these separately.
- [ ] Starter sensitive list floors at `sensitive`: dependency manifests and locks (`pyproject.toml`, `uv.lock`, `package*.json`, the Engineering dependency registry), `.claude/settings*.json`, hooks, `.github/workflows/**`, `Makefile`, Engineering launchers; in the maintainer checkout also the dependency, skill-installation, apply, transaction, update, migration, publication and verification modules.
- [ ] Starter documentation exclusion list (agent-policy files: `CLAUDE.md`, `AGENTS.md`, `.claude/**`, skills, `REVIEW.md`, `ENGINEERING.md`, Engineering docs, agent docs) floors at `ordinary`; every other path floors at `ordinary` until project documentation settings exist (ticket 12).
- [ ] A mixed change takes the highest per-path floor; declaring below the floor is rejected with the paths and rules that set it; declaring above the floor with a reason is accepted.
- [ ] Required roles: `documentation` → behavioral; `ordinary` → maintainability + behavioral; `sensitive` → all three. Outcome reads roles from the tier.
- [ ] Reports sharing a `reviewer` identifier across roles are accepted for `ordinary` and rejected at record time and in status for `sensitive`.
- [ ] Required checks are unchanged by tier.
- [ ] The evidence record stores floor, per-category paths, required checks and roles; its format version increases; a record without tier data is unsupported and instructs preparing again.
- [ ] `verify status` reports tier, tier reason, floor, required and missing roles, and whether one reviewer identifier covered multiple roles.
- [ ] The `./engineering publish` preflight recomputes the floor for the current scope and refuses evidence whose recorded tier is below it.
- [ ] `CLAUDE.md`, `REVIEW.md`, the verification guide and the `/review` and `/ship` skills describe tiers, the floor and combined ordinary sessions; `/review` spawns only the required roles and one combined session when permitted. Reviewer agent definitions keep read-only independence; pinned upstream skills unchanged.
- [ ] Command-level tests through `verify prepare | record | check | status` on consumer and maintainer fixtures, plus a publication preflight test, cover the scenarios above.
- [ ] Affected evals updated; no wording permits self-certification.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review (this change is itself `sensitive`: three separate sessions).
