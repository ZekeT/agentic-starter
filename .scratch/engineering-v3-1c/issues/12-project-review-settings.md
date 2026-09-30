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

**Status:** completed — merged in [PR #40](https://github.com/ZekeT/agentic-starter/pull/40)

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
- [x] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review (`sensitive`: three separate sessions).

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
- `/code-review` (2026-09-29), both axes: human accepted the recommendations.
  Keep `graft.py` sensitive; keep starter lists in code, recorded in ADR 0002;
  keep the any-depth `README.md` default from the spec; leave `CLAUDE.md` and
  `/ship` unchanged. Fixed: configuration reading moved to
  `settings.review_settings`; the 1 → 2 migration keeps a trailing comment on
  `schema_version`; clearer test helper names. Not changed (judgement calls):
  defaults kept in both the migration and the template, the review-settings
  dict type, and rebuilding the rule table per path.
- 2026-09-29: independent evidence for snapshot 0cb85cb5…: behavioral (after a
  first FAIL from an unprepared checkout environment; `uv sync --offline
  --all-extras` fixed it), maintainability and security PASS from three separate
  sessions; `make check`, `make engineering-check`, `make engineering-test` (480
  passed) and `make engineering-evals` (13/13 static) exit 0. Human accepted and
  published via `/ship` as PR #40 (not merged).
- Non-blocking follow-ups from review (moved to ticket 13): the `docs/**` default also covers
  non-prose files under `docs/`; a broad project pattern such as `**` can reach
  `.pre-commit-config.yaml`, `.envrc`, `CODEOWNERS` and installation metadata
  (consider starter-sensitive additions); base-settings reading ignores unknown
  `[review]` keys; `test_review_tiers.py` is at 374 code lines (split before 500).

### Status audit (2026-09-30)

Merge `21ec8b6` is present in `origin/main`. Earlier pending-merge notes are historical. Ticket 13 subsequently narrowed the documentation default to `docs/**/*.md` with human approval.
