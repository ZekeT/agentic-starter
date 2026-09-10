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
| `graph.py` | Normalized source-graph records and stable serialization | `CodeGraph`, `serialize_graph(graph)` |
| `python_analysis.py` | AST symbols, imports and entry points | `analyze_python(root, sources) -> CodeGraph` |
| `call_edges.py` | Resolve supported local imports/calls without dynamic guesses | `resolve_edges(graph, syntax) -> list[CallEdge]` |
| `map_render.py` | Markdown/Mermaid navigation from graph and annotations | `render_map(graph, annotations) -> str` |
| `codemap.py` | Compose analysis, rendering, refresh and non-mutating check | `build_map(root, config)`, `refresh_map(...)`, `check_map(...)` |
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

Approximately 15–20 runtime/launcher files across the complete change, plus
focused test modules, one reviewer definition, one policy document, and generated
graph/map artifacts. Existing workflow, packaging, runtime, and CI files receive
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

CODEMAP configuration owns module responsibility/contract annotations, navigation
entries, and bounded graph settings. Validate annotation paths and referenced
navigation destinations; machine-generated symbols remain outside configuration.

`Diagnostic` contains a stable code, severity, optional path, explanation, and
remediation. `GrowthFinding` contains current/base paths, available code counts,
growth, status, and exception reason. CLI exit codes: 0 for success with possible
warnings, 1 for failed checks/conflicts, and 2 for invalid invocation. Errors
never disappear behind quiet output; library functions do not terminate Python.

### Source and graph contracts

`LineCounts` separates physical LOC and code LOC. Token and AST positions must
exclude only docstring tokens, not executable statements sharing the same line.
Support Python source encodings using standard-library source decoding.

Graph schema version 1 contains `modules`, `symbols`, `imports`, `calls`, and
`entrypoints`, plus analysis diagnostics. Module IDs use relative POSIX paths;
symbol IDs combine path and qualified name. Edges identify source and target,
source location, relationship kind, and confidence. Internal module resolution
requires an unambiguous mapping; duplicate script basenames must not create false
edges. Signatures preserve positional/keyword structure, defaults and annotations
where available. Do not execute imports, source, annotations, or build scripts.

Sort serialized records by stable keys. Render safe Mermaid identifiers derived
from IDs and escape labels/table cells. Graph limits must disclose omissions.
No supported entry points means an explicit empty-state explanation, not an
invented request flow. Refresh validates all input before replacing artifacts;
check mode computes expected bytes without writing either artifact.

### Ownership and plan contracts

Manifest entries keep full-file distribution hashes and add explicit ownership
mode and, where needed, named section metadata. Distribution hashes verify
template contents; installation fingerprints describe the actual managed scope.
Neither manifest nor state fingerprints itself. Project fields remain outside
factory metadata replacement. Generated CODEMAP is derived target content, not
an upstream map copied from the starter.

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
reviewer and map completion instructions join together in group 2 so commands
never refer to an unavailable stage. Upgrade active Python metadata, lockfile,
CI, bootstrap checks, and emitted migration defaults together.

### Group 2: Navigation and independent maintainability review

Safe inventory → Python analysis → resolved supported edges → normalized graph
→ annotation-enriched Markdown/Mermaid. `factory map --check` compares both
artifacts; `factory map` refreshes them. Then add the read-only reviewer and
completion sequence to dev/review/verifier guidance. The new reviewer receives
slug/group or branch identity only and discovers static evidence independently.

### Group 3: Installation diagnosis

Doctor reads installed manifest/version → required structure and hook/settings
checks → configuration/exception validation → map freshness → findings. Register
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
| Graph | Classes/functions/method signatures/import aliases/relative imports/entry points/basic calls; ambiguous targets omitted |
| Rendering | Required headings, no external primary nodes, escaped labels, graph limits and disclosed omissions |
| Map check | Stable output bytes; stale/missing graph or Markdown; no writes on check or analysis failure |
| Reviewer | Read-only tools, restricted inputs, exact PASS/CONCERNS contract, concrete drift output in a prompt eval where useful |
| Doctor | Missing commands/hooks; invalid manifest/config; absent protections; stale map warning; normal starter health |
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
Regenerate the template manifest after owned changes, and refresh CODEMAP after
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

- Import/call resolution in standalone scripts is inherently approximate. Start
  with provable local mappings, label approximations, and test ambiguous names;
  a richer resolver is deferred, not a reason to invent graph edges.
- Legacy arbitrary instruction/Makefile structure may prevent a clean bounded
  merge. The accepted fallback is a conflict with remediation; fixtures must
  prove preservation before extending the recognized patterns.
- Keeping project configuration in the distribution manifest makes regeneration
  delicate. Round-trip override tests and non-self-referential fingerprint rules
  are mandatory before adding update mutation.

These are bounded implementation risks with accepted safe outcomes, not unresolved
architecture choices. If evidence invalidates an accepted boundary, stop and
present the issue, consequence, and suggested revision before proceeding.
