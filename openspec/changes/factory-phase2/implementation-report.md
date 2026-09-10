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
