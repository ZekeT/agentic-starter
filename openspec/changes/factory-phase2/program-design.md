# Program Design

Architecture: accepted `design.md`. The user accepted this program design and
`tasks.md` on 2026-09-10 and authorized group 1 implementation. Implementation
completion is recorded only by verified task claims in `tasks.md`.

## Code Shape

### Existing modules reused

- `.harness/scripts/lib/change.sh`: canonical base resolution and merge-base
  semantics; invoke through an argument-safe subprocess, not interpolated shell.
- `.harness/scripts/lib/run_quiet.sh`: concise successful full-gate output and
  complete failure output.
- `.harness/scripts/generate_template_manifest.py`: retain inventory discovery,
  version source, and hash-history behavior; delegate metadata validation and
  ownership extraction to the shared engine when introduced.
- `.harness/evals/run_evals.py`: retain static/prompt case discovery and reporting.
- Existing migration/update inspection and Git preflight behavior: move useful
  behavior into cohesive lifecycle modules, preserving supported CLI contracts
  through adapters and testing documented intentional changes.

### New modules

All Python runtime modules live in `.harness/factory/`, imported by a thin root
`factory` launcher. This is an ordinary package, not an application under src.

| Module | Responsibility | Intended public surface |
|---|---|---|
| `cli.py` | Argument parsing, root selection, dispatch, exit codes | `main(argv) -> int` |
| `config.py` | Manifest schema, defaults, project overrides and validation | `load_config(root)`, `validate_config(root, data)` |
| `source.py` | Safe repository source inventory and Python code-line counting | `discover_sources(root)`, `count_python(source) -> LineCounts` |
| `growth.py` | Merge-base comparison, rename mapping, threshold decisions | `check_growth(root, config, base) -> list[GrowthFinding]` |
| `graft.py` | Thin pinned-CLI invocation and non-mutating freshness diagnostics; no source analysis | `run(root, args)`, `application_roots(root)`, `install_skill(root, apply=...)` |
| `doctor.py` | Independent installation checks and remediation | `diagnose(root) -> list[Diagnostic]` |
| `ownership.py` | Managed paths, section extraction and structural JSON rules | `validate_ownership(...)`, `owned_content(...)`, `merge_owned(...)` |
| `installation.py` | Versioned baseline state, fingerprint validation | `load_state(root)`, `build_state(...)` |
| `inspection.py` | Conservative target tool/instruction/structure discovery | `inspect_target(root) -> Inspection` |
| `adoption.py` | Inspection and ownership into read-only adoption actions | `plan_adoption(template, target) -> Plan` |
| `updates.py` | Baseline comparison and legacy conversion into update actions | `plan_update(template, target) -> Plan` |
| `apply.py` | Revalidate plans, apply safe actions, postchecks and recovery report | `apply_plan(plan) -> ApplyResult` |

Introduce each module with its first real caller, not as empty scaffolding. Keep
records with their owning capability; no generic services, repositories, or
utility package. A small concrete `Plan`/`Action` model belongs with the shared
application boundary used by adoption and update.

### Existing modules intentionally not extended

- `.harness/scripts/migrate_to_framework.py` already spans roughly 1,500 physical
  lines and combines discovery, checks, generation, mutation, and reporting.
  New lifecycle behavior goes in the shared package; this script becomes an
  adapter in the lifecycle shipping group.
- `setup_update.py` must not gain another ownership algorithm beside the shared
  planner. Its legacy interface translates arguments and reports deprecations.
- `check_feature_docs.py` retains feature-documentation responsibility; it does
  not become the growth checker or source-graph implementation.
- The eval runner keeps running cases; fixture logic belongs in tests.

### Expected implementation footprint

Approximately 10–15 runtime/launcher files across the complete change, plus
focused test modules, one reviewer definition, one policy document, and generated
upstream Graft skill wiring. Graft caches remain ignored local artifacts. Existing workflow, packaging, runtime, and CI files receive
localized integrations. Each group below names its subset; this is not a demand
to create every possible module regardless of need.

Aim for cohesive modules below 300 code lines; no new handwritten source above
500 without an explicitly reviewed exception. Split tests by independently
testable behavior if needed. Do not count generated graph/Markdown as handwritten
source. Do not pad root instructions with policy text.

## Important types and interfaces

### Configuration and diagnostics

Extend the existing JSON manifest with `schema_version`, `defaults`, and `project`
sections. Retain `template_version` and `files`. Resolve configuration by merging
documented factory defaults with project overrides; unknown configuration keys
produce diagnostics rather than silently ignoring a misspelled safety setting.

The maintainability object exposes `enabled`, `warn_file_lines=300`,
`max_file_lines=500`, `substantial_growth_lines=150`, and `exceptions` containing
`path`/`reason`. Reject booleans where integers are required. Exact normalized
paths must remain inside the repository. Source scope identifies Python v1 and
documented exclusions; unsupported languages are visible, not implicitly checked.

Factory configuration records only the tested Graft dependency/integration
contract. Graft owns navigation settings, symbols and graph storage; remove
`project.codemap` and do not introduce a replacement annotation schema.

`Diagnostic` contains a stable code, severity, optional path, explanation, and
remediation. `GrowthFinding` contains current/base paths, available code counts,
growth, status, and exception reason. CLI exit codes: 0 for success with possible
warnings, 1 for failed checks/conflicts, and 2 for invalid invocation. Errors
never disappear behind quiet output; library functions do not terminate Python.

### Source counting and Graft contracts

Preserve `LineCounts` and the existing token/AST code-line accounting unchanged.
Graft replaces only navigation analysis. No factory-owned graph records, renderer,
Mermaid escaping layer, source-hash cache or semantic annotation system is needed.

The small Graft boundary calls the upstream executable using argument arrays and
an explicit repository root. It never invokes a shell with interpolated input.
Capture exit status and actionable stderr; missing/incompatible executables are
errors, not successful empty navigation. Keep version pinning separate from the
application package manifest. Validate the selected executable/package once
installed; do not fetch packages implicitly from doctor or reviewer commands.

Expose upstream `/graft` and CLI guidance with this lifecycle contract:
- Implementer: explicit structural build after targeted tests.
- Reviewer: `graft check`, plus queries with `--no-refresh` or
  `GRAFT_NO_REFRESH=1`; never build, enrich, install, or refresh.
- CI: install the pinned dependency, prepare its local cache, then test freshness
  and integration without LLM credentials.
- Human review: relevant on-demand impact output or optional visualization export,
  not a mandatory checked-in CODEMAP diff.

Obtain the unchanged skill from the pinned package’s skill template; preview writes and
validate disabled hooks, preserved statusline, repository-local scope and no
implicit global configuration. Keep safety/lifecycle instructions in the factory
rather than forking upstream skill content. Graft’s own versioned configuration
and cache stay under its ownership. Integration tests must prove that querying
with refresh disabled leaves cache, source and configuration unchanged.

### Ownership and plan contracts

Manifest entries keep full-file distribution hashes and add explicit ownership
mode and, where needed, named section metadata. Distribution hashes verify
template contents; installation fingerprints describe the actual managed scope.
Neither manifest nor state fingerprints itself. Project fields remain outside
factory metadata replacement. Graft cache content is derived locally and never fingerprinted or copied from
the starter. Track only explicitly owned integration wiring; preserve existing
Graft configuration and report incompatible versions or ownership conflicts.

`Plan` records template/target roots, target Git baseline, observed input hashes,
actions, conflicts, and detections. Actions use ADD/MERGE/PRESERVE/CONFLICT/SKIP
with path, reason, owned scope, and proposed content where relevant. A plan is
computed in memory and printed; no workflow-status store is introduced.

Apply reconstructs/revalidates current inputs and rejects any unresolved conflict
before writing. Reject `.git` paths, traversal, malformed markers, special files,
and symlink escape paths. Mutation preflight requires a clean committed target;
read-only planning does not. Target and template must not overlap for adopt/update.

The installation record stores schema/version and per-scope upstream hashes.
For legacy content, matching a historical pristine hash is evidence; otherwise
report customization. Treat missing local content as a local edit. Upstream
removals need a visible plan and preserved customizations; do not delete files
merely because a newer manifest no longer lists them.

## Data and control flow

### Group 1: Runtime and deterministic growth

Launcher runtime guard → CLI → config validation → existing merge-base resolver
→ safe changed-source inventory → base/current token counts → policy findings.
The full gate adds this check through its existing quiet wrapper. Explicit
full-repository inspection warns on sizes with unknown history; normal diff
verification fails visibly if a requested comparison base cannot be resolved.

Ship the short policy and Code Shape template extension here. The semantic
reviewer and Graft completion instructions join together in group 2 so commands
never refer to an unavailable stage. Upgrade active Python metadata, lockfile,
CI, bootstrap checks, and emitted migration defaults together.

### Group 2: Graft navigation and independent maintainability review

First reconcile the uncommitted custom CODEMAP attempt: remove its navigation
modules, generated files, annotation settings, tests and command integrations,
while preserving group 1 source/growth code and reusable reviewer work. Scope this
cleanup to this branch’s CODEMAP additions; do not reset unrelated user edits.

Validate a pinned Graft release on a disposable fixture before wiring the starter.
Then add `/graft`, dependency setup, structural build/read-only retrieval guidance,
and the maintainability reviewer. Existing task group/branch identity remains
`factory-phase2`, group 2; no new parallel change framework is introduced.

Flow: targeted tests → Graft structural build → maintainability review → fresh
behavioral verifier → human review. Supply identifiers to fresh reviewers, never
implementation-session reasoning. Report concerns and missing evidence explicitly.
Append actual group results and deviations to implementation-report.md.

### Group 3: Installation diagnosis

Doctor reads installed manifest/version → required structure and hook/settings
checks → configuration/exception validation → Graft dependency/wiring/freshness → findings. Register
only checks for functionality actually shipped at this stage. Baseline ownership
state is not made mandatory before group 4 installs it. Integrate doctor into
make check and CI without invoking make check from doctor.

### Group 4: Shared adoption/update and ownership transition

Template verification + target inspection + optional existing baseline → one
ownership model → adoption/update plan → explicit apply → clean-tree/input
revalidation → writes → baseline state → doctor and follow-up report.

Publish the complete managed inventory, markers, section payloads, and state
conversion together with both compatibility adapters. Activate doctor baseline
checks at that point. Upgrade the completed template version to 2.0.0 and refresh
starter installation metadata with make manifest. Intermediate groups preserve
working legacy behavior and do not claim the lifecycle transition is complete.

## Integration boundaries

- Use repository-root discovery independent of current working directory. CLI
  supports an explicit root; adopt/update require explicit target and a local
  template source, defaulting to the invoking checkout when it is that source.
- Reuse merge-base resolution through the existing helper, passing arguments
  positionally. Git inventories use NUL delimiters to handle unusual filenames.
- Existing `make check` remains product verification; maintainer tests remain
  `make harness-test`. Add actual factory module lint/type coverage to the
  maintainer workflow so hidden code is not silently outside validation.
- Hooks keep existing protection behavior. Doctor inspects settings without
  opening `.env`, executing project commands, or making network requests.
- Legacy script paths and dry flags remain available. Tests of supported public
  behavior persist; tests that assert forbidden force overwrites are deliberately
  replaced with explicit preservation/conflict tests in group 4.
- Human reviews and commits remain separate. Shaping cannot authorize shipping.

## Test design

### Behavior tests

Place pure policy/serialization tests in `.harness/tests/unit/` and real
filesystem/Git/CLI cases in `.harness/tests/integration/`, retaining existing
pytest markers and test conventions.

| Area | Evidence |
|---|---|
| Code counts | Blank/comment/docstring exclusion; inline code; multiline string data; async functions; encoding |
| Thresholds | 300/301, 500/501, and 149/150 boundaries; project override; disabled policy |
| Growth | New 900-line file fails; existing 900 unchanged passes; 700→950 fails; staged/unstaged/untracked; rename |
| Exceptions | 1500-line generated fixture; duplicate/missing/escaping/wildcard paths; empty reasons; invalid types |
| Graft navigation | Real pinned-release fixture covers application Python sources, excludes factory/harness tooling, and checks public surfaces, retrieval and impact evidence; do not retest every upstream parser |
| Graft integration | Previewed local wiring, preserved instructions/statusline, hooks disabled, no global agent configuration changes, isolated dependency |
| Graft checks | Missing executable, incompatible release, missing/stale cache; read-only queries/checks preserve source/config/cache bytes |
| Reviewer | Read-only tools, restricted inputs, exact PASS/CONCERNS contract, concrete drift output in a prompt eval where useful |
| Doctor | Missing commands/hooks; invalid manifest/config; absent protections; stale Graft cache warning; normal starter health |
| Adoption | Plan writes nothing; canonical make check and instructions preserved; Python/non-Python detections; unknown commands |
| Update | Four-way fingerprint table, convergence, local deletion, upstream removal, legacy unknown hashes, section preservation |
| Apply | Dirty target refusal; conflict preflight writes nothing; changed inputs rejected; failures report recovery paths |
| Packaging | Fresh inventory contains every runtime dependency; project overrides survive refresh; old entry points agree with new |

### Failure cases

Use disposable Git repositories for destructive-path assertions, never the user's
working checkout. Simulate a write or postcheck failure and assert failure status,
reported baseline/paths, and no false installed-success claim. Use malformed JSON,
invalid Python, broken markers, and symlink fixtures to exercise error boundaries.
Do not weaken checks to get starter dogfooding to pass.

### Neighbouring regression risks

Retain existing manifest OpenSpec ownership exclusions, migration/update safety,
base selection, feature-doc checks, shell portability, quiet failure propagation,
root instruction size budget, static eval credentials, and verifier independence.
Regenerate the template manifest after owned changes, and build the Graft structural cache after
targeted implementation tests once group 2 has shipped. Fresh verification owns
the full gate; broaden testing only for changed behavior or unresolved failures.

## Migration / compatibility

Groups ship sequentially on `feat/factory-phase2-g1` through `-g4`; each subsequent
group waits for its predecessor to merge and starts from updated main. The
already-created group 1 branch belongs to this session: do not rerun branch
creation as though it were an unclaimed branch.

Keep historical Phase 1 reports/designs unchanged. Runtime documentation refers
to 3.12 while historical records retain the version they actually verified.
The first three groups are useful incremental improvements; complete ownership
and baseline activation occurs only with group 4. Final archive waits for all
groups and the human-approved canonical spec diff.

## Least-confident decisions

- Graft’s published release, application-only scope and installation side
  effects need fixture validation. Select a pinned release and verify integration
  before adopting it; if it cannot satisfy the approved boundaries, stop and
  present evidence instead of restoring an in-house analyzer implicitly.
- Legacy arbitrary instruction/Makefile structure may prevent a clean bounded
  merge. The accepted fallback is a conflict with remediation; fixtures must
  prove preservation before extending the recognized patterns.
- Keeping project configuration in the distribution manifest makes regeneration
  delicate. Round-trip override tests and non-self-referential fingerprint rules
  are mandatory before adding update mutation.

These are bounded implementation risks with accepted safe outcomes, not unresolved
architecture choices. If evidence invalidates an accepted boundary, stop and
present the issue, consequence, and suggested revision before proceeding.

### Application-only navigation scope — 2026-09-11

The user clarified that Graft graphs cover the main project implementation only.
Exclude factory and harness tooling, including tooling outside hidden directories.
Use upstream scope controls to select application source roots; do not infer graph
scope from dot-directory exclusion alone. This does not narrow source-growth
enforcement or independent source review of factory changes.

No-application behavior accepted 2026-09-11: when no application sources are
configured, report `not applicable: no application sources configured`. Validate
Graft against an application fixture; retain tooling growth and behavioral gates.
Document `/graft` usage in HARNESS.md.

### Approved skill-only integration — 2026-09-11

Graft 0.18.0's Claude installer adds hooks despite `--no-hooks`. The user approved
installing only its unchanged upstream skill and isolated CLI. Preview skill
installation, preserve customized skill files, and do not run upstream `init`.
The generated skill stays upstream-owned and ignored; `make graft-install`
regenerates it from the locked package without hooks, MCP or global agent wiring.

The factory's `.harness/bin/graft` launcher delegates through `factory navigation`
to the thin `graft.py` boundary. `project.navigation.application_roots` in the
existing manifest records the explicit application input list (empty in this
starter), forwarded as upstream `--only-dir` options. Graft still owns all graph
and cache formats. The launcher checks the pinned release, disables dotenv and
query refresh. Upstream owns fingerprint selection and validation; the wrapper
does not inspect fingerprint files. Changing application roots requires an
explicit build before review because upstream checks the last-built scope.
This input list is not an alternate graph/configuration store. Supported review
commands are check, ask, grep, skeleton, callers, map and blast; structural build
and explicit optional `build --deep` belong to the implementer. Upstream visual
exports remain optional, outside the required read-only command surface.
