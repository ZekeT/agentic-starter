# Engineering v3.1c — Consumer verification and optional navigation

Status: ready-for-agent — shared understanding and test seams approved 2026-09-27

Source: [intent](intent.md). Covers slices A and C only; B, D, E and F remain
intent-level until their own grilling sessions. Vocabulary follows the product
context glossary; the installation role follows ADR 0001.

## Problem Statement

A developer who generates or adopts the starter is told to edit the project
configuration, but doing so makes verification demand the starter's maintainer
suites, which consumer projects deliberately do not have. The only ways forward
are to fake the requirement or abandon verification. Verification currently
decides this from the path prefix alone, so it cannot tell the developer's own
settings from the starter's implementation.

The same developer must also install Graft and its Node toolchain before any
application code exists to navigate. Graft is marked required, doctor fails
without it, and agent policy tells agents to use it. Many developers never want
Graft, yet they cannot opt out, and the documentation does not say which
prerequisites are core and which serve an optional capability.

## Solution

Every installation records its installation role: maintainer checkout or
consumer project. Verification combines that role with each changed path's
manifest ownership. Project configuration changes need the project's normal
checks plus the Engineering health checks. Maintainer source changes in the
maintainer checkout still need the maintainer suites. A consumer project that
edits managed implementation is told why that cannot be verified and how to
change it properly. A missing role blocks verification instead of guessing.

Navigation becomes an optional capability selected by the existing navigation
provider setting. New consumer projects start with navigation disabled and
nothing Graft-related installed. Enabling it runs the normal dependency preview
and install and adds the Graft launcher, skill, package pins and agent guidance.
Doctor reports disabled, ready, enabled-without-roots (warning) and
enabled-but-broken states distinctly. Existing installations keep Graft when
they visibly use it; otherwise the update preview proposes disabling it.
Documentation states that Node is a core prerequisite for skill installation and
that Graft is optional.

## User Stories

1. As a consumer-project developer, I want to change my navigation roots and see verification plan successfully, so that following onboarding does not dead-end.
2. As a consumer-project developer, I want to change maintainability settings and verify them, so that tuning thresholds is an ordinary change.
3. As a consumer-project developer, I want an invalid project configuration to fail verification visibly, so that a broken setting is never certified.
4. As a consumer-project developer, I want configuration changes checked by my normal checks and the Engineering health checks, so that the new settings are actually exercised.
5. As a consumer-project developer, I want verification never to require targets my project does not have, so that the plan is achievable.
6. As a consumer-project developer, I want an edit to managed implementation rejected with an explanation and the supported route, so that I know to update the starter or contribute upstream.
7. As a consumer-project developer, I want a managed-implementation edit reported as INCOMPLETE rather than PASS, so that no one mistakes it for verified work.
8. As a consumer-project developer, I want an update to report my managed-implementation edit as a conflict, so that it is never silently overwritten.
9. As a consumer-project developer, I want starter updates to keep my project configuration values, so that updating never resets my settings.
10. As a consumer-project developer, I want updates to migrate my project configuration's schema when needed, so that my settings stay valid across versions.
11. As a starter maintainer, I want changes to maintainer source to keep requiring the maintainer suites, so that releases stay proven.
12. As a starter maintainer, I want editing my checkout's own project configuration to need only the project and health checks, so that the rule is consistent with consumer projects.
13. As a starter maintainer, I want deleting a maintainer target or the role record never to downgrade required verification, so that the gate cannot be bypassed by omission.
14. As any developer, I want verification to block with a clear next step when the installation role is missing, so that classification is never guessed.
15. As an existing-installation owner, I want an update to record my installation role automatically, so that the new requirement costs me nothing.
16. As an adopter, I want an adopted project classified exactly like a generated one, so that the installation route never changes verification.
17. As a new developer, I want a generated project to start with navigation disabled, so that setup does not need Graft.
18. As a new developer, I want setup, doctor and verification to succeed without Graft installed when navigation is disabled, so that the core workflow works immediately.
19. As a new developer, I want agents to search and read source directly when navigation is disabled, with no instructions pointing at an absent tool.
20. As a developer, I want to enable Graft by setting the navigation provider and applying the normal dependency flow, so that activation is previewed and authorized like any other dependency.
21. As a developer, I want enabling navigation to install the pinned Graft and its launcher, skill, package pins and agent guidance together, so that the capability is complete.
22. As a developer, I want disabling navigation to remove its gate obligations and conditional managed content while keeping my Graft index and root settings, so that I lose no project data.
23. As a developer, I want the update preview to show every file disabling navigation removes, so that nothing disappears unexpectedly.
24. As a developer, I want doctor to say navigation is disabled without treating that as a failure.
25. As a developer, I want doctor to warn but not fail when Graft is enabled with no application roots, so that I notice settings that have no effect.
26. As a developer, I want doctor to fail with a concrete fix when enabled Graft is missing, stale or mispinned, including disabling as one option, so that broken navigation never passes silently.
27. As a developer, I want verification to require the Graft check only when Graft is enabled and roots are configured, so that navigation gates match what is in use.
28. As an existing-installation owner who uses Graft, I want updates to keep navigation enabled, so that my working setup is untouched.
29. As an existing-installation owner who never used Graft, I want the update preview to propose disabling navigation and explain how to re-enable it, so that I shed an unused dependency knowingly.
30. As an existing-installation owner, I want that navigation change applied only with the approved update, so that nothing changes without my consent.
31. As a developer, I want the dependency status to show Graft as required only while navigation selects it, so that status agrees with configuration.
32. As a future maintainer, I want optional dependencies tied to a capability through one generic registry field, so that later optional capabilities need no special cases.
33. As a new developer, I want documentation to state that Node is a core prerequisite for skill installation and that Graft is optional, so that I install exactly what I need.
34. As a developer, I want the engineering guide to explain each navigation provider value and how to switch, so that I can choose without reading code.
35. As a developer, I want template contents, setup, doctor, dependency status, verification and documentation to agree about navigation optionality, so that no surface contradicts another.

## Implementation Decisions

- **Installation role**: a required `role` value (`maintainer` or `consumer`) in the committed per-installation install state, not in the manifest (the manifest is generated from the maintainer checkout and would leak `maintainer`). Generation and adoption write `consumer`; this repository commits `maintainer`. No default and no inference from path prefix, Make targets or template presence (ADR 0001).
- **Role migration**: an Engineering migration records `consumer` for existing consumer installations during update. Until recorded, verification planning fails with guidance to run the update.
- **Path categories**: verification planning derives each changed path's category from manifest ownership plus role:
  - project configuration → project checks plus `engineering-check`;
  - managed implementation in a consumer project → plan rejected with the supported update/upstream route; the outcome is INCOMPLETE;
  - maintainer source in the maintainer checkout (templates, managed implementation, maintainer tests and evals) → additionally `engineering-test` and `engineering-evals`;
  - other project paths → project checks, as today.
  Requirements are computed from role and ownership, never from which targets exist.
- **Project configuration ownership**: the Engineering configuration file moves from whole-file managed ownership to project-owned. Updates validate it and apply schema migrations but never overwrite values. The maintainer checkout's own copy is project configuration there too; the template copy is maintainer source.
- **Health checks target**: the existing managed Makefile integration section already supplies `engineering-check` (doctor plus maintainability) in generated and adopted projects; no new command.
- **Navigation setting**: disabling uses the existing navigation provider field with value `none`; no separate enabled flag. The template default becomes `none`.
- **Doctor navigation states**: `none` passes with an informational line; `graft` with roots and valid pins passes; `graft` with empty roots passes with a non-blocking warning and next step; `graft` with missing, stale or mispinned installation fails with fixes including setting `none`. Pin and launcher checks run only when Graft is selected.
- **Verification navigation rule**: unchanged in substance — the Graft check is required only when the provider is `graft` and application roots exist.
- **Dependency registry**: add a generic optional `capability` field. A dependency with a capability is required only while that capability's provider selects it; Graft gets `capability = "navigation"`. Dependency status, setup and doctor use this single rule.
- **Navigation-conditional managed content**: the Graft skill, the Graft launcher, the Graft package pins and the navigation guidance in agent policy are managed content present only while navigation selects Graft. Agent-policy navigation guidance becomes its own managed section. Update and generation select this content from the project configuration.
- **Enable/disable flow**: enabling = set provider to `graft`, then the existing dependency preview/apply installs the pinned package and the conditional content. Disabling = set provider to `none`, then an update whose preview lists the removals. The Graft index and application-root values are project data and are never removed.
- **Upgrade rule**: an update keeps `graft` when a Graft index exists or dependency state records Graft installed. Otherwise its preview proposes `graft → none` with re-enable instructions, applied only with the approved update.
- **Prerequisites**: Node remains a documented core prerequisite because upstream skill installation uses the `skills` npm installer. Graft's npm package is an optional-capability prerequisite. Node-free skill installation is future work.
- **Documentation**: the engineering guide explains the navigation provider values, enabling and disabling, and that Graft is optional; the generated README and onboarding reflect the `none` default and prerequisite split; verification documentation describes role-based requirements.
- **Delivery**: two tickets in order — A (role, categories, configuration ownership, migration) then C (navigation optionality). Each updates consumer generation, adoption/update behavior and documentation, not only the maintainer checkout.

## Testing Decisions

- One seam: the `./engineering` command line run against fixture repositories (a generated consumer project, an adopted project and a maintainer-checkout fixture). Tests assert exit status, reported categories/next steps and resulting files — not internal functions or exact prose.
- Template generation: a generated project records the consumer role, defaults navigation to `none` and contains no Graft launcher, skill, package pins or navigation guidance. Prior art: template tests.
- `verify prepare`: consumer configuration change plans with `make check` plus `engineering-check`; invalid configuration fails; consumer managed-implementation edit is rejected as INCOMPLETE with guidance; missing role blocks; maintainer source requires the maintainer suites; removing a maintainer target does not lower requirements; adopted and generated projects classify identically. Prior art: verification integration tests.
- `doctor`: disabled, ready, enabled-without-roots warning (non-failing) and enabled-but-broken states. Prior art: doctor tests and Graft integration tests.
- `update` preview/apply: role migration; project configuration values preserved across update and schema migration; managed-implementation edit reported as conflict; `graft → none` proposed only without Graft evidence and applied only on approval; disabling removes conditional content but keeps the index and roots. Prior art: installation tests.
- `deps` plan/install: Graft required only while navigation selects it; enabling installs the pinned version. Prior art: dependency tests.
- Starter tooling changes also run the maintainer test and eval suites; add or adjust policy evals where agent-policy navigation guidance changes.

## Out of Scope

- Review tiers (B), adoption compatibility preview (D), evidence freshness performance (E) and review explanations (F).
- Node-free skill installation.
- Supporting symlinks, submodules or additional languages.
- Changing the Graft integration itself beyond making it optional.
- Live user journeys, authenticated agent runs, real remote publication or full project builds as acceptance gates.
- Replacing or patching pinned upstream skills.

## Further Notes

- The maintainer checkout currently has an install state and manifest like a consumer's, with an empty manifest project field; the role must be added explicitly to this repository's install state as part of ticket A.
- Unrecorded role is intentionally a blocker, not a default, to prevent silent downgrade of maintainer verification.
- The upgrade rule deliberately refines the intent's "preserve explicit selection": existing `graft` values came from the template default, so evidence of use stands in for explicit choice, and any change is visible and approved.
