# Factory Phase 2 implementation report

This is a cumulative review record, following the Phase 1
[implementation report](../software-factory/implementation-report.md).
The task checklist remains [tasks.md](tasks.md).

Append one numbered section per completed task group before its human review
handoff. Each section records the date and branch, files added/modified/removed,
before/after behavior, compatibility, verification evidence, review fixes,
limitations, deviations and pending decisions. Distinguish implementer checks
from independent verification and local results from CI results. Record later
corrections as dated addenda under the relevant group; preserve earlier evidence
instead of rewriting it to imply that later checks ran against earlier code.
Do not prefill results for unimplemented groups. The last group also appends a
Phase 2 acceptance summary covering delivered and deferred scope.

## Group 1 — Python 3.12 and configurable source-growth enforcement

Recorded on 2026-09-11 on `feat/factory-phase2-g1`, covering tasks 1.1–1.5
and the subsequent review fixes. Implementation and local regression checks are
complete. Changes remain uncommitted; the review fixes have not received a new
independent verifier verdict. Groups 2–4 have not started.

### Files added

- `factory`: repository-local launcher with an unsupported-interpreter guard.
- `.harness/factory/__init__.py`, `cli.py`, `config.py`, `source.py`, `growth.py`:
  command dispatch, validated configuration, source discovery, Python code-line
  accounting and merge-base growth analysis.
- `.harness/docs/maintainability.md`: short cohesion policy, configuration and
  command guidance.
- `.harness/evals/cases/015-maintainability.yaml`: static policy and packaging eval.
- `.harness/tests/integration/test_growth.py`: growth, configuration, source and
  launcher regression fixtures.
- Change-local planning and review artifacts: `.openspec.yaml`, `intent.md`,
  `proposal.md`, `design.md`, `program-design.md`, `tasks.md`, this report and
  `specs/{factory-maintainability,factory-codemap,factory-installation}/spec.md`.
  These describe all four groups; their presence does not mean all are implemented.

The repository-root `idea.md` is the source brief, not a delivered runtime file.

### Files modified

- `.claude/skills/setup-update/scripts/setup_update.py`
- `.claude/skills/shape-change/SKILL.md`
- `.github/workflows/evals.yml`
- `.harness/docs/setup.md`
- `.harness/scripts/cmd_check.sh`
- `.harness/scripts/generate_template_manifest.py`
- `.harness/scripts/migrate_to_framework.py`
- `.harness/setup.sh`
- `.harness/template-manifest.json`
- `.harness/tests/integration/test_factory_checks.py`
- `.harness/tests/integration/test_generate_template_manifest.py`
- `CLAUDE.md`
- `Makefile`
- `openspec/config.yaml`
- `pyproject.toml`
- `uv.lock`

### Files removed

None.

### Before and after

| Before | After |
|---|---|
| No deterministic source-growth check | `factory maintainability` checks changed Python files against the configured merge base |
| No file-size policy in the full gate | Warnings above 300 code lines; new files above 500 fail; existing oversized files fail at 150 net added lines |
| No configurable growth exceptions | Manifest defaults and project overrides, with exact-path exceptions requiring reviewed reasons |
| No code-line accounting | Token/AST counting excludes blank, comment-only and docstring-only lines while retaining ordinary string data and same-line code |
| No growth evidence for working-tree changes | Staged, unstaged and non-ignored untracked files are included; Git-detected renames retain their baseline |
| No explicit size-only mode | `--all` warns without inventing history; missing history fails normal comparison |
| DEEP template lacks Code Shape | New designs name reused/new modules, public surfaces, modules intentionally not extended and expected footprint |
| Python 3.11 project/tooling baseline | Starter metadata, tooling guards, emitted defaults and CI use Python 3.12; growth tooling runs separately from downstream project environments |

`make check` retains its quiet wrapper, complete failure output and non-mutating
source checks. `--verbose` includes passing-file evidence. Configuration disabling
and exemptions are explicit in command output. Maintainer checks now lint,
format-check and type-check the new factory package.

### Compatibility and packaging

The starter requires Python 3.12+. Standalone launcher, migration and update
guards reject older interpreters with upgrade guidance. The full gate invokes
`uv run --no-project --isolated --python 3.12 python factory maintainability`,
preserving downstream project requirements, virtual environments and lockfiles.
uv may install the tooling interpreter on first use.

The existing manifest inventory packages the launcher and runtime dependencies.
Regeneration preserves project overrides and hash history, accepts schema 1 and
legacy unversioned input, and rejects unsupported schema versions before writing.
Legacy migration/update paths initialize growth configuration; their shared
ownership-engine conversion remains group 4 work. Template version remains 1.5.0;
the planned 2.0.0 version change belongs to the completed lifecycle rollout.

FAST/STANDARD/DEEP boundaries, existing security hooks and the human shipping gate
remain in place. Canonical specs and Phase 1 artifacts were not changed.

### Verification and review fixes

Initial independent evidence is recorded in `tasks.md`: the fresh verifier
returned PASS after resolving missing verbose PASS-file evidence, quiet-wrapper
integration, tomllib-version wording and a docstring-semicolon counting issue.
It ran `make check`, `make harness-test` (196 tests), `make evals` (15/15 static),
verbose growth evidence, 94 manifest-hash assertions and docstring edge cases.
Strict OpenSpec validation was also recorded as passing for that earlier state.

The subsequent human-requested review identified two additional issues:

1. A migrated downstream Python 3.11 environment could still be selected by the
   growth gate. The gate now selects isolated Python 3.12 tooling. A fixture
   migrates a real Python 3.11 project and executes the actual uv/factory command,
   checking that its environment, project metadata and lockfile remain unchanged.
2. Manifest regeneration silently replaced unknown schema versions with schema 1.
   It now rejects them before writing. Fixtures check unchanged input bytes on
   rejection and retained overrides/hash history for supported inputs.

Post-fix implementer results, observed locally on 2026-09-11:

| Check | Result |
|---|---|
| Targeted gate and manifest tests | 39 passed, including the real Python 3.11 fixture |
| `make check` | Passed format, lint, types, tests, maintainability and feature-docs |
| `make harness-test` | Factory lint/format/types passed; 204 tests passed |
| `make evals` | 15/15 static cases passed; six prompt cases not run |
| `make manifest` | Refreshed the 94-file inventory |
| `git diff --check` | Passed |

Initial full-check/manifest attempts could not access the uv cache in the sandbox;
approved reruns passed. CI now installs Python 3.11 and 3.12 for the regression,
but no remote CI result is claimed. These local checks are not a replacement for
a new independent verifier verdict after the review fixes. This report and its
task-list links were added afterward as documentation-only changes.

### Limitations, deviations and pending decisions

- Python is the only source-analysis adapter. Other detected source languages
  are reported as unanalyzed; dynamic architecture quality is not inferred from LOC.
- Semantic maintainability review, CODEMAP generation/checking, doctor and shared
  ownership-aware adopt/update are deferred to groups 2–4 as planned.
- Six prompt evals and a clean starter environment rebuild were not repeated.
  The isolated migration fixture covers the specific downstream-runtime regression,
  not every downstream installation or operating system.
- Runtime isolation is the review-driven compatibility adjustment: factory tooling
  uses Python 3.12 without forcing an existing downstream application to upgrade.
- No unresolved implementation choice is recorded for group 1. Fresh independent
  verification after the fixes, human review and commit/PR approval remain pending.
  No shipping or archive operation was performed.

### Shipping verification addendum — 2026-09-11

The user requested `/commit-push-pr` after the review found no actionable code
defects and identified missing fresh verification evidence. The shipping session
reran `make check` (all six stages passed), `make harness-test` (factory
lint/format/types passed; 204 tests passed), and `make evals` (15/15 static;
six prompt cases skipped). All 94 manifest hashes matched and `git diff --check`
passed. The initial gate attempt was blocked by sandbox access to the uv cache;
the approved rerun passed.

These are fresh local shipping-session results, not a separate verifier-agent
rerun or a remote CI verdict. The prior review also independently ran 70 targeted
integration tests successfully. Groups 2–4 remain unimplemented. The user's
shipping request authorizes committing, pushing, and opening the group 1 PR;
it does not authorize merging or archiving.

## Group 2 feasibility checkpoint — 2026-09-11

Group 2 remains incomplete and uncommitted. Removed the paused custom CODEMAP
implementation and restored its unshipped integration edits, preserving the
merged growth checker, revised Graft planning documents and reusable reviewer.

Installed published `@nanonets/graft@0.18.0` in a disposable directory under
`/private/tmp`, isolated from application dependencies. npm reports Node >=20;
installation and CLI help succeeded with the available Node 25 runtime.
No repository skill installation or global Graft configuration was performed.

Release validation found a coverage blocker: `graft build --help` explicitly
states that dot-directories are never overridable. The published
`dist/ingest/fs.js` implements that exclusion before checking include overrides.
A direct invocation of `shouldSkipDir(".harness", new Set([".harness"]))`
returned `true`. Thus the proposed repository-root graph omits factory source
under `.harness`, contrary to task 2.2's hidden-harness coverage requirement.
CLI inspection used `DOTENV_CONFIG_PATH=/dev/null` to avoid loading `.env`.

Implementation is paused for the user's decision on this incompatibility.
Suggested direction: retain Graft, but seek an upstream hidden-directory opt-in
before making its graph a required factory review gate. No full fixture build,
freshness/mutation verification, full gates or independent group 2 reviews are
claimed by this checkpoint.

### Scope decision addendum — 2026-09-11

The user clarified that navigation must exclude factory/harness tooling and focus
on the main project implementation. This resolves the hidden-directory coverage
blocker above. Planning and the navigation delta now require application coverage
and tooling exclusion. Release integration remains unverified; no additional
build, installation or gate result is claimed.

## Group 2 implementation evidence — 2026-09-11

### Delivered behavior and files

Replaced paused custom CODEMAP work with the unchanged upstream `/graft` skill
and `@nanonets/graft@0.18.0`, locked separately under `.harness/graft`. The local
`.harness/bin/graft` launcher delegates through `factory navigation` to the thin
`graft.py` boundary. Skill installation previews writes, refuses customized skill
replacement, and appends missing ignore rules while preserving existing content.
It never runs upstream `init` or adds hooks, MCP or global agent configuration.

`project.navigation.application_roots` explicitly selects application inputs;
the starter's list is empty. Build/check report not applicable here. Python
application fixtures exercise real structural graphs, including exclusion of
visible and hidden harness tooling. Review commands force no refresh and disable
`.env` loading. Missing/incompatible dependencies, missing/stale application
graphs and changed application scope produce failures with remediation.

Added fresh read-only maintainability review between graph preparation and the
behavioral verifier. Updated CLAUDE/FACTORY/HARNESS/REVIEW and command/agent
instructions, setup guidance, migration packaging and CI preparation. HARNESS.md
includes `/graft` installation, PATH, scope, build and retrieval examples.
Template inventory includes 101 files; upstream generated skill/cache are ignored
and excluded from template ownership.

### Implementer validation

- Real Graft fixtures: 18 tests cover structural Python scope, read-only retrieval,
  missing/stale graphs (including preserved file size/mtime), changed scope,
  empty application scope, dependency errors, unsupported Node, environment and
  alternate-root bypass rejection, skill preview/idempotence/customization,
  settings/instruction preservation and ignore-rule append behavior.
- Graft plus migration regression run: 86 tests passed. Earlier manifest,
  migration and growth regression run: 124 tests passed.
- Static evals: 16/16 passed. Focused prompt eval 106: passed after an approved
  rerun with Claude authentication; the sandboxed run reported not logged in.
  Six unrelated prompt evals were not run.
- Factory lint/type checks passed. Strict OpenSpec validation and diff whitespace
  checks passed. Starter navigation build/check both reported the accepted
  no-application disposition, rather than claiming a real starter graph build.
- Fresh maintainability review and independent full-gate verification are pending;
  task 2.5 remains unchecked. No commit or PR has been created.

### Compatibility adjustments and limits

The user approved application-only scope, the no-application disposition, and
skill-only installation because the upstream Claude installer disregards its
no-hooks option. The lockfile requires Node 22.12+ through Commander 15, stricter
than Graft's advertised Node 20+; the launcher and docs enforce the actual minimum.
Local release fixtures used Node 25; CI is configured for Node 22, with no remote
CI result claimed. Only structural navigation is required; deep enrichment and
visual exports are optional and not exercised. The upstream CLI may check for
new package versions and maintain its own machine-level update cache; it does
not install global agent configuration through this integration. Tests assert
repository source/config/graph preservation, not absence of upstream version
checks. Doctor and shared ownership/adoption/update remain groups 3 and 4.

### Independent review and verification corrections — 2026-09-11

Fresh maintainability reviewer returned:

```text
PASS

No maintainability concerns requiring review.
```

The first independent verifier passed make check, make harness-test (222 tests),
and make evals (16 static cases), but returned FAIL after a real fixture showed
that `application_roots=["src"]` included `src/harness/tool.py`. The boundary now
rejects roots containing visible factory/harness subdirectories and requests
narrower roots, with regression coverage for both names and successful narrowed
application builds. This is a scope-enforcement fix, not a change to the accepted
application-only requirement.

A separate implementer correction preserves explicit provider settings only for
optional `build --deep`; default structural commands still strip Graft overrides.
Its environment regression uses fixture placeholders and makes no model calls.
Manual real-fixture `blast --format markdown` succeeded on an edited Python source
and preserved repository source/config/cache bytes. Full independent verification
of these corrections is pending; no shipping approval is implied.

### Final boundary correction — 2026-09-11

The verifier subsequently returned PASS on the nested-tooling corrections,
including make check, make harness-test (226 tests), 16 static evals, focused
prompt eval 106, independent non-mutating nested-tooling rejection and a
committed-change blast fixture. The verifier corrected an overly specific test
assertion about plural wording; no corresponding implementation defect existed.

After that tree, final dependency inspection showed dotenv merges CLI settings
after environment settings, so a query argument beginning `dotenv_config_` could
override the disabled dotenv path. The launcher now rejects those arguments
before upstream execution and removes the optional dotenv vault key from the
child environment. No `.env` file was read to validate this: a placeholder
argument and environment contract test exercise the rejection. The current
Graft suite passes 23 tests. Fresh reviews of this final correction are pending.

### Group 2 completion and final independent verdict — 2026-09-11

Fresh maintainability review of the final correction again returned PASS with
no concerns requiring review. Task group 2 is complete, including its report;
groups 3 and 4 remain pending. Changes are uncommitted on
`feat/factory-phase2-g2`, awaiting human `/review` before `/commit-push-pr`.
No canonical specs were edited, and nothing was committed, pushed or archived.

Final verifier report, verbatim:

```text
Verification — factory-phase2, group 2

Ran on current `feat/factory-phase2-g2`:
- `.harness/bin/graft check`: exit 0; accepted no-application disposition.
- `make check`: exit 0.
- `make harness-test`: exit 0; lint, formatting, types and 227 tests passed.
- `make evals`: exit 0; 16/16 static cases passed.
- `git diff --check`: exit 0.
- Template hash verification: exit 0; all 101 match.

Checked against:
- Navigation scenarios, installation preservation, dependency validation, application coverage, tooling exclusion, freshness and non-mutating retrieval: HOLDS.
- Latest dotenv override hardening and nested-tooling regressions: HOLDS.
- Reviewer restrictions, completion ordering, FAST handling and packaging: HOLDS.
- Prior independent focused prompt evaluation and committed-change impact/non-mutation fixture remain applicable and passed.

Mismatches: None remaining.

Not covered: Six unrelated prompt evals, remote Node 22 CI, optional model enrichment and visualization exports. Starter navigation correctly reports no application sources; real graph behavior is exercised through fixtures.

Verdict: PASS.
```

Only this report and the task checklist changed after the verifier's final checks;
strict OpenSpec validation and diff whitespace checks were repeated for that
reporting update. HARNESS.md contains the installed `/graft` usage instructions.

### Human-review P2 correction: structural gate after enrichment — 2026-09-11

Human review reproduced a successful structural rebuild followed by a failing
check because upstream also gates stale optional summaries. The user approved
adapting the check to distinguish structural drift from optional enrichment.

The launcher now consumes the pinned CLI's `check --json` report. Missing wiring,
added/removed/changed structural nodes, malformed reports and inconsistent process
statuses fail. Stale optional summaries and deep content are reported without
blocking a structurally current graph. Checks preserve enrichment and remain
read-only; no deep build or model access is introduced. HARNESS.md and the active
navigation delta scenario document this distinction.

Verification performed by the implementer on this correction:
- Pinned Graft integration suite: 28 passed. A fixture seeds prior summaries,
  edits source, observes structural failure, rebuilds structurally, then observes
  success with a non-blocking stale-summary message. Snapshot comparisons confirm
  checks preserve source/config/cache bytes and retain summaries.
- Additional fixtures cover stale deep content, added/removed source and an
  upstream execution failure from invalid wiring. Existing missing-cache,
  changed-source and scope tests continue to pass.
- `make harness-test`: exit 0; lint, formatting, strict types and 232 tests passed.
- `make check`: exit 0; all six gates passed.
- `make evals`: exit 0; 16 static cases passed, seven prompt cases skipped.
- `make manifest`: exit 0; refreshed the 101-file manifest.
- `.venv/bin/python factory navigation check`: exit 0, accepted no-application
  disposition. `openspec validate factory-phase2 --strict`: passed.
- `git diff --check`: passed.

Not covered: live model enrichment, remote Node 22 CI and prompt eval reruns.
Enrichment state is seeded in disposable fixtures, with actual pinned upstream
build/check processing. Earlier independent reviewer/verifier PASS reports predate
this correction; fresh independent review is still required before shipping.
Nothing was committed, pushed or archived.

### Accepted review correction: upstream-owned fingerprints — 2026-09-11

The user chose to remove wrapper fingerprint validation rather than select a
fingerprint through another internal upstream API. Graft owns fingerprint
selection and validation, including coexistence of extractor versions. The
wrapper retains application-root validation, missing-graph diagnostics and the
structural freshness gate. After changing application roots, the implementer must
explicitly build before review: upstream checks the last-built scope and does not
detect changes to the manifest's roots. HARNESS.md, design, program design and the
navigation delta record this accepted tradeoff.

Validation: the pinned Graft integration suite passed all 30 tests. New fixtures
verify successful read-only checks and queries with two fingerprints after a
rebuild, and verify an explicit build applies changed roots and excludes the old
scope. Ruff lint, Ruff formatting and mypy passed for .harness/factory.

Not covered: fresh independent maintainability/verifier verdicts, live model
calls and remote CI. This targeted correction does not replace those required
independent verdicts. Nothing was committed, pushed or archived.

### Fresh independent verification after review corrections — 2026-09-12

Fresh agents independently discovered factory-phase2 group 2 from the checkout,
without implementation-session history. The maintainability reviewer completed
first, followed by the behavioral verifier. Both returned PASS on the current
implementation, including the structural/enrichment correction and accepted
removal of wrapper fingerprint inspection.

Maintainability evidence:
- Confirmed feat/factory-phase2-g2 and merge base
  339d8f80e30d3e1b8e333ef320d939720fe85793; included untracked files.
- `uv run --no-project --isolated --python 3.12 python factory maintainability --verbose`:
  exit 0, no pathological growth. Migration script and Graft test file produced
  non-blocking size warnings; 10 non-Python files were reported unanalyzed.
- `.harness/bin/graft check`: exit 0, accepted no-application disposition.
- Verdict: PASS; no maintainability concerns requiring review.

Independent verifier report:

```text
Verification — factory-phase2, group 2
Ran:
- .harness/bin/graft check: exit 0; accepted no-application disposition.
- make check: exit 0.
- make harness-test: exit 0; 234 tests passed.
- make evals: exit 0; 16/16 static cases passed.
- Focused prompt eval 106: exit 0; 1/1 passed.
- git diff --check: exit 0.
- Independent manifest assertions: all 101 hashes match.

Checked against:
- Claimed branch and group 2 installation, scope, lifecycle, packaging and reviewer contracts: HOLDS.
- Multiple upstream fingerprints accepted without wrapper inspection: HOLDS.
- Changed application roots require explicit build; check uses last-built scope: HOLDS.
- Structural drift fails; stale optional enrichment remains nonblocking: HOLDS.
- Application retrieval and read-only source/config/cache preservation: HOLDS.
- Existing growth checks and dependency/configuration regression paths: HOLDS.

Mismatches: None found.
Not covered: Six unrelated prompt cases, remote Node 22 CI execution, actual
model-backed deep enrichment and visualization exports. Application graphs were
exercised in disposable integration fixtures; the starter has no configured
application sources. Initial sandbox cache/auth failures resolved with escalation.
Verdict: PASS.
```

These verdicts supersede the earlier pending-verification notes for group 2.
Only this report and tasks.md were updated afterward to record the results.
The implementation remains uncommitted for human /review; groups 3 and 4 remain
pending. No source, canonical specs, commits, pushes or archive state changed.

## Group 3 feasibility checkpoint — 2026-09-12

The user confirmed group 2 merged and requested continuing from main.
`git pull --ff-only` reported already up to date; claimed the new
`feat/factory-phase2-g3` branch. Earlier group 2 uncommitted-status notes above
are historical. Group 3 tasks remain unchecked; no runtime implementation or
verification results are claimed.

Local inspection of installed, pinned Graft 0.18.0 found a conflict between
doctor's offline contract and reuse of the CLI freshness check:

- `dist/cli.js` registers a `preAction` hook calling
  `maybeRefreshInBackground()` for `check`. Its skip list excludes `check`.
- `dist/upkeep.js:117` reads the machine-global update cache and, when missing
  or expired, writes its timestamp and spawns the detached `_update-check`
  command. That command requests the registry version. The function has no
  environment opt-out; `DO_NOT_TRACK` controls telemetry, not this upkeep.
- The existing factory wrapper invokes that CLI directly. Reusing it would
  therefore not satisfy program-design.md's no-network doctor boundary.
  No network-triggering reproduction was needed or performed.

Proposed scope adjustment, **not yet accepted**: doctor checks Graft dependency,
version, skill/launcher wiring and configured application paths offline;
structural freshness remains the explicit `graft check` review/CI gate. Doctor
would report that freshness was not assessed, rather than claim a current cache.
This requires amending task 3.1 and the doctor stale-navigation scenario/design.
An alternative is an upstream-supported offline CLI check before implementing
the original scope; bypassing the CLI through internal APIs is not assumed.

Implementation pauses for disposition under CLAUDE.md's instruction to stop for
unresolved architecture or contradictory requirements. No canonical specs were
changed, and nothing was committed, pushed or archived.


## Group 3 implementation evidence — 2026-09-13

Branch: `feat/factory-phase2-g3`. The user accepted offline Graft diagnosis on
2026-09-12 and requested a step-by-step HARNESS.md reference guide. This resolves
the preceding feasibility checkpoint. Tasks 3.1–3.3 are implemented; 3.4 remains
unchecked pending fresh maintainability review and independent verification.

### Delivered behavior and files

Added `.harness/factory/doctor.py` and `doctor_wiring.py`, exposed through
`factory doctor` and the existing global `--root` option. Diagnostics carry
stable category codes, severity, paths, explanations and remediation. Independent
categories continue after a failure; errors exit 1, healthy installations exit 0,
and invalid CLI arguments exit 2.

Doctor checks manifest schema/version/hash metadata, optional existing version
stamps, required directories/files, command references, Makefile target presence,
active protection-hook tool/event coverage, relevant executable permissions,
OpenSpec schema structure, effective Git ignore rules, configuration/exceptions,
Graft package/lock/installed versions, launcher/skill presence, application paths
and eval-case configuration. It does not compare customized file bytes to
upstream distribution hashes or require group 4's ownership state.

Only machine Git ignore inspection and a sanitized Node version probe execute.
Doctor refuses tool executables inside the inspected project, reads no
secret-environment files, invokes no Graft/project commands and performs no
network requests or source writes. Graft freshness is always explicitly deferred
to `.harness/bin/graft check`; missing/stale/malformed graph bytes alone do not
fail doctor and are never opened by doctor. OpenSpec behavioral validation and
full product verification remain separate checks.

Updated CLI dispatch, `cmd_check.sh` and the CI workflow to include offline doctor
in the full gate without recursion. Updated the legacy migration copy allowlist
and regenerated the 104-file distribution manifest. Template version remains
1.5.0; ownership/apply/update conversion remains group 4 work.

HARNESS.md now starts with six sequential steps: prepare the checkout, diagnose
installation health, agree on a change, implement a group, prepare navigation and
verify, then review/ship/continue. Existing runtime, navigation, Git and command
references remain available. The guide explains each step's output, human gates,
Graft upkeep/network behavior, doctor limits and the separate freshness gate.
Setup guidance was updated to match the new full-gate prerequisites.

New validation files are `.harness/tests/integration/test_doctor.py` and the
credential-free static eval `017-offline-doctor.yaml`; existing gate tests now
cover doctor's quiet failure propagation. Active delta/design/program-design and
tasks reflect the accepted offline boundary. No canonical specs were edited.

### Implementer validation and corrections

| Check | Observed local result |
|---|---|
| Final doctor filesystem/CLI suite | 52 passed; healthy/broken/config/permission/symlink/FIFO/offline/deferred-freshness fixtures, actual starter health, CLI root and status contracts |
| Doctor + gate + manifest targeted run before final tool-refusal additions | 90 passed |
| Migration and manifest regressions after copy-list correction | 93 passed |
| Factory Ruff lint/format and strict mypy | Passed for all 8 runtime modules |
| `make fmt` | Passed; starter has no application Python files to format |
| Starter `factory doctor` | Exit 0, zero installation errors; freshness not assessed |
| Graft structural build and separate check | Exit 0; accepted no-application disposition |
| `factory maintainability --verbose` | Exit 0; doctor modules 239/155 code lines; nonblocking warnings for existing migration script and 322-code-line doctor test module |
| `make evals` | 17/17 static cases passed; seven prompt cases not run |
| Manifest | Refreshed 104 entries; independently matched 103 file hashes, leaving `.env.template` unopened in the hash audit |
| `openspec validate factory-phase2 --strict` | Passed |
| `git diff --check` | Passed |

The first migration regression exposed that the legacy copier has its own runtime
allowlist: refreshing the manifest alone did not ship the new doctor imports.
Added both modules to that list; the real isolated Python 3.11 migration fixture
and the broader migration/manifest suite passed. The new static eval also needed
to select an available Python 3.12+ interpreter when the shell's python3 is older;
it uses the active interpreter, an installed python3.12, or the starter venv,
without provisioning dependencies. Failed sandbox uv-cache accesses were rerun
with approval for formatting, manifest refresh and Graft preparation.

### Remaining evidence and limitations

Fresh independent maintainability/verifier verdicts and their full `make check`
and `make harness-test` evidence are pending; none of the implementer results
above is represented as an independent verdict. An asynchronous question asks
for explicit authorization to run the two review agents, as required by this
session's delegation rule. Do not mark task 3.4 complete until those reviews
finish and any findings are resolved.

No remote CI execution, prompt/model evals, optional deep enrichment or visual
exports are claimed. Offline doctor deliberately does not assess Graft freshness
or authenticate upstream package contents. The starter has no application graph;
existing Graft integration fixtures remain the source of real graph coverage.
No commit, push, PR or archive operation was performed. Group 4 is unstarted.


### HARNESS reference layout correction — 2026-09-13

At the user's request, restored a compact Pipeline diagram and four-column
stage/command/output/gate table above the detailed walkthrough. Updated the
older summary's command mapping to the shipped factory workflow: `/explore`
records intent, `/crystallize` handles specs/design, DEEP uses `/shape-change`,
worktrees are optional, and fresh verification precedes human review/shipping.
The overview also distinguishes human shipping authorization, PR merge and
pre-apply archive approval. This is a documentation layout correction; the
pending independent group 3 reviews remain pending.

### Group 3 review corrections — 2026-09-13

Fixed both findings from human-triggered review. Hook validation now matches
explicit double-quoted project-variable paths (either the variable alone or the
whole path), retaining shell expansion semantics and rejecting single-quoted or
escaped variables. Eval validation accepts both literal `|` and folded `>` bodies
supported by the shipped runner, while rejecting empty bodies for either kind.

Added 13 regression cases for accepted/rejected hook quoting and static/prompt
block styles. Before the fixes, four cases reproduced the findings. Afterward,
the doctor and factory gate suites passed all 80 tests. Factory Ruff, formatting
checks and strict mypy passed; static evals passed 17/17 and `git diff --check`
passed. Refreshed the distribution manifest. Not covered: prompt/model evals
and fresh independent full-gate verification; the pending independent review
requirements above remain unchanged. No commit, push or PR was performed.

### Group 3 inline eval correction — 2026-09-13

The subsequent human review reproduced a valid inline `shell: true` body being
accepted by the eval runner and rejected by doctor. Doctor now accepts nonempty
inline static and prompt bodies as well as the existing literal/folded blocks.
Header parsing stays on the current line, so an empty body cannot consume the
following `why` field; whitespace-only inline values are also rejected.

Added six regression cases covering inline, empty and whitespace-only bodies for
both eval kinds. The doctor and factory gate suites passed 86 tests (exit 0).
`make fmt` and targeted runtime/test formatting passed; Graft preparation reported
`not applicable: no application sources configured` (exit 0). Refreshed the
104-file distribution manifest; `git diff --check` passed.

The user's instruction to fix both review findings authorizes obtaining the
pending independent maintainability and verifier evidence. Their results will
be recorded below before task 3.4 is marked complete. No commit, push or PR was
performed.

### Group 3 fresh independent maintainability review — 2026-09-13

A fresh-context reviewer received only the group identity and reviewer role,
discovered the diff including untracked files, and returned **PASS** with no
maintainability concerns requiring review. It compared the implementation with
accepted Code Shape and neighboring modules, finding the planned boundaries and
reuse of configuration/path and Graft application-scope validation intact.

`factory maintainability --verbose` passed: doctor modules contain 239 and 167
code lines. Nonblocking warnings cover the cohesive doctor tests (361 code lines)
and existing migration module (969, zero growth). `.harness/bin/graft check`
exited 0 with `not applicable: no application sources configured`. An initial
sandbox denial accessing uv's cache was resolved by an approved rerun. The
reviewer edited no files. Fresh behavioral verification follows separately.

### Group 3 fresh independent verification — 2026-09-13

A fresh-context verifier received only the group identity and verifier role,
confirmed `feat/factory-phase2-g3`, independently discovered the changed artifacts,
and returned **PASS** with no mismatches.

| Check | Independent observed result |
|---|---|
| `.harness/bin/graft check` | Exit 0; no application sources configured |
| `make check` | Exit 0; all seven gates passed |
| `make harness-test` | Exit 0; lint, formatting, types and 306 tests passed |
| `make evals` | Exit 0; 17/17 static cases passed |
| Standalone `factory doctor` | Exit 0; zero installation errors, freshness explicitly deferred |
| Manifest assertions | All 104 hashes match |
| `git diff --check` | Exit 0 |

Completed tasks 3.1–3.3 and applicable installation/maintainability scenarios hold.
Fixtures cover missing structure, malformed metadata/configuration, hook quoting
and activation, permissions, Git protections, exception validation, navigation
configuration, missing/stale graph deferral, inline/block eval bodies, CLI failure
status, source preservation and rejection of project executable shims. Existing
growth, migration, hook and navigation tests cover adjacent regression paths.

Not covered: seven prompt evals and remote CI execution. Group 4 ownership
baselines remain intentionally deferred. Initial sandbox cache failures and
pending approval requests were resolved through approved reruns. The verifier
edited no files.

These independent PASS verdicts supersede the earlier pending group 3 evidence
notes. Task 3.4 is complete. Only this report and the task checkbox were updated
after the final verdict to record evidence. Group 3 remains uncommitted for human
`/review`; no commit, push, PR or archive operation was performed. Group 4 remains
unstarted.

### P1 migration/doctor contract correction — 2026-09-14

User approved P1 separately; P2 command-preamble validation remains unchanged
and awaits approval. Migration now ships the required spike preamble, statusline,
eval runner and a downstream installation-health case, adds a missing evals
target, records upstream distribution metadata for copied files, and appends
secret/cache ignore rules with the environment-example exception last. Existing
project configuration, instructions, Makefile targets and recorded fingerprints
are preserved. Setup instructions order OpenSpec and Graft installation before
doctor/full checks. No ownership-format or adoption workflow redesign is included.

Two integration fixtures exercise actual migration and its copied doctor CLI:
a fresh project and one with custom configuration/instructions/Makefile/ignores.
Both failed before the correction and pass afterward. Only external OpenSpec and
Graft installation artifacts are supplied by the fixtures; migration output is
not repaired by hand. Repeated migration preserves manifest bytes. The ignore
fixture includes an existing example exception to cover rule ordering.

Observed validation: 156 targeted migration/doctor/gate tests passed;
make fmt, make manifest, make check, make harness-test (308 tests), and make evals
(18 static cases) passed. After the final ignore-order correction, all 70 migration
tests and test formatting passed. Git diff whitespace checks passed. uv cache
access required an approved sandbox escalation. No commit, push or PR was made.

Not covered: fresh dependency downloads in the migration fixtures, seven prompt
evals, remote CI, and fresh independent maintainability/verifier review of this
correction. Previous independent verdicts do not cover these new changes; obtain
fresh evidence after the separately approved P2 fix before final human review.

### P2 command-preamble correction — 2026-09-14

After separate user approval, replaced substring matching with recognition of
supported standalone preambles in doctor_wiring.py. Bash/sh fenced blocks and
standalone inline shell directives accept the exact script path (optionally
quoted), optional $ARGUMENTS and a trailing shell comment. HTML comments,
prose-only references, commented shell lines, wrong paths and shell wrappers
are rejected. This is a bounded structural check, not a shell interpreter;
HARNESS.md now documents the supported forms and customization boundary.

Added 20 integration cases: six accepted forms and fourteen inactive/unsupported
forms. Before the correction all fourteen rejection cases failed; afterward
all 176 doctor/migration/gate tests passed, including P1 migration coverage.
make fmt, make manifest, make check, make harness-test (328 tests), make evals
(18 static cases) and git diff --check passed. Graft check exited 0 with no
application sources configured. uv cache access required approved escalation.

Not covered: seven prompt evals, remote CI, arbitrary shell/Markdown syntax,
and fresh independent maintainability/verifier review. Task 3.4 remains pending
that fresh independent evidence for P1/P2; prior independent PASS verdicts do
not cover these corrections. No commit, push, PR or archive was performed.

### Three review findings and feasibility assessment — 2026-09-14

The user authorized fixing all three latest findings (called P1/P2/P3 in the
request; review priorities were P1/P2/P2) and assessing whether the complete
Phase 2 end state remains achievable.

What and why:

- P1: new ignore-file writes followed symlinks outside the target. Migration now
  validates ignore and legacy metadata destinations in CLI preflight and again
  at the library mutation boundary. Symlinks, directories and special files are
  rejected before installation writes. A committed-Git CLI fixture proves no
  migration branch is created and the external file stays unchanged.
- P2: completing a manifest with the current template version could disagree
  with preserved older stamps; creating a missing stamp could cause the inverse.
  The shared installation module validates all existing version sources and
  preserves their agreed installed baseline when completing either record.
  Conflicting/malformed records fail before writes. Copying missing files does
  not claim a full upgrade or advance existing fingerprints.
- P3: doctor checked block markers while the runner checked parsed content.
  Both now use the same pure stdlib eval parser, including required-content,
  kind and duplicate-field validation. Doctor does not import or execute the
  inspected project's runner. The runner retains its existing YAML-ish subset.

How and boundaries:

Introduced installation.py with its first real callers, moving metadata
completion out of the large legacy script. Group 4 will extend that planned
module with ownership state; no adoption/update engine was implemented here.
Introduced eval_config.py by extracting the runner's parser and sharing it with
doctor. Both dependencies are included in migration and manifest inventory.
Updated Code Shape, setup and eval-format documentation accordingly.

New regression coverage exercises fresh/customized installations with no version,
stamp-only, manifest-only and version-file baselines; copied doctor and eval CLIs;
repeat-migration metadata stability; unsafe ignore destinations; invalid and
conflicting versions; and parser agreement on inline/literal/folded fields.
The pre-fix focused batch produced 22 failures and 10 passes. After implementation,
the targeted doctor/migration/gate suite passed 206 tests; final additional CLI,
packaging and duplicate-field checks are included in the complete suite below.

The first full gate rejected growth in the existing migration test module.
Moved the cohesive installation fixtures into test_legacy_installation.py rather
than introducing a threshold exception. No behavioral coverage was removed.

Final observed validation:

| Check | Result |
|---|---|
| `make check` | PASS, all seven gates |
| `make harness-test` | PASS, factory lint/format/strict types and 361 tests |
| `make evals` | PASS, 18/18 static cases |
| Factory navigation build and check | Exit 0, no application sources configured |
| Manifest regeneration and hash verification | All 107 current hashes match |
| Changed eval runner/test lint and formatting | PASS |
| `git diff --check` | PASS |

uv cache access was sandbox-blocked and then approved. These are implementer
results, not fresh independent verdicts. No further runtime changes were made
after final verification; only this report and the task evidence note followed.

The [feasibility assessment](feasibility-assessment.md) identifies repeated
cross-component contract gaps and a bounded completion path: shared ownership,
explicit conflict outcomes, one demonstrated adopt/update round trip, then legacy
adapter equivalence and failure/recovery cases. The design remains technically
achievable under its conservative scope. Full Phase 2 readiness is not established:
the ownership/update/apply engine and its acceptance matrix remain group 4 work.

Not covered: seven prompt evals, remote CI, fresh dependency downloads in migration
fixtures, arbitrary YAML/shell syntax, adversarial concurrent filesystem mutation,
and fresh independent maintainability/verifier review. Group 3 task 3.4 remains
pending independent evidence; group 4 remains unstarted. No commit, push, PR or
archive was performed.

### OpenSpec schema review correction and feasibility reassessment — 2026-09-14

The user requested fixing the first review finding (called P1 in the request;
the review labeled it P2), explaining the change and reassessing final-state
feasibility after seven review rounds.

What/why: doctor previously accepted empty quoted values, comment-only values and
an empty schema followed by another key because its presence regex crossed lines.
It could report healthy schema wiring without a usable schema value.

How: check_openspec now extracts exactly one top-level schema declaration and
validates the documented inline name representation, with optional matching quotes
and trailing comments. It rejects empty/null/boolean values, duplicate declarations
and unsupported YAML forms with remediation. The stdlib/offline boundary remains;
no YAML dependency or inspected project code is executed. HARNESS.md and design.md
state that complete YAML validity and custom-schema resolution are outside this
structural check. The installed OpenSpec project's config source was inspected to
confirm its nonempty-string requirement.

Evidence: added 30 filesystem regression cases; before the fix, 23 negative cases
failed and seven supported forms passed. After the fix all 30 passed. Final
make check passed all seven gates, make harness-test passed factory lint/format/
strict typing and 391 tests, and make evals passed 18 static cases. Graft build
and check both exited 0 with no application sources configured. Changed-test
lint/format and git diff --check passed. make manifest refreshed 107 entries.
uv cache access was sandbox-blocked and then approved for these commands.

The updated feasibility assessment distinguishes conditional technical feasibility
from demonstrated readiness. It recommends a group 4 adopt/update/repeat checkpoint,
mixed-file preservation evidence, failure injection and legacy adapter equivalence.
Group 4 remains unimplemented; this correction does not prove its final state.

Not covered: seven prompt evals, remote CI, arbitrary YAML syntax, installed custom
schema resolution and fresh independent maintainability/verifier evidence. Task
3.4 remains unchecked. No commit, push, PR or archive was performed.


### Eighth review correction: FIFO manifest and verification audit — 2026-09-14

What/why: fixed the P2 hang where doctor rejected a FIFO manifest in one category
and then blocked reopening it in navigation. Moved the existing contained,
regular-file reader from doctor_wiring into config and reused it for doctor,
application_roots and configuration load/initialization. Removed doctor's
unreachable direct-execution import fallback; the factory launcher remains the
supported entry point. Updated the accepted module responsibility description.

How tested: the new public CLI regression failed before the fix with
TimeoutExpired after three seconds. Afterward all 21 cases passed across seven
input paths and FIFO/directory/dangling-symlink forms. Each asserts error exit,
category output and completion through the freshness diagnostic. The first full
gate rejected the enlarged test_doctor.py at 514 code lines; moved the cohesive
CLI regression matrix into test_doctor_cli.py, reusing the healthy fixture. No
threshold exception was added.

Final observed checks after the source/test changes:

- make check: all seven gates passed.
- make harness-test: factory lint, format and strict types passed; 412 tests passed.
- make evals: 18/18 static cases passed; seven prompt cases skipped.
- .harness/bin/graft check: exit 0, no application sources configured.
- make manifest: refreshed 107 entries, four runtime hashes changed.
- New CLI test lint/format checks passed.

uv-based commands initially failed on sandbox cache access and passed after
approved escalation. The accompanying feasibility assessment records concrete
workflow weaknesses: untracked files omitted by the review preamble, warning-only
unfinished-task handling at shipping, instruction-presence evals rather than
proof of independent execution, and incomplete public-CLI special-file coverage.
These workflow recommendations have not been silently implemented as new policy.

Not covered: prompt evals, remote CI, concurrent filesystem replacement, new
independent verifier/maintainability runs, or group 4 adoption/update behavior.
This is implementer verification and a source audit of the verifier definitions;
it is not a fresh independent verdict. Task 3.4 remains pending. No commit, push,
PR or archive was performed. Only report/task documentation followed these checks.

### Group 3 final independent verification and review — 2026-09-14

The user supplied the following reports from two fresh reviewer sessions
after the latest FIFO correction. Both reviewed group 3 on
feat/factory-phase2-g3.

- Independent verifier: PASS.
- Independent maintainability reviewer: PASS, no concerns.
- Human-requested /review: APPROVE after receiving both reports.

These reports supersede the earlier statements that independent evidence
was pending. Task 3.4 is complete. Group 4 remains unimplemented.

Coverage gaps: seven prompt evals, remote CI, and group 4 ownership behavior.
No files were edited or committed by either reviewer.

#### Independent verifier report

Verification — factory-phase2, group 3
Verdict: PASS
Branch matches feat/factory-phase2-g3.
Ran successfully (exit 0):
- Doctor via Python 3.12: zero installation errors; freshness explicitly deferred.
- .harness/bin/graft check: not applicable—no application sources configured.
- make check: all gates passed.
- make harness-test: lint, formatting, types and 412 tests passed.
- make evals: 18/18 static cases passed.
- Independent fixture assertions, all 107 manifest hashes, and git diff --check.
  Checked against tasks 3.1–3.3 and relevant scenarios → HOLDS. Covered malformed inputs, wiring, permissions, exceptions, offline/non-mutating behavior, starter health and packaging. Regression coverage included FIFO rejection, shared eval parsing, legacy version reconciliation and gate failure propagation.
  Mismatches: none found. Initial uv-cache restrictions were resolved through approved reruns. Direct invocation under older Python correctly failed with the runtime requirement.
  Not covered: seven prompt evals, remote CI, separate maintainability review and group 4 ownership behavior. Task 3.4 remains unchecked. No files edited or committed.

#### Independent maintainability report

PASS
No maintainability concerns requiring review.

### Fresh review cycle — 2026-09-15

Branch: feat/factory-phase2-g3. Task group: 3.

Started fresh independent maintainability and verification for the current tree,
including the report-handoff workflow edits made after the previous PASS reports.
Prior verdicts remain above as history. Current handoff: [verification-report.md](verification-report.md).

### Independent maintainability result — 2026-09-15

Branch: feat/factory-phase2-g3. Task group: 3.
Source: fresh maintainability subagent following its repository role instructions.

PASS

No maintainability concerns requiring review.

### Independent verifier result and packaging correction — 2026-09-15

Branch: feat/factory-phase2-g3. Task group: 3.
Source: fresh verifier subagent following its repository role instructions.

Verification — factory-phase2, group 3

Ran:
- Graft check: exit 0; no application sources configured.
- `make check`: exit 0; all gates passed.
- `make harness-test`: exit 0; lint/format/types and 412 tests passed.
- `make evals`: exit 0; 18 static cases passed; seven prompt cases skipped.
- Doctor under Python 3.12: exit 0; zero errors, freshness explicitly deferred.
- `git diff --check`: exit 0.
- Independent manifest hash assertion: exit 1.

Checked against:
- Tasks 3.1–3.3 and relevant doctor scenarios → HOLDS.
- Regression fixtures cover nonregular inputs, schema parsing, shared eval parsing, legacy version reconciliation, offline behavior and gate failure propagation.
- Task 3.4 refreshed packaging → MISMATCH.

Mismatches:
- `.harness/template-manifest.json:58` and `:73` contain stale hashes for `.claude/commands/dev-change.md` and `.claude/commands/review.md`. Refresh the manifest and verify hashes again.

Not covered: seven prompt evals, remote CI, group 4. Initial sandbox cache failures resolved through approved reruns. No files edited.

Verdict: FAIL.

Implementer correction: ran `make manifest`; initial uv-cache sandbox failure
was resolved by an approved rerun (exit 0). Regenerated 107 entries, updating
the two command fingerprints. No runtime or command instructions changed.
Maintainability PASS remains applicable; independent verification of the
corrected packaging is pending. The failed report above is retained as history.

### Final independent verifier rerun — 2026-09-15

Branch: feat/factory-phase2-g3. Task group: 3.
Source: new fresh verifier subagent following its repository role instructions.

Verification — factory-phase2, group 3

Ran:

- `.harness/bin/graft check`: exit 0; no application sources configured.
- `make check`: exit 0; all gates passed.
- `make harness-test`: exit 0; lint/format/types passed; 412 tests passed.
- `make evals`: exit 0; 18 static cases passed.
- Doctor under Python 3.12: exit 0; zero installation errors; freshness explicitly deferred.
- Independent manifest assertion: exit 0; all 107 fingerprints match.
- `git diff --check`: exit 0.

Checked against: tasks 3.1–3.4’s implementation and packaging claims and relevant installation scenarios → HOLDS. Confirmed the expected branch. Regression fixtures exercise malformed/nonregular inputs, schema and eval parsing, wiring, permissions, legacy version reconciliation, offline/non-mutating diagnosis, and gate failure propagation.

Mismatches: none found. Previous stale command fingerprints are corrected. Initial sandbox cache failures resolved through approved reruns. Direct invocation using older Python correctly rejected the unsupported interpreter.

Not covered: seven prompt evals, remote CI, group 4 ownership behavior. Graft structural build was not repeated because verification prohibits refreshing navigation; its check reports no applicable sources. Separate maintainability evidence remains the responsibility of that reviewer. No files edited or committed.

Verdict: PASS.

The final verifier PASS supersedes the packaging FAIL above. Maintainability
PASS remains applicable: only generated fingerprints and evidence changed after
that review. Task 3.4 remains complete. Group 4 is unstarted. Current reports
are in [verification-report.md](verification-report.md). Only evidence files
were updated after final verification. No commit, push or PR was performed.


### PR 20 CI dependency correction — 2026-09-15

Branch: feat/factory-phase2-g3. Task group: 3.

GitHub static evals failed because installation-health invokes uv, but the job
only installed Python. Added uv, Node 22, and make graft-install before static
evals, matching the installed-factory prerequisites already used by the tests
job. Added the workflow itself to its pull-request path filter.

Implementer validation: make evals passed 18 static cases; make manifest refreshed
107 entries (one workflow fingerprint changed); make check passed all seven gates.
Initial local uv-cache sandbox failures passed after approved reruns.
Not covered locally: a fresh GitHub runner, seven prompt evals, or a new independent
review of this CI-only correction. Previous independent reports cover the earlier
implementation; remote validation of this follow-up remains pending.
