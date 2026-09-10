## Context

See `proposal.md` for scope and `intent.md` for user-accepted decisions.
Architecture and capability deltas accepted by the user on 2026-09-10.
Program design and task groups are reviewed separately before implementation.

Phase 1 inspection at main `35d871f` confirmed:

| Contract | Existing implementation |
|---|---|
| Tier routing and human gates | `FACTORY.md`, root `CLAUDE.md` |
| DEEP program design | `.claude/skills/shape-change/SKILL.md` |
| One group/branch/PR and selective context | `.claude/commands/dev-change.md`, its shell preamble |
| Fresh read-only verifier | `.claude/agents/verifier.md` |
| Quiet non-mutating full gate | `.harness/scripts/cmd_check.sh`, `lib/run_quiet.sh` |
| Template version and upstream history | `.harness/TEMPLATE_VERSION` (1.5.0), `template-manifest.json` |
| Manifest generation | `.harness/scripts/generate_template_manifest.py`, `make manifest` |
| Adoption precursor | `.harness/scripts/migrate_to_framework.py` |
| Update precursor | `.claude/skills/setup-update/scripts/setup_update.py` |
| Installation stamps | `.claude/template-version.json`, migration report |
| Static and prompt evals | `.harness/evals/`, `make evals`, `make evals-full` |

These are source inspection findings, not new execution-test results. The Phase 1
report records prior verification. Phase 2 must produce its own evidence.

## Goals / Non-Goals

Keep language-neutral configuration, deterministic bootstrap tooling, and small
modules under the existing harness. Maintain one ownership authority for both
old and new lifecycle entry points. Make navigation inexpensive and review
concerns concrete. Preserve all Phase 1 stage and shipping boundaries.

Exclude a language server, perfect dynamic call graphs, automatic refactoring,
AI merges, Wayfinder, package-release infrastructure, and new workflow-state
documents. Python is the first source-analysis adapter; do not silently claim
equivalent analysis for unsupported languages.

## Decisions

### Runtime and interface

Use Python 3.12+ across tooling, dependency metadata, lockfile, Ruff, mypy, CI,
setup checks, and documentation. Standalone CLI entry points check the runtime
and explain how to obtain a supported interpreter. Hooks retain their existing
security behavior during migration.

Provide a repository-root `factory` executable, backed by cohesive modules under
`.harness/`, with doctor, map, maintainability, adopt, and update subcommands.
Document `./factory` as the portable invocation; no global installation or PATH
mutation is required. Keep `make manifest` as the existing refresh operation.
Existing migration/update scripts delegate to the shared lifecycle engine.

### Configuration and installation metadata

Extend `.harness/template-manifest.json` with a schema version, defaults, and
ownership metadata. Preserve `template_version`, file hashes, and hash history.
Put project overrides and optional CODEMAP semantics in its clearly separated
project configuration section. Manifest regeneration preserves these overrides;
updates merge factory metadata without replacing project configuration.

Keep `.harness/TEMPLATE_VERSION` as the version source; a completed Phase 2
release uses 2.0.0 because runtime and ownership contracts change. Do not add a
second human configuration file or a redundant version authority.

Use `.factory/state.json` only for installation metadata: installed version and
upstream fingerprints for owned files or sections. It contains no task status.
Unknown schema versions fail with remediation rather than guessed parsing.

### Code-line accounting and growth

Use Python tokenization and AST docstring locations to count physical lines
containing code, excluding blank lines, comment-only lines, and docstring-only
lines. A line containing code plus a comment or docstring still counts. Regular
multiline string data is code, not documentation. Syntax errors are reported as
analysis failures rather than interpreted as zero lines.

Keep physical LOC separately for CODEMAP metrics. Discover tracked and
non-ignored untracked source, including hidden harness tooling. Ignore deleted
files, caches, vendored dependencies, and generated artifacts through documented
source classification and explicit reasoned exceptions. Do not follow symlinks
outside the repository or inspect environment-secret files.

During verification compare the working tree, including staged/unstaged and
untracked changes, with the merge base resolved by the existing base-branch
contract. Preserve rename identity where Git identifies it so moving an existing
large module does not automatically make it a new pathological file. Missing
comparison history must be explicit; full-repository inspection can warn about
existing sizes but must not invent growth evidence.

| Condition, without exception | Outcome |
|---|---|
| At most 300 code lines | Pass |
| More than 300, at most 500 | Warning |
| New file with more than 500 | Failure |
| Existing file with more than 500 and at least 150 net added lines | Failure |
| Existing file with more than 500 and smaller growth | Warning |
| Deleted file | Ignore |
| Valid path-specific exception | Report exception and reason; exempt from size failure |

Thresholds and enabled state are configurable. Validate positive integer values,
warning below maximum, and a positive substantial-growth threshold. Exact-path
exceptions require nonempty reasons, existing regular files, unique normalized
paths, and repository containment. V1 rejects wildcard exception entries; an
explicit project-wide disabled setting is visible and distinguishable from a
malformed configuration. Exceptions are checked-in reviewer-visible decisions,
not something the implementation agent silently grants itself to pass a gate.

### Maintainability review and lifecycle

Keep the short policy in harness documentation and reference it at relevant
stages. New DEEP program designs require Code Shape: reused modules, new modules
and public surfaces, modules intentionally not extended, and rough footprint.
Do not retrospectively rewrite accepted Phase 1 designs. STANDARD can abbreviate
this in design.md.

The fresh read-only reviewer discovers the diff, relevant accepted design,
immediate neighbours, and deterministic growth output. It receives identifiers,
not implementation narrative. It reports PASS or CONCERNS with M-identifiers,
locations, problems, consequences, and specific directions. Structural drift,
duplication, coupling, or needless abstractions are review concerns; they do not
independently prove behavioral failure. Return concerns to the implementer or
human; the reviewer never edits. Avoid speculative interfaces, frameworks,
one-function fragmentation, and generic utilities.

```mermaid
flowchart LR
  implementation --> targeted_tests --> map_refresh
  map_refresh --> maintainability_review --> fresh_verifier --> human_review
  human_review --> commit_PR
```

FAST can skip the semantic reviewer; deterministic growth still joins the full
gate. Doctor must never call make check. Map refresh occurs once at completion,
not in a post-tool hook. Human review reads specs, design, map changes, diff, and
both review outputs. Preserve the existing verifier/shipping full-gate ownership.

### Source graph and navigation

Separate Python analysis, a normalized versioned graph, and rendering. The graph
has sorted modules, symbols, imports, calls, and entrypoints with stable IDs,
paths, locations, signatures, and edge confidence. Serialize it to
`.codemap/graph.json`; render `CODEMAP.md` from this data plus project annotations.

Extract top-level functions/classes, public methods, imports, physical and code
lines, main guards, and declared Python console entry points where resolvable.
Resolve direct local calls and imported names when supported by static evidence.
Label approximate relationships and omit unresolved dynamic dispatch rather than
inventing targets. Keep external imports as analysis data, excluding them from
primary Mermaid diagrams. Bound diagram size and depth, group major modules, and
state omissions explicitly. Discoverable entry points get bounded flow diagrams.

Annotations supply responsibility, capability navigation, and boundary contracts
that source cannot reliably convey. Reuse existing feature instruction references
where useful; do not copy their prose or maintain manual symbol inventories.
Escape source-derived labels for Markdown/Mermaid and use safe generated node IDs.

The renderer includes System at a Glance, Entry Points, Major Flows, Modules,
Important Data / Contracts, Where Should I Look If..., and Generated Metrics.
Generated output contains no timestamps. `map --check` compares both artifacts
without writing them and reports stale or missing output.

```mermaid
flowchart LR
  source --> analysis --> graph --> markdown_mermaid
  annotations --> markdown_mermaid
```

OpenSpec defines expected behavior; design/ADRs define rationale; source defines
implementation; CODEMAP locates implementation. Retrieval starts with relevant
specs and map sections, then the indicated code, expanding only as needed.

### Ownership, adoption, and update

Use the existing manifest allowlist as the starting inventory, then classify
each entry as full-file ownership, bounded-section ownership, or preserve.
Factory policy, shipped commands/hooks, and runtime modules can be fully owned.
Root instructions and Makefile additions use named marker regions. Project
source, existing CI, and project documentation remain project-owned. Existing
JSON hook configuration requires a structural merge retaining unrelated values;
conflicting factory hook settings are surfaced, not overwritten.

Adopt accepts an explicit target and local template checkout. Initial source
distribution remains a local checkout, matching the existing scripts; no network
fetch or new registry is needed. Inspection proposes detected build/test tools
and preserves canonical commands. Python is the first fully supported adoption
path; other detected stacks receive conservative plans with unsupported steps
identified, never fabricated checks or wholesale Python project replacement.

Default adopt/update invocations are read-only plans listing ADD, MERGE,
PRESERVE, CONFLICT, and SKIP. `--apply` rechecks the plan against current input.
All conflicts are found before writes; an unresolved conflict prevents apply.
Require a clean committed target Git worktree for mutation, record its recovery
commit, and leave resulting changes uncommitted. Reject unsafe paths, symlink
escapes, malformed marker regions, and unsupported ownership metadata before
writing. Never claim ownership outside the explicit inventory.

Install required OpenSpec directory structure without copying upstream specs or
claiming CLI-managed OpenSpec artifacts. Automatically run doctor after apply;
report failed postchecks with recovery instructions and never claim success.

Updates compare each local file/section and proposed upstream content with its
recorded upstream fingerprint:

| Local changed | Upstream changed | Action |
|---|---|---|
| No | No | Preserve |
| No | Yes | Replace owned content |
| Yes | No | Preserve local content |
| Yes | Yes | Conflict, unless local already equals new upstream |

Treat local deletion as a local change. For dual changes, reporting a conflict is
the v1 deterministic strategy; a three-way merge is optional in the source brief
and would require storing retrievable base content. Do not add that machinery
until it is justified. Bounded-section updates preserve all surrounding bytes.
Advance fingerprints only for successfully reconciled entries; a conflict must
not be hidden by updating its baseline or installed-version stamp.

Legacy hash matches can identify pristine files; unmatched legacy contents remain
customizations. The first conversion previews new ownership and baseline state.
Recognize legacy version stamps for migration, then use the shared state model.
Keep legacy script paths and dry-run options, with clear deprecation guidance;
reject legacy `--force` when it requests forbidden overwrite behavior.

### Doctor, dogfooding, and validation

Doctor independently validates manifest/version/state consistency, directories,
commands and hook wiring, applicable executable bits, OpenSpec structure,
gitignore and secret protections, maintainability settings and exceptions,
CODEMAP settings/freshness, and eval configuration. Findings identify a path,
severity, and remediation. Invalid installation structure fails; stale navigation
is a warning in doctor and a failure in explicit map --check.

The starter uses the same installation contracts; make manifest refreshes both
distribution metadata and starter baselines deterministically. Doctor validates
owned content against expected metadata without treating recorded downstream
customizations as corruption. Add doctor to the full gate and CI without a loop.

Use semantic fixture tests for line boundaries, comments/docstrings, grandfathered
growth, exceptions, renames, graph extraction/determinism, Mermaid escaping,
adoption preservation, clean-worktree requirements, and the update truth table.
Test conflicting and missing metadata, deleted files, changed marker sections,
and unknown legacy customizations. Static evals verify lifecycle and read-only
review contracts. Prompt evals cover only agent behavior that static checks
cannot establish; report authentication gaps honestly.

## Risks / Trade-offs

- A 500-code-line limit may encourage fragmentation → short cohesion policy,
  explicit exceptions, and a reviewer that discourages needless abstraction.
- Net growth does not detect large rewrites of unchanged size → semantic review
  covers responsibility and duplication; line checks remain a narrow signal.
- Python v1 leaves other languages unanalyzed → report scope and unsupported
  files explicitly; keep configuration and graph independent of the adapter.
- One manifest holds generated metadata and project settings → separate fields,
  preserve overrides on regeneration, and test update behavior.
- Legacy ownership is ambiguous → preview conflicts; never infer permission to
  replace customized whole files or claim existing project content.
- Filesystem failure after writes start → clean Git baseline plus documented
  created paths and recovery instructions; report partial failure, not success.
- Full Phase 2 is too broad for a casual single PR → shape independently
  shippable groups after architecture acceptance; do not conflate branch creation
  with approval to implement every future group on that branch.

## Migration Plan

After architecture acceptance, prepare Code Shape and independently shippable
groups with tests and integration in each. Keep the first group on the created
`feat/factory-phase2-g1`; later dependent groups wait for their prerequisites.
Preserve Phase 1 change artifacts. Upgrade runtime and contracts together where
their shipping boundary requires it. Update the manifest using make manifest,
refresh CODEMAP at implementation completion, and run independent reviews.

Downstream adoption/update apply remains explicit and produces uncommitted Git
changes. Humans inspect the printed actions, resulting diff, doctor, map check,
and relevant eval evidence before committing. Rollback restores only paths and
managed regions reported by the operation from the recorded clean Git baseline;
no automatic reset, clean, or hidden backup directory is introduced.
