# Engineering System

## What this system is

Agentic Starter provides repository-level engineering support:

```text
Engineering System =
  Instructions + Constraints + Verification + Navigation
  + Dependency Management + Migration + Runtime Integration
```

It owns deterministic checks, maintainability constraints, security safeguards,
independent verification, human shipping policy, safe installation and updates.
Matt Pocock's upstream skills own development workflows. Graft owns derived
code structure. Repository policy continues to apply regardless of how work was
planned. Changing a skill's internal method should require little or no starter
code change; Graft's internal graph format is not our architecture database.

The standard stack is **Matt + Graft + optional show-me + Karpathy principles +
the Engineering System**. Selected Pstack principles (subtract before adding,
reduce reader load, respect boundaries, model the domain, use verifiable units,
and encode lessons in structure) are useful reference material. No Pstack
workflow package is installed.

## Onboarding

Use a separate checkout of the Engineering source repository for generation,
adoption and migration. A generated application is the consumer payload, not a
copy of this repository's development history. Install Git, Python 3.12+, uv and
Node.js 22.12+ with npm through your normal toolchain management first.

### New application

From the Engineering source checkout, run `make template DEST=/absolute/new-app`.
The parent must exist and the destination must not exist. In the generated directory:

```bash
git init -b main
make setup
git add .
git commit -m "Initialize application"
make check
./engineering doctor
```

Setup explicitly installs pinned dependencies over the network and initializes
missing installation state after verifying distribution bytes. Repeating setup
preserves the baseline. Application code, tests, README and project metadata are
yours; ordinary edits never need `make manifest`. The generated README is the
application's starting guide. Remote template publication is not provided.

### Existing project without Engineering

Start with a clean, committed project and a working project-native `make check`.
Keep its language, package manager, CI and application checks. From the external
Engineering source checkout:

```bash
./engineering adopt /absolute/existing-project
./engineering adopt /absolute/existing-project --apply
```

The first command previews exact actions without writes. Inspect the plan and
resolve conflicts before applying. Adoption adds managed regions around shared
files and preserves project-owned content; it does not replace native tooling
with the Python template. If OpenSpec is detected, its sources and integration
remain until the separate semantic migration below.

In the target project, install managed tools explicitly, then verify:

```bash
./engineering deps install --apply
./engineering doctor
make check
make engineering-check
```

Install the target's own development dependencies with its existing package
manager before running its native check. Inspect the resulting diff and record
it in Git before another adoption/update/migration operation requiring clean Git.
Do not copy the maintainer checkout over an existing project.

### Earlier Agentic Starter

Use the external Engineering source checkout against a clean, committed target:

```bash
./engineering migrate legacy-starter --target /absolute/legacy-project --plan
./engineering migrate legacy-starter --target /absolute/legacy-project --apply
```

Review the preview before apply. Resolve customized managed-file conflicts rather
than forcing replacement. Inspect preserved custom policy under
`.engineering/migrations/legacy-docs/`. Upgrade changes infrastructure; OpenSpec
sources, commands and hooks stay available pending semantic reconciliation.
Install managed dependencies and run the target's native and Engineering checks
as in adoption above. Review and commit the infrastructure change before preparing
the final OpenSpec inventory.

### OpenSpec project

This works for arbitrary OpenSpec repositories, including ones that never used
Agentic Starter. Use an external Engineering source checkout; fresh consumer
applications intentionally contain no migration implementation or migration skill.
If Engineering is absent, first adopt it and install its dependencies as above.
For earlier starters, perform the infrastructure upgrade first. Preserve the
project's native check and commit the reviewed infrastructure changes.

```bash
./engineering migrate openspec-project --target /absolute/project --plan
./engineering migrate openspec-project --target /absolute/project --apply
```

The preview writes nothing. Apply prepares temporary inventory and indexes only;
source and integration remain intact. In an agent session with access to both
checkouts, use the external source checkout's
`.claude/skills/migrate-from-openspec/SKILL.md` against the target. It compares prose,
code and tests, stages exact durable-document proposals and remaining-work
handoffs, and asks the owner to resolve conflicts. A task checkbox does not prove
implementation, and a prepared inventory does not complete migration.

Review the complete finalization diff and digest before authorizing apply. After
successful validation, explicitly accept the outputs; then review and authorize
cleanup or retention. Follow the commands and safeguards in
[OpenSpec finalization and closure](#openspec-projects-and-earlier-starters).
Pending cleanup does not block ordinary development. Do not run acceptance or
removal commands merely because inventory preparation succeeded.

### Configure your first change

Read `CLAUDE.md` for shared policy. Set `[navigation].application_roots` in
`.engineering/config.toml` to actual application directories; never point Graft
at all repository tooling. Empty means no application graph is needed. Build and
check an applicable graph explicitly before verification.

Local Markdown is the default tracker regardless of hosting provider. Existing
projects retain their configured tracker. Read `docs/agents/issue-tracker.md`;
keep durable specs and tickets in Git. Run `engineering deps status`. Claude Code
discovers project skills; other runtimes can read their `SKILL.md` files directly.
Choose a branch before `/implement` or `/tdd`, then follow the review and shipping
policy below. Optional show-me installs only when explicitly requested:
`engineering deps install show-me --apply`.

## Mental model

| Layer | Responsibility |
|---|---|
| Decide | Matt: grill-with-docs, wayfinder, research, prototype, to-spec, to-tickets |
| Understand code | Graft: map, skeleton, callers, grep, ask, blast radius |
| Build | Matt: implement, tdd, diagnosing-bugs, code-review; repository constraints apply |
| Prove | Targeted tests, formatting, full deterministic gate, fresh reviewers, human review |
| Understand as a human | show-me for focused diagrams, code sketches and ephemeral explanations |

Karpathy principles are summarized in the root instructions: surface material
assumptions, prefer the minimum sufficient design, make surgical changes,
respect boundaries and express success as verifiable outcomes. The optional
upstream skill is installed explicitly with
`engineering deps install karpathy-guidelines --apply`.

## Which skill do I use?

| Situation | Use |
|---|---|
| I do not yet know what I want | `/grill-with-docs` |
| Large architectural uncertainty | `/wayfinder` |
| Need external evidence | `/research` |
| Need to test a design hypothesis cheaply | `/prototype` |
| Decisions settled; work spans sessions | `/to-spec` |
| Need execution-sized vertical slices | `/to-tickets` |
| Ready to build | `/implement` |
| One behavior test-first | `/tdd` |
| Hard bug | `/diagnosing-bugs` |
| Review implementation quality | `/code-review` |
| Need codebase navigation | Graft |
| Need a readable explanation | `/show-me` |
| Inspect a planning map | Matt's configured tracker |
| Final repository checks | `make check` |
| Installation diagnosis | `engineering doctor` |

## Workflow examples

These are examples, not persisted states or mandatory classifications.

**Obvious small change:** request → `/implement` or `/tdd` → `make fmt` →
independent verification → human review → authorized shipping. A clear,
one-session change needs no spec ceremony.

**Feature needing discussion:** `/grill-with-docs` → `/implement` → verification
→ review → shipping. Discussion resolves the unknowns before coding.

**Multi-session feature:** `/grill-with-docs` → `/to-spec` → `/to-tickets` →
`/implement` one ticket per fresh session → verification → review → shipping.
The spec carries settled decisions across sessions; tickets bound execution.

**Large uncertain coding work:** `/wayfinder` → inspect through the configured
tracker → resolve research/prototype/grilling tickets → `/to-spec` →
`/to-tickets` → `/implement`. The completed map hands off to a spec. Wayfinder
is not the entire coding-to-shipping lifecycle. Matt owns the method and its
tracker contract; the starter neither parses ticket state nor routes tasks.

**Hard bug:** `/diagnosing-bugs` → regression test → fix → verification → review.
Use evidence to isolate the fault before changing unrelated code.

Create or switch to the intended branch **before `/implement`**. Ordinary
`feat/`, `fix/`, `chore/`, and `docs/` branches are sufficient. Worktrees are
optional developer tools; branch names are not a workflow database.

## Context boundaries and verification

Prefer fresh context between wayfinding, settled specs/tickets, each
implementation ticket, maintainability review, and behavioral verification.
The implementer's hidden reasoning and self-review narrative must never be
passed to the verifier. Reviewers receive only a branch/ticket/spec/request
pointer and reconstruct requirements, diff, source and test evidence themselves.

```text
implement → targeted tests → make fmt
          → graft build / graft check (when application roots exist)
          → fresh maintainability reviewer (read-only: PASS / CONCERNS)
          → fresh verifier (read-only: PASS / FAIL; runs make check)
          → conditional security reviewer → human review → authorized ship
```

Use [REVIEW.md](REVIEW.md) for human review. Security review applies to auth,
secrets, cryptography, untrusted input, payments, privilege boundaries,
destructive operations, sensitive storage, network exposure and dependency
execution. It is unnecessary for a trivial prose change.

`/implement` authorizes scoped local commits, not acceptance or publication.
After implementation, automatically hand off to fresh independent reviewers when
supported by the runtime. Pinned upstream skills stay unchanged; their committed-only
review does not prove coverage of uncommitted work. When fresh execution is
unavailable, give an explicit fresh-session handoff; never self-certify.

`/review` obtains missing/stale independent verification, then summarizes scope,
evidence and risks. Current proof is reused across sessions using the local
`engineering verify` commands described in
[verification evidence](.engineering/docs/verification.md). Records cover actual
content and check inputs rather than just HEAD. Ordinary application commits do
not carry this bookkeeping. After completed acceptance review, `/ship` accepts
the unchanged presented scope and authorizes remaining scoped commits, push and
actual PR/MR creation. It reuses current proof without duplicate checks and honors
narrower requests; merge/force-push remain separate. See
[publication](.engineering/docs/publication.md) for preflight and provider setup.
After a transport failure, restore connectivity and rerun `engineering publish
run --change <change>`: it retains scoped authorization, checks actual remote and
provider state, and reuses completed commits/pushes/PRs and unchanged verification.
GitHub is optional. Invocation of `/implement` does not authorize pushes or PRs.

## Review corrections

`/review` explains findings with evidence and waits for your fix instructions.
Ordinary corrections need no new planning cycle and may remain uncommitted.
Fresh reviewers inspect the correction and affected behavior, justify retained
evidence for unchanged areas, and rerun authoritative checks after code fixes.
The updated scope comes back for acceptance. Preference-only alternatives are
non-blocking. After two unsuccessful attempts at a finding, or before undoing a
settled decision, pause for focused `/grill-me` and record the agreed resolution.
Material expansion returns to `/to-spec` and `/to-tickets`. See [REVIEW.md](REVIEW.md).

## Deterministic checks

| Command | Purpose |
|---|---|
| `make fmt` | Mutating formatting/import fixes |
| `make lint` | Read-only formatting, lint and type checks |
| `make test` | Product tests |
| `make check` | Product formatting/lint/types/tests, doctor, maintainability, feature docs |
| `make engineering-test` | Starter Python/script/update/migration tests, lint and types |
| `make engineering-evals` | Static integration checks |
| `make engineering-evals-full` | Optional authenticated prompt evals; costs model tokens |
| `make engineering-check` | Offline installation and maintainability checks |
| `make manifest` | Starter-maintainer distribution fingerprints; never repair a customized installation with this |
| `make template DEST=/path/to/new-project` | Maintainer-only deterministic consumer directory build |

`make check` does not mutate source, fetch dependencies, update pins, build a
Graft graph or invoke a model. Test/cache files may be produced. Run setup first;
ordinary gates use offline uv with Python downloads disabled.
Adopted projects keep their own `make check`; run `make engineering-check`
alongside it. Their application environment, package manager and CI stay theirs.
The starter's Python application targets are a template, not an adoption rule.
`engineering-test`, `engineering-evals`, `manifest` and `template` are maintainer targets in the starter checkout;
run the self-tests there before distributing an update to adopted projects.
Generated consumer Makefiles omit these targets. The shared `engineering-check`
runs doctor and maintainability without the upstream eval suite, including after
adoption and legacy upgrade. Maintainers run `engineering-evals` explicitly.

## Build a clean application template

In an Engineering maintainer checkout, run
`make template DEST=/path/to/new-project`. The parent must exist and the destination
must not exist. The build is offline, creates no Git history and never overwrites
an existing directory. In the output, run `git init -b main`, `make setup`, and
commit the initialized project before running `make check`. For another default
branch, configure `git config engineering.baseBranch <branch>`.

`.engineering/template/files.json` is the authoritative positive payload inclusion
list: exact destination/source mappings separate managed runtime from application
seed files. Consumer README, Makefile and configuration inputs live beside it.
Review additions explicitly; merely tracking a file never ships it. The builder
reuses the distribution fingerprint generator for the selected managed files and
validates the resulting manifest. That generated manifest describes update
ownership; it is distinct from the maintainer's packaging inclusion list.

The payload excludes migration implementations, migration skills and legacy
baselines. Run brownfield migration from a separate Engineering checkout; existing
installations are not automatically stripped of their migration files. It also
excludes upstream tracker artifacts,
maintainer tests/evals/build scripts, historical project documentation, caches,
installed dependency outputs and populated installation/migration state.
Downstream `.scratch/` tickets remain trackable. Application README, project
metadata and lockfile are seed content outside Engineering update ownership.
Application edits and project-owned portions of shared files pass ordinary gates
without `make manifest` or fingerprint repair. Setup verifies distribution bytes
before first initialization; later setup preserves the installation baseline.
Maintainers retain distribution integrity checks and migration runtime in the
Engineering checkout. External OpenSpec migration defaults to `git-only` for
projects without a migration policy.

Repeated builds of identical inputs produce identical file bytes and executable
modes. Build from reviewed source; run the maintainer's required checks and review
before distributing it. This command does not publish a remote template branch.

Maintainability checks count Python code lines: warn above 300, maximum 500,
substantial growth 150. A new oversized module fails; existing oversized modules
fail on substantial growth. Other source languages are reported as unanalyzed.
Use reviewed exact-path exceptions in `[maintainability]`, not inline bypasses.
See [.engineering/docs/maintainability.md](.engineering/docs/maintainability.md).

## Graft navigation

Graft is pinned and installed in `.engineering/graft/`. Its launcher confines
navigation to application roots, avoids implicit refreshes and keeps optional
model enrichment out of normal gates. Preserve its package lock.

```bash
.engineering/bin/graft build
.engineering/bin/graft check
.engineering/bin/graft map
.engineering/bin/graft skeleton src/service.py
.engineering/bin/graft callers handle_request
.engineering/bin/graft grep handle_request
.engineering/bin/graft ask handle_request --source
.engineering/bin/graft blast --base main
```

`build` is explicit implementer-owned structural preparation. Reviewers never
rebuild. Optional `build --deep` may use configured model credentials and is not
required. Graph freshness is assessed separately from installation health.
No configured application roots reports NOT APPLICABLE. Do not write a custom
symbol graph, call-map database or manually maintained current file map.

## Dependency ownership and updates

`.engineering/dependencies.toml` is desired state. Required: Matt skills and
Graft. Optional: show-me and Karpathy. No full Pstack or Wayfinder Maps package is
managed. Git skills use immutable commits; npm packages and the skills installer
use exact versions. `.engineering/state/dependencies.json` records installed
pins and output hashes separately and is local installation bookkeeping.

```bash
engineering deps status                         # offline comparison
engineering deps plan                          # no writes, no network
engineering deps install                       # preview missing required tools
engineering deps install --apply               # explicit network/install
engineering deps install show-me --apply        # explicit optional choice
engineering deps update                        # plan current installed-vs-desired pins
engineering deps update matt-skills --check-remote  # explicit network discovery
engineering deps update matt-skills --ref <full-commit-sha>
engineering deps update matt-skills --ref <full-commit-sha> --apply
```

Updates never silently select latest. Review the proposed pin and apply it
explicitly. Skills are staged with the pinned upstream skills installer and
installed unchanged into project-local skill directories. Local modifications
cause conflicts, not silent replacement. Global installations are untouched.
After updating, run doctor, starter self-tests in the starter checkout and the
static evals; authenticated prompt evals remain optional. Failed installation
leaves recorded dependency state unchanged; ordinary file-write errors roll back.
A process kill/power loss still requires inspecting Git status and install state.

## System installation, adoption and update

System updates change starter-owned instructions, scripts and adapters.
Dependency updates change upstream capabilities. System updates never change
existing dependency pins, package locks or installed skills.

From a v3 starter checkout:

```bash
engineering adopt /path/to/project
engineering adopt /path/to/project --apply
engineering update /path/to/project
engineering update /path/to/project --apply
```

Plans inspect build-system evidence, Git, existing checks/instructions/settings
and CI without executing target scripts. Define a project-native `make check`
first if absent; adoption will not invent an application gate. Non-Python
projects are supported when they expose that check.

Apply requires a clean committed target repository, unchanged inspected inputs,
and zero conflicts. There is no force flag. Shared instruction/Makefile/ignore
regions and the recognized JSON hook subset preserve surrounding project data.
The manifest and installed baseline distinguish new, unchanged, local-only,
upstream-only, conflicting and safely removable scopes. A removed customized
scope conflicts. Unresolved conflicts never advance metadata. Configuration
schema changes require explicit migration rather than guessing.

After adoption install required dependencies and run doctor and both project
and engineering checks. Doctor validates structure during apply; missing
managed dependencies remain a separate explicit setup step.

## Doctor and diagnostics

`engineering version` prints `.engineering/TEMPLATE_VERSION` for migration and
support diagnostics without checking installation health.

`engineering doctor` is offline. It checks repository protections, Python,
required files, executable launchers, policy, tracker pointers, hook wiring,
reviewer definitions, Graft pin wiring, dependency evidence and installation-state
schemas. Migration receipts are validated by migration commands, not ordinary
development gates. It does not inspect tickets, run tests, contact remotes, assess graph
freshness or ask for credentials. Optional missing skills warn.

Exit codes: 0 healthy, 1 configuration/installation failure, 2 invalid CLI usage.
Errors include stable categories, affected paths and remediation. Restore or
reconcile affected scopes; never overwrite customization merely to silence a
health check. Unknown schemas fail closed.

## OpenSpec projects and earlier starters

Use an external Engineering System checkout against any OpenSpec repository,
including projects that never used Agentic Starter:

```bash
./engineering migrate openspec-project --target /path/to/project
./engineering migrate openspec-project --target /path/to/project --plan
./engineering migrate openspec-project --target /path/to/project --apply
```

The default and `--plan` are non-mutating previews. `--apply` requires a clean,
committed Git repository and prepares only temporary evidence under
`.engineering/migration-work/openspec/`. It preserves all OpenSpec source,
commands, configuration, project documentation and application code.
`engineering migrate openspec` is a deprecated alias with the same safe behavior.

The workspace contains `inventory.json`, canonical/active/archived source indexes,
`detected-integrations.md`, and a `reconciliation/` directory. Inventory records
source paths and SHA-256 fingerprints, the source commit, local/remote branch
references, metadata, existing durable docs and detected integration. It does not
infer code/test relationships or classify requirements from task checkboxes.

The migration sequence is inventory → `/migrate-from-openspec` semantic
reconciliation → human review → approved finalization. Reconciliation must compare
prose with code and tests, resolve conflicts with the human, and route remaining
work into Matt's skills. Preparation alone does not complete migration or approve
removals. No durable replacement docs are created mechanically.

The project-owned skill is `.claude/skills/migrate-from-openspec/SKILL.md`; runtimes
without slash-command discovery can read it directly. It stages a readable
`reconciliation/plan.md` and exact proposed changes in
`reconciliation/application.json`, using the linked versioned contract. Review
the evidence, classifications, remaining-work handoffs, complete diff and manifest
digest. Conflicts require human answers; unresolved design may be handed to
Wayfinder only with explicit acceptance of that deferral. Staging changes neither
applies them nor approves removal. Preview the complete readable plan, file diffs and manifest SHA-256 with:

```bash
./engineering migrate openspec-project --target /path/to/project --finalize --plan
```

After the human accepts those exact bytes, apply with `--finalize --apply`.
Neither preview nor a generated approval field authorizes removal. Finalization
uses the inventory's history policy; changing it requires a new inventory/review.
The target must already have Engineering installed, required dependencies available,
and its native `make check`. Prepare applicable Graft graphs explicitly beforehand.

Finalization requires current `reviewed_head`, unchanged inventory/source/evidence,
exact destination hashes and clean Git. Keep temporary review artifacts ignored
(the starter ignores `.engineering/migration-work/`); on arbitrary projects,
configure that exclusion before preparing the final review. Do not force-add the
manifest: committing a manifest that embeds `reviewed_head` changes that HEAD.
Shared integration files receive exact reviewed replacements, never whole-file
deletion. All inventoried OpenSpec files and runtime wiring require explicit removal.

Apply runs offline doctor, the native `make check`, and Graft check (not applicable
when application roots are empty). It does not build graphs or install dependencies.
Ordinary write or validation failure restores affected file bytes/modes, prints the
failure and recovery commit, and creates no success receipt. Project checks are
project-owned executable code: inspect their output/status for any additional
artifacts they create; the transaction only restores its own affected files.
A process kill or power loss still requires manual recovery inspection.

Successful validation writes a temporary `validation.json` with the recovery
commit, exact output/evidence fingerprints and gate results. Exact retries make
no changes, including before committing; changed outputs or reappeared OpenSpec
files conflict. A repeat acknowledges the original checks, not a fresh validation
of subsequent development. Changes remain uncommitted for human review. Validation alone is not human acceptance. After the human accepts these validated
outputs, record it explicitly:

```bash
./engineering migrate openspec-project --target /path/to/project --accept --apply
./engineering migrate openspec-project --target /path/to/project --cleanup --plan
```

**Migration accepted** means validation passed and the human accepted the outputs.
The handoff now says **cleanup pending**; ordinary development may continue.
**Migration closed** means the temporary workspace files were removed or explicitly
retained by the human. Cleanup is bounded to `.engineering/migration-work/openspec/`.
The preview lists every file, fingerprint and mode with REMOVE or RETAIN. Use
repeatable workspace-relative `--retain <file-or-directory>` selections, such as
`--retain snapshot`; `--retain .` explicitly retains all artifacts. Repeat those
choices when applying the exact human-approved cleanup digest:

```bash
./engineering migrate openspec-project --target /path/to/project --cleanup --plan --retain snapshot
./engineering migrate openspec-project --target /path/to/project --cleanup --apply --retain snapshot --approved-cleanup <SHA-256>
```

Omit `--retain snapshot` when no snapshot exists or none is requested. The preview
is not removal authorization: obtain human approval before applying its digest.
Changed/new artifacts are never silently deleted; explicitly retain them after
review. Missing artifacts conflict; restore them before retrying. Ordinary write
failure rolls back cleanup, and exact retries are read-only acknowledgements.
Post-acceptance application development does not invalidate temporary cleanup;
this acknowledges the original migration acceptance, not validation of new work.

The small local `.engineering/migration-work/openspec-closure.json` record is kept
outside the cleanup scope for acceptance and retry reporting. The preview discloses
it; it is optional bookkeeping, not a permanent migration service. Removing it
manually loses automatic retry recognition and does not affect normal development.
No normal project gate depends on migration evidence, acceptance or cleanup records.

Git history is the default preservation policy for an unconfigured project.
An explicit `[migration] legacy_history` setting or `--legacy-history` selection
is honored. `--legacy-history snapshot` additionally copies inventoried sources
into the temporary workspace. Preparation records whether sources match HEAD;
later removal must verify preservation against the recorded commit.

Identical retries create no duplicate outputs, including after committing the
workspace. Changed sources or edited evidence produce conflicts rather than
overwriting review work. Review and remove obsolete temporary evidence explicitly
before preparing a new inventory. The workspace may be removed after successful
final validation and human acceptance; normal development never depends on it.

For an earlier Agentic Starter installation:

```bash
./engineering migrate legacy-starter --target /path/to/project --plan
./engineering migrate legacy-starter --target /path/to/project --apply
```

This upgrades known infrastructure and ownership metadata while preserving
OpenSpec pending semantic reconciliation. It advertises the separate OpenSpec
handoff. Explicit OpenSpec instruction blocks, commands, skills and project hooks
remain. A Makefile conversion that would discard OpenSpec integration conflicts
before writes so the owner can reconcile the shared file. Unknown project files
and global installations remain untouched. Customized legacy root docs are saved
under `.engineering/migrations/legacy-docs/` for manual review.

`engineering adopt` remains ordinary-project installation. When it detects
OpenSpec it recommends `engineering migrate openspec-project` and preserves the
existing workflow sources.

On dirty Git, commit or stash user work and retry. On conflicts, reconcile the
named paths and re-plan. Symlinks and unsafe paths are refused. Ordinary write
failures restore affected bytes and modes; the report identifies the recovery
commit. After infrastructure migration, install dependencies, run doctor and
project checks, then obtain review before committing.

## Durable knowledge and human explanations

| Information | Home |
|---|---|
| Product/domain context code cannot express | `docs/context/` |
| Architectural WHY and alternatives | `docs/adr/` |
| Decisions for work and execution slices | Matt's configured tracker |
| Stable feature interfaces/invariants/gotchas | Local feature instructions / `docs/features/` |
| Executable behavior | Tests and code |
| Current symbols, callers and blast radius | Graft-derived state |
| Temporary visual explanation | show-me; normally uncommitted |

Ask show-me to explain a design before implementation, a request flow, module
boundaries or a diff. Persist WHY that remains useful months from now; generate
current structure on demand. No prose file must mirror every application behavior.

## What should I avoid?

Do not create OpenSpec changes, restore a second Superpowers workflow, invent
FAST/STANDARD/DEEP tiers, require specs for tiny fixes, use Wayfinder for obvious
one-session work, or maintain a custom call-map document duplicating Graft.
Do not pass implementation reasoning to reviewers or silently overwrite local
customizations. Do not conflate installation bookkeeping with workflow state.

## Optional ecosystem alternatives

[Wayfinder Maps](https://github.com/rengwu/wayfinder-maps) is an external alternative
with a different local tracker contract. It is not installed, version-managed,
or required by this system. Do not assume it visualizes Matt's local artifacts.

The Engineering System MUST NOT maintain a `.scratch/` ↔ `.plan/` translator,
dual-write Wayfinder artifacts, patch Matt's skills to emit Wayfinder Maps format,
or treat the two local tracker contracts as interchangeable.

## Runtime portability and upstream references

`CLAUDE.md` is the single policy source; `AGENTS.md` directs other agents to it.
The Python core and Git safety rules do not depend on Claude. `.claude/` holds
Claude-specific hooks, reviewer definitions and thin review/ship commands.
Other runtimes must honor the same policy; Claude hooks do not automatically
run in them. Upstream skill installation mechanics may vary by runtime.

- [Matt Pocock skills and setup](https://github.com/mattpocock/skills)
- [Graft](https://github.com/trailhq/Graft)
- [HumanLayer show-me](https://github.com/humanlayer/skills)
- [Karpathy guidelines](https://github.com/multica-ai/andrej-karpathy-skills)
