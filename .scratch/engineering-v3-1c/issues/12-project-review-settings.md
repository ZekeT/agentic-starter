# 12: Project review settings enable the documentation tier

**Spec:** [Review tiers and carried evidence](../spec-b-review-tiers.md) (slice B)

**What to build:** Project configuration gains a `[review]` section with
`documentation` and `sensitive` glob lists. Documentation-listed paths not caught
by starter rules can use the `documentation` tier, so a prose-only change needs
one fresh behavioral reviewer plus `make check`. Projects can add sensitive
paths but never weaken starter rules, and a change cannot weaken the rules that
apply to itself. Existing projects receive the settings only through an approved
update; generated and adopted projects start with identical defaults.

**Blocked by:** 11 (Declare a review tier checked against a starter-rule floor).

**Status:** in-progress — implemented on `feat/v3-1c-12-review-settings`; awaiting independent verification

- [x] `[review]` with `documentation` and `sensitive` glob lists is read from project configuration; invalid settings fail planning visibly, consistent with existing configuration validation.
- [x] A path matching `documentation` and no starter or project sensitive/exclusion rule floors at `documentation`; domain context and ADRs are eligible, agent-policy Markdown is not.
- [x] Project `sensitive` additions raise the floor; nothing in project configuration can reduce the starter exclusion or sensitive lists.
- [x] A change editing `[review]` floors at least `ordinary` and uses the stricter of base and proposed settings, including starter lists from base and proposed managed implementation.
- [x] A documentation-only change reaches PASS with one behavioral report and passing `make check`.
- [x] The maintainer checkout's configuration lists `docs/**` only, not maintainer docs shipped as policy.
- [x] An Engineering migration adds `[review]` with `documentation = ["README.md", "docs/**"]` and empty `sensitive`, shown in the update preview, applied only with the approved update, preserving existing configuration values.
- [x] Generated and adopted projects contain identical `[review]` defaults.
- [x] Policy text and the `/review` flow describe the documentation tier and its reviewer brief (check docs against code and recorded decisions).
- [x] Command-level tests: verification fixtures for the scenarios above; update preview/apply/decline and generation/adoption template tests.
- [x] Affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review (`sensitive`: three separate sessions).

- Follow-ups from ticket 11 review (human-accepted 2026-09-29): add root
  `GNUmakefile`/`makefile` (optionally `*.mk`), `.engineering/scripts/**` and
  `.claude/statusline.sh` to the starter sensitive list; decide whether `graft.py`
  is sensitive; document the leading `/` root anchor in the pattern comment.

- Implementation notes: configuration schema 2 adds `[review]`; the schema 1 → 2
  migration appends the defaults and shows as `MIGRATE` in the update preview.
  `verification_requirements.path_floor` evaluates starter rules, project
  sensitive additions, agent policy, the configuration file itself ("review
  settings", always ordinary), then project documentation; `review_settings`
  reads base and proposed settings and the per-path maximum wins. Starter lists
  stay in code: they sit in a module that is sensitive in the maintainer
  checkout and managed implementation in consumers, so base and proposed lists
  agree whenever verification can pass.
- Follow-ups done: `GNUmakefile`, `makefile`, `*.mk` (build recipe),
  `.engineering/scripts/**` (check script), `.claude/statusline.sh`
  (agent-executed script) are starter sensitive; `graft.py` joins the maintainer
  dependency modules (it executes the pinned Graft CLI); the leading `/` anchor
  is documented. Remaining maintainability notes from ticket 11 (`operate()`
  growth, preflight floor via `snapshot()`, `SESSIONS` table) are unchanged.
- Remaining: `make engineering-test`, three separate independent review
  sessions (sensitive), human review, publication.
