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

**Status:** ready-for-agent

- [ ] `[review]` with `documentation` and `sensitive` glob lists is read from project configuration; invalid settings fail planning visibly, consistent with existing configuration validation.
- [ ] A path matching `documentation` and no starter or project sensitive/exclusion rule floors at `documentation`; domain context and ADRs are eligible, agent-policy Markdown is not.
- [ ] Project `sensitive` additions raise the floor; nothing in project configuration can reduce the starter exclusion or sensitive lists.
- [ ] A change editing `[review]` floors at least `ordinary` and uses the stricter of base and proposed settings, including starter lists from base and proposed managed implementation.
- [ ] A documentation-only change reaches PASS with one behavioral report and passing `make check`.
- [ ] The maintainer checkout's configuration lists `docs/**` only, not maintainer docs shipped as policy.
- [ ] An Engineering migration adds `[review]` with `documentation = ["README.md", "docs/**"]` and empty `sensitive`, shown in the update preview, applied only with the approved update, preserving existing configuration values.
- [ ] Generated and adopted projects contain identical `[review]` defaults.
- [ ] Policy text and the `/review` flow describe the documentation tier and its reviewer brief (check docs against code and recorded decisions).
- [ ] Command-level tests: verification fixtures for the scenarios above; update preview/apply/decline and generation/adoption template tests.
- [ ] Affected evals updated.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review (`sensitive`: three separate sessions).
