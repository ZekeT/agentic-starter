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
