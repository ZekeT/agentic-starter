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

**Status:** in-progress — implemented on `feat/v3-1c-11-review-tiers`; awaiting independent verification

- [x] Plans require `tier` (one of the three values) and nonempty `tier_reason`; a plan with `security_required`/`security_reason` or missing the new fields is invalid with a message naming the replacement.
- [x] One deep function in the verification-requirements module returns required checks, tier floor, per-category paths and required roles for a (checkout, plan); callers do not assemble these separately.
- [x] Starter sensitive list floors at `sensitive`: dependency manifests and locks (`pyproject.toml`, `uv.lock`, `package*.json`, the Engineering dependency registry), `.claude/settings*.json`, hooks, `.github/workflows/**`, `Makefile`, Engineering launchers; in the maintainer checkout also the dependency, skill-installation, apply, transaction, update, migration, publication and verification modules.
- [x] Starter documentation exclusion list (agent-policy files: `CLAUDE.md`, `AGENTS.md`, `.claude/**`, skills, `REVIEW.md`, `ENGINEERING.md`, Engineering docs, agent docs) floors at `ordinary`; every other path floors at `ordinary` until project documentation settings exist (ticket 12).
- [x] A mixed change takes the highest per-path floor; declaring below the floor is rejected with the paths and rules that set it; declaring above the floor with a reason is accepted.
- [x] Required roles: `documentation` → behavioral; `ordinary` → maintainability + behavioral; `sensitive` → all three. Outcome reads roles from the tier.
- [x] Reports sharing a `reviewer` identifier across roles are accepted for `ordinary` and rejected at record time and in status for `sensitive`.
- [x] Required checks are unchanged by tier.
- [x] The evidence record stores floor, per-category paths, required checks and roles; its format version increases; a record without tier data is unsupported and instructs preparing again.
- [x] `verify status` reports tier, tier reason, floor, required and missing roles, and whether one reviewer identifier covered multiple roles.
- [x] The `./engineering publish` preflight recomputes the floor for the current scope and refuses evidence whose recorded tier is below it.
- [x] `CLAUDE.md`, `REVIEW.md`, the verification guide and the `/review` and `/ship` skills describe tiers, the floor and combined ordinary sessions; `/review` spawns only the required roles and one combined session when permitted. Reviewer agent definitions keep read-only independence; pinned upstream skills unchanged.
- [x] Command-level tests through `verify prepare | record | check | status` on consumer and maintainer fixtures, plus a publication preflight test, cover the scenarios above.
- [x] Affected evals updated; no wording permits self-certification.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review (this change is itself `sensitive`: three separate sessions).

- Implementation notes: `verification_requirements.requirements(checkout, plan)`
  returns checks, floor, per-tier paths with the rule that set each, and roles;
  `materialize` returns it, so `prepare`, `status`, `check`, `record` and the
  publish preflight all recompute the floor for the current scope. Record format
  version 2. Maintainer sensitive modules also include `adoption.py` and
  `installation.py` (update/installation) and `registry.py` (dependency registry);
  `*package-lock.json` covers the fixed Graft lock.
- Evidence (implementer-run, not independent): new `test_review_tiers.py`
  (consumer + maintainer fixtures), migrated verification, requirements, publication recovery,
  publication, greenfield and navigation tests pass (`make engineering-test`: 455 passed, the one failing recovery test then fixed and rerun); `make engineering-evals`
  static cases pass except `offline-installation-health` (see below), including
  new `013-review-tiers`.
- Blocker outside this change: `make check` fails only at `./engineering doctor`
  with `ERROR [dependency] graft: MISSING` — the ignored local
  `.engineering/state/dependencies.json` does not match the installed Graft
  outputs. No dependency or doctor file is changed here; resolving it needs a
  human decision (e.g. `./engineering deps install graft --apply`).
- Remaining: three separate independent review sessions (this change is
  sensitive), human review, publication.
