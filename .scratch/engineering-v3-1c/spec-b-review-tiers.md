# Engineering v3.1c — Review tiers and carried evidence (slice B)

Status: ready-for-agent — shared understanding and test seams approved 2026-09-28;
tickets 11–13 in [breakdown](breakdown.md)

Source: [intent](intent.md), section "B. Review tiers and carried evidence".
Slices A and C are in [spec](spec.md). Vocabulary follows the product context
glossary (review tier, tier floor, carried evidence); decisions follow
[ADR 0001](../../docs/adr/0001-explicit-installation-role.md) and
[ADR 0002](../../docs/adr/0002-review-tiers-and-carried-evidence.md).

## Problem Statement

A developer using the starter pays for the same three independent review
sessions whatever the change: a README typo, an ordinary feature and a change to
dependency execution all need a maintainability review, a behavioral review and
usually a hand-set security decision. Whether security review applies is a
boolean the implementer sets alone, so the author of a change decides how much
scrutiny it gets.

Evidence is also fragile. Any movement of the comparison base — a clean rebase,
or merely fetching an advanced `main` — changes the snapshot fingerprint and
discards every report. In v3.1c tickets 01–05 and 07 this produced about fifteen
review rounds of three reviewers; four rebase-only rounds found nothing blocking.
The cost falls on the developer's time and usage limits, and it pushes people
toward skipping the process rather than using it.

## Solution

Each verification plan declares a review tier — `documentation`, `ordinary` or
`sensitive` — with a reason. The tier decides which reviewer roles are required
and whether one fresh session may cover two roles. The verification tool
computes a tier floor from the changed paths and the project's review settings
and rejects any plan that declares less. Starter-owned rules always win:
agent-policy Markdown is never documentation, and dependency, hook, settings,
workflow and destructive-operation paths are always sensitive. A project can
add to these rules but never weaken them, and a change cannot weaken the rules
that apply to itself.

When a change is rebased cleanly onto an advanced base — its own diff unchanged,
nothing upstream touching its scope — reviewer reports carry forward to the new
snapshot and only the authoritative checks rerun. Anyone may run that rerun
because it involves no judgment and the tool records exactly what ran. Base-tip
movement alone no longer invalidates evidence; shipping still requires the
change to be based on the current remote base, which carried evidence makes
cheap.

## User Stories

1. As a consumer-project developer, I want a documentation-only change to need one fresh reviewer, so that fixing prose does not cost three review sessions.
2. As a consumer-project developer, I want the documentation reviewer to check my docs against the code and recorded decisions, so that documentation that contradicts the code is still caught.
3. As a consumer-project developer, I want `make check` to remain required for every tier, so that formatting, links and size limits still gate documentation.
4. As a consumer-project developer, I want an ordinary change to allow one fresh session to file both the maintainability and the behavioral report, so that routine work needs one review session instead of two.
5. As a consumer-project developer, I want the two reports from a combined session to stay separate verdicts, so that the record still shows what each role concluded.
6. As a security-conscious maintainer, I want sensitive changes to require three separate fresh sessions, so that high-risk changes keep independent perspectives.
7. As a security-conscious maintainer, I want the tool to reject a sensitive plan whose reports share a reviewer identifier, so that combined sessions cannot slip into the sensitive tier.
8. As a reviewer, I want a plan whose declared tier is below the computed tier floor to be rejected with the paths and rules that set the floor, so that an implementer cannot under-declare risk.
9. As an implementer, I want to raise the tier above the floor with a stated reason, so that risk the paths cannot show — such as application authentication code — gets a security review.
10. As an implementer, I want a change that mixes documentation and code to take the highest tier any path requires, so that I never have to split a change to get classification right.
11. As a maintainer, I want agent-policy files — `CLAUDE.md`, `AGENTS.md`, `.claude/**`, skills, `REVIEW.md`, `ENGINEERING.md`, Engineering docs and agent docs — to never count as documentation, so that changes to how agents behave get full review.
12. As a consumer-project developer, I want domain context and ADRs to remain eligible for the documentation tier, so that glossary and decision records are cheap to maintain.
13. As a consumer-project developer, I want to configure which paths count as documentation in project configuration, so that the tier fits my repository layout.
14. As a consumer-project developer, I want to add paths to the sensitive list in project configuration, so that my project's own risky areas always get security review.
15. As a security-conscious maintainer, I want the starter's exclusion and sensitive lists to be impossible to reduce through project configuration, so that a project cannot opt out of baseline protection.
16. As a reviewer, I want the tier floor for a change that edits the review settings to use the stricter of the base and proposed settings, so that a change cannot lower its own required review.
17. As a reviewer, I want any change to the review settings to be at least ordinary, so that loosening review rules is itself reviewed properly.
18. As a maintainer, I want the maintainer checkout's dependency, installation, transaction, update, migration, publication and verification modules to be sensitive, so that starter changes that execute dependencies or destroy or publish data always get security review.
19. As a reviewer, I want the tier, its reason, the computed floor and the path categories behind it recorded in evidence, so that I can audit why a change got the review it did.
20. As a human accepting a change, I want `verify status` to show tier, floor, required roles and whether one session covered two roles, so that I know what the evidence actually proves.
21. As a consumer-project developer, I want tiers to leave required checks unchanged, so that a lower review tier never silently weakens deterministic verification.
22. As an implementer, I want reviewer reports to carry forward when I rebase cleanly onto an advanced base, so that a rebase does not cost another full round of reviews.
23. As an implementer, I want carry-forward to happen automatically during `verify prepare` when its conditions hold, so that I do not need a separate command or manual record editing.
24. As a reviewer, I want carry-forward to require an identical own diff, unchanged plan, tools and checks, and no upstream change to any path or explicit input in scope, so that carried reports only cover content they actually reviewed.
25. As a reviewer, I want carried reports to record the snapshot they came from, so that the chain of evidence stays traceable.
26. As a reviewer, I want authoritative checks to rerun on every carried snapshot, with status incomplete until they pass, so that interaction bugs hidden by a clean textual merge are still caught.
27. As an implementer, I want to be allowed to run `verify check` myself for a carried snapshot, so that a deterministic rerun does not need a fresh verifier session.
28. As a reviewer, I want a failing check on a carried snapshot to produce FAIL and drop the carried behavioral report, so that a broken rebase can never ship on old approval.
29. As an implementer, I want a rebase whose upstream changes overlap my scope to carry nothing and route to the existing review-corrections procedure, so that reviewers re-examine interactions while still retaining justified unchanged coverage.
30. As an implementer, I want evidence to stay current when the base tip moves without a rebase, so that fetching `main` does not discard reviews.
31. As a human shipping a change, I want `/ship` to still refuse when the remote base has moved, so that a published PR has been checked against the base it merges into.
32. As a human shipping a change, I want `/ship` to recompute the tier floor for the current scope and refuse evidence whose recorded tier is below it, so that stale classification cannot be published.
33. As a human shipping a change, I want `/ship` to accept current carried evidence without new review, so that a clean rebase before shipping is cheap.
34. As an implementer with evidence recorded before tiers existed, I want the tool to tell me to prepare again rather than infer a tier, so that no evidence is silently downgraded.
35. As an existing consumer-project owner, I want the update preview to show the new review settings and their documentation defaults before anything changes, so that lowering review for documentation is a visible, approved decision.
36. As an existing consumer-project owner, I want the review settings migration applied only with the approved update, so that my review requirements never change silently.
37. As a new consumer-project developer, I want generated and adopted projects to start with the same documentation defaults, so that both installation routes classify identically.
38. As a maintainer, I want the maintainer checkout's own settings to list `docs/**` but not maintainer docs that are shipped as policy, so that the starter's own policy prose keeps full review.
39. As an agent following project policy, I want `CLAUDE.md`, `REVIEW.md` and the verification guide to describe tiers, combined sessions and carried-snapshot check runs, so that I request the right reviewers and never self-certify outside the permitted rerun.
40. As a reviewer agent, I want the `/review` flow to spawn only the roles the tier requires, and one combined session when the tier permits, so that review cost matches risk.

## Implementation Decisions

- **Plan schema**: the plan's `security_required` and `security_reason` fields are replaced by `tier` (one of `documentation`, `ordinary`, `sensitive`) and `tier_reason` (nonempty text). A plan still carrying the old fields, or missing the new ones, is invalid with a message naming the replacement.
- **Tier floor module**: the existing verification-requirements module, which already classifies paths by installation role and manifest ownership, gains the tier floor computation alongside required checks. It is one deep function from (checkout, plan) to required checks, floor, categories and required roles; callers do not assemble these separately.
- **Floor rules** (highest applicable wins, per path, then across the change):
  - `sensitive` if the path matches the starter sensitive list or the project's `sensitive` additions. Starter list: dependency manifests and locks (`pyproject.toml`, `uv.lock`, `package*.json`, the Engineering dependency registry), `.claude/settings*.json`, hooks, `.github/workflows/**`, `Makefile`, Engineering launchers; in the maintainer checkout, also the dependency, skill-installation, apply, transaction, update, migration, publication and verification modules.
  - `ordinary` if the path matches the starter documentation exclusion list (agent-policy files) or is review settings in project configuration, or matches no documentation pattern.
  - `documentation` only if the path matches the project's `documentation` list and none of the above.
- **Review settings**: a `[review]` section in project configuration with `documentation` and `sensitive` glob lists. The floor uses the stricter result of evaluating base and proposed settings (including the starter lists from base and proposed managed implementation). Invalid settings fail planning visibly, consistent with existing configuration validation.
- **Required roles**: `documentation` → `behavioral`; `ordinary` → `maintainability` and `behavioral`; `sensitive` → `maintainability`, `behavioral` and `security`. Roles remain the fixed set of three. Outcome computation reads roles from the tier, not a boolean.
- **Combined sessions**: reports with the same `reviewer` identifier for two roles are accepted in the ordinary tier and rejected at record time and in status for the sensitive tier.
- **Required checks unchanged**: checks continue to derive from ownership categories and navigation; tiers never add or remove checks.
- **Evidence record**: stores the computed floor, per-category paths, required checks and required roles alongside the plan. `verify status` reports tier, tier reason, floor, required and missing roles, and whether one reviewer identifier covers multiple roles. The record format version increases; a record without tier data is unsupported and instructs preparing again.
- **Snapshot identity**: the base tip is removed from the fingerprint and kept as recorded, advisory data. The merge-base remains part of content identity. Freshness comparisons in status and publication compare identity fields, not the advisory tip.
- **Carried evidence**: during `verify prepare`, when a previous record exists for the change and all conditions hold — each path's own patch identical, plan (other than base-derived fields), tools and checks unchanged, and no path changed between the previous and new merge-base intersecting the plan's paths or explicit inputs — the new record copies the previous reviewer reports, each marked with `carried_from` naming the previous snapshot, and has no checks. Reports are rebound to the new snapshot only through this mechanism; manual relabelling remains forbidden. The previous record is still saved as historical evidence.
- **Carried check runs**: `verify check` on a record containing carried reports keeps those reports and records fresh check results. Any failing check makes the outcome FAIL and removes the carried behavioral report. On a record without carried reports, current behavior is unchanged (checks clear behavioral proof first).
- **Overlap**: if any condition fails, nothing is carried; the existing previous-evidence reference and review-corrections procedure apply.
- **Publication**: the preflight keeps requiring the remote base tip to equal the tip recorded at the latest prepare. It additionally recomputes the tier floor for the current scope and refuses when the recorded tier is below it. Carried evidence that is current and PASS is accepted without further review.
- **Migration and generation**: an Engineering migration adds `[review]` with `documentation = ["README.md", "docs/**"]` and an empty `sensitive` list to existing project configuration, reported in the update preview and applied only with the approved update. Generated and adopted projects start with the same section. The maintainer checkout's own configuration lists `docs/**` only.
- **Policy and workflow text**: `CLAUDE.md`, `REVIEW.md`, the verification guide and the `/review` and `/ship` skills describe tiers, the floor, combined ordinary sessions, carried evidence and the permitted non-verifier check run for carried snapshots only. Reviewer agent definitions keep their read-only independence rules. Pinned upstream skills are not modified.

## Testing Decisions

- Good tests assert externally observable outcomes of the commands users and agents run — exit status, reported tier, floor, missing roles, rejection reasons, resulting configuration — not internal functions or exact prose.
- **Seam 1 — `./engineering verify prepare | record | check | status`** against consumer and maintainer-checkout fixture repositories. Scenarios: documentation-only change reaches PASS with one behavioral report and `make check`; agent-policy Markdown floors at ordinary; sensitive-list paths floor at sensitive; declared tier below floor rejected with reasons; mixed change takes highest tier; project additions raise, project removals cannot lower; editing `[review]` uses the stricter of base and proposed settings; shared reviewer id accepted for ordinary, rejected for sensitive; legacy record without tier requires preparing again; old plan fields rejected. Carry-forward: clean rebase with no overlap carries reports and stays incomplete until checks pass; failing rerun is FAIL and drops the behavioral report; overlapping upstream change, changed own patch, changed plan, tools or checks carry nothing; base-tip movement without rebase keeps status current. Fixtures gain a helper that advances `main` and rebases the feature branch. Prior art: verification integration tests and verification-requirements integration tests.
- **Seam 2 — `./engineering publish` preflight**: refuses evidence whose tier is below the recomputed floor; refuses when the remote base moved; accepts current carried PASS evidence. Prior art: publication integration tests.
- **Seam 3 — `./engineering update` preview/apply**: the `[review]` migration appears in the preview, applies only on approval and preserves existing configuration values; generated and adopted projects contain identical defaults. Prior art: installation, migration and template tests.
- **Seam 4 — policy evals**: agent-policy wording for tiers, combined sessions and carried-snapshot check runs; no instruction permits self-certification outside the carried rerun.
- Starter tooling changes also run `make engineering-test` and `make engineering-evals`.

## Out of Scope

- Evidence freshness performance and prepared-checkout reuse (slice E).
- Adoption compatibility preview (D) and review explanations (F).
- Changes to the review-corrections procedure beyond linking it from the overlap case.
- Mapping reviewer roles to paths for partial re-review.
- Size- or line-count-based review thresholds.
- Changing which checks are required.
- Authenticating reviewer sessions; the tool still validates attestations, not identities.
- Relaxing the publication remote-base guard.
- Replacing or patching pinned upstream skills.

## Further Notes

- Ticket 09 also edits the verification-requirements module; implement B first and rebase 09 onto it, per the agreed order (B → 06 → 09 → 10 → 08).
- The permitted implementer check run is a deliberate, narrow loosening of the rule that the verifier runs `make check`; it applies only to snapshots holding carried reports and must be worded that way in policy.
- The publication guard makes base-tip movement matter at ship time even though it no longer invalidates review evidence; this is intended — shipping rebases, and carry-forward keeps that cheap.
- Carry-forward conditions are deliberately conservative; a false negative costs a review round, a false positive would ship unreviewed interactions.
