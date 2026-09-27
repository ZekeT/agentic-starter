# Engineering v3.1c — starter refinement

Status: intent settled by grilling 2026-09-27; ready for `/to-spec` (slices A and C only)

A focused refinement of the current Engineering System, not a redesign. Keep
the v3 ownership split: Engineering System owns invariants, checks, migration,
updates and verification; upstream Matt skills own workflow; Graft owns derived
code knowledge.

Terms follow [product context](../../docs/context/product.md). The installation
role decision is [ADR 0001](../../docs/adr/0001-explicit-installation-role.md).

## Intent

Make the starter quick to start and to adopt, keeping `/implement → /review →
/ship` and its safeguards while cutting compulsory setup dependencies,
disproportionate review handoffs and repeated repository work. Small work needs
little ceremony; substantial work arrives with evidence and an explanation a
CS/data-science reader can review without reading every line.

## Scope

Six independently reviewable slices, one PR each, in this order:

1. **A** — consumer versus maintainer verification (confirmed defect)
2. **C** — optional navigation and accurate prerequisites
3. **B** — review tiers scaled to change risk
4. **D** — adoption compatibility preview
5. **E** — cheaper evidence freshness checks
6. **F** — human-readable review explanation for substantial changes

Specify and ticket **A and C now**. B, D, E and F stay ideas until their own
grilling session; B waits for C because optional navigation affects which checks
tiers must require.

## A. Consumer versus maintainer verification

Defect: `verification_snapshot.validate_plan` requires `make engineering-test`
and `make engineering-evals` for any changed path under `.engineering/`.
Consumer projects lack those targets, so editing `.engineering/config.toml` — as
onboarding instructs — creates an impossible verification requirement.

Settled decisions:

- Each installation records its **installation role** (`maintainer` or
  `consumer`) in `.engineering/state/install.json`. Generation and adoption write
  `consumer`; this repository commits `maintainer`.
- A missing role blocks verification with an actionable message. A migration
  records the role for existing installations. No default, no inference from
  path prefix, Make targets or template presence (see ADR 0001).
- Per-path category comes from manifest ownership:
  - **Project configuration** — `.engineering/config.toml` changes from
    `file` ownership to project-owned: the starter validates and migrates its
    schema on update but never overwrites values. Required checks: `make check`
    plus `make engineering-check` (doctor + maintainability). The Makefile
    `integration` section already supplies `engineering-check` in generated and
    adopted projects.
  - **Managed implementation** edited in a consumer project — the verification
    plan is rejected with the supported route (update the starter or contribute
    upstream); the result is INCOMPLETE, never PASS. Updates separately report
    the edit as a conflict.
  - **Maintainer source** in the maintainer checkout — `.engineering/template/**`,
    managed implementation, maintainer tests and evals — still requires the
    maintainer suites. The checkout's own `.engineering/config.toml` is its
    project configuration, not maintainer source.

Acceptance criteria:

- A consumer project changes `application_roots` or maintainability settings and
  prepares a valid verification plan without nonexistent targets.
- Invalid configuration still fails visibly.
- Maintainer source changes still require the maintainer suites; removing a
  target or the role cannot downgrade them.
- Generated and adopted consumer projects classify identically.
- A consumer edit to managed implementation is rejected with guidance.

Starting points: `verification_snapshot.py`, `ownership.py`, `installation.py`,
`.engineering/state/install.json`, manifest generation, migrations,
`.engineering/template/Makefile`, template tests.

## C. Optional navigation

Settled decisions:

- Navigation is disabled with `[navigation] provider = "none"` (existing
  field; no separate `enabled` flag). New consumer projects default to `none`.
- Doctor states:
  - `none` — disabled, passes; ordinary search and source reading are the
    navigation method.
  - `graft`, ready, with roots — passes.
  - `graft` with empty `application_roots` — passes with a non-blocking warning
    and next step (add roots or set `provider = "none"`), so settings are not
    silently ineffective.
  - `graft` enabled but missing/stale/mispinned — fails with an actionable fix,
    including disabling as an option. Never falls back to PASS.
- Verification requires `.engineering/bin/graft check` only when the provider is
  `graft` and roots exist (current root rule retained).
- Upgrade of existing installations: keep `graft` when the project shows use —
  a Graft index exists or dependency state records Graft installed. Otherwise
  the update preview shows `navigation: graft → none` with how to re-enable, and
  it applies only with the approved update. Never silent.
- Navigation-conditional managed content, present only while enabled: the
  `graft` skill, `.engineering/bin/graft`, `.engineering/graft/package*.json`,
  and the navigation guidance in `CLAUDE.md` as its own managed section. When
  disabled, agent policy says nothing about Graft.
- Enabling goes through the existing dependency preview/apply flow. Disabling is
  a configuration edit then an update whose preview shows the removals. The
  Graft index and `application_roots` values are project data and are kept.
- Dependency registry gains a generic `capability = "navigation"` field: such a
  dependency is required only while its capability's provider selects it. No
  Graft-specific special cases.
- Node stays a documented **core** prerequisite because upstream skill
  installation runs `npx skills@…`. Graft's npm dependency is a separate
  optional-capability prerequisite. Do not claim a Node-free core.
- `ENGINEERING.md` explains the navigation field: what each value does, how to
  enable or disable, and that Graft is optional — many developers will not
  want it.

Acceptance criteria:

- A new consumer project with navigation `none` sets up and runs the normal
  workflow without Graft installed.
- Doctor distinguishes disabled, enabled-and-ready, enabled-without-roots
  (warning) and enabled-but-broken.
- Enabling installs and validates the pinned Graft through the dependency flow.
- Disabling removes gate obligations and conditional managed content without
  deleting project data.
- Upgrade follows the evidence rule above and shows any change in its preview.
- Dependency status, template contents, setup, verification and documentation
  agree about optionality and prerequisites.

Starting points: `dependencies.toml`, `deps.py`, `registry.py`, `doctor.py`,
`graft.py`, `verification_inputs.py`, `settings.py`, `updates.py`, setup,
`CLAUDE.md` sections, template `files.json`, generated README, `ENGINEERING.md`.

## Future improvement (not in this initiative)

Node-free core: replace the `npx skills` installer with a pinned Git checkout
and copy. Unproven whether Node can be avoided entirely; investigate before
scoping.

## Deferred slices — open questions for their own sessions

- **B. Review tiers** (documentation-only / ordinary / sensitive): which
  deterministic checks form the documentation tier and how existing evidence
  migrates; when one fresh reviewer may cover behavior and maintainability;
  classification by semantic impact (agent-policy Markdown is not low risk);
  storing tier, reason, checks and reviewer coverage in evidence; shipping
  reuses compatible evidence.
- **D. Adoption compatibility preview**: extend adoption's existing read-only
  plan to report project checks, runtime prerequisites, unsupported repository
  constructs (symlinks, submodules, unmerged entries), policy conflicts,
  language coverage gaps and migration route; propose a `make check` wrapper
  only from a clearly declared native command; blockers versus warnings.
- **E. Evidence freshness cost**: measure first with small and large synthetic
  repositories; reuse validated prepared checkouts safely; never HEAD-only
  freshness; missing/corrupt prepared state rebuilds or reports INCOMPLETE; no
  background service or database.
- **F. Review explanation**: part of the existing review handoff; behavior and
  reason, optional small Mermaid diagram, entry points and I/O, files to read in
  order, checks and remaining uncertainty; trivial changes get short prose; no
  new command, knowledge store or compulsory show-me.

## Validation

Targeted regression and command-level fixture tests only. No live user journey,
authenticated agent runs, real remote publication or full project build as a
per-change gate. Key scenarios for A and C: consumer config change verifies;
maintainer changes still need maintainer suites; missing role blocks; consumer
managed-implementation edit rejected; navigation none versus enabled-ready
versus enabled-without-roots versus enabled-broken; upgrade with and without
Graft evidence.
