# Complete greenfield journey — 2026-09-25

Scope: v3.1b issue 08, based on `92d7e3e` with the changes on
`docs/complete-greenfield-journey`. This records observations, not acceptance or
publication of the Engineering branch. Current branch verification belongs to
change `complete-journey` in ignored `.engineering/state/verification/`.

## Accepted publication scope — 2026-09-26

The human approved deferring the unfinished live correction, independent
reverification and publication handoff, retaining that limitation in the PR, and
obtaining fresh verification before shipping. See the
[spec acceptance revision](../.scratch/engineering-v3-1b/spec.md#acceptance-revision--2026-09-26).
The observed trial below is unchanged: its test-category finding is unresolved,
and scripted fixtures do not establish completion of the deferred live steps.
This is a revision to this slice's acceptance scope, not a change to runtime
verification or publication safeguards. The ticket retains deferred follow-up.

## Repeatable command integration

```bash
uv run pytest .engineering/tests/integration/test_greenfield_journey.py -o addopts='' -q
```

The assembled case generates a consumer directory, initializes Git, runs setup,
implements a runnable greeting and commits it locally. It prepares isolated
verification while a README has different staged and working edits. The isolated
README equals the baseline; both owner versions survive correction and publishing.

The ordinary generated `make check` runs after implementation and after a scripted
whitespace correction. Changed content reports STALE; repreparation retains the
old evidence as history and requires current reports/checks. The correction stays
uncommitted until the fixture publishes the accepted scope. A rejecting local
bare-remote hook makes the first push fail after the correction commit. Removing
only that deliberate fixture failure and retrying preserves the commit, original
implementation parent, evidence bytes and each snapshot's single gate invocation.
A later retry reuses the fake PR receipt. The published README is the baseline.
Manifest and installation baseline bytes remain identical throughout; neither
consumer manifest regeneration nor migration scaffolding is involved.

This is a command integration test, not an autonomous agent benchmark. Engineering,
Git, the filesystem and Python application checks execute normally. Existing
`template_toolchain` doubles replace external installers/discovery; the fake
hosting adapter writes a local receipt and returns an `.invalid` URL. Reviewer
reports and review/authorization inputs are authored fixtures, clearly labelled
as such. They prove protocol consumption and recovery, not human intent or actual
independent review. The separate live trial below supplies actual reviewer execution.

## Live generated application

Local artifacts: `/private/tmp/journey-08-e47xzon4/`, including `commands.jsonl`,
`greeting-app/` and its ignored `.engineering/state/verification/` reports and
isolated checkouts. The preparation script is `/private/tmp/journey-08-setup.py`.
These temporary paths support this run only; they are not consumer dependencies.

The trial used the real pinned setup and toolchain:

```bash
make template DEST=/private/tmp/journey-08-e47xzon4/greeting-app
# In the generated directory:
git init -b main
make setup
git add .
git commit -m "Initialize disposable greeting application"
make check
git switch -c feat/greeting
# Implement .scratch/greeting.md using public subprocess tests.
uv run pytest tests/test_greeting.py -o addopts= -q
make fmt
uv run mypy src
uv run python -m src.greeting Ada
```

Setup and the baseline gate passed. Public tests first failed with no greeting
module, then both passed after implementation. The command printed `Hello, Ada!`
with a newline. The request preserves spelling/punctuation and delegates missing
or extra argument diagnostics to argparse. Whitespace normalization is explicitly
outside the first slice; `"  Ada  "` therefore printed `Hello,   Ada  !`.
The application and request were committed locally; unrelated staged/working
README notes stayed outside the proposed scope.

Prepared change `greeting` initially reported INCOMPLETE with no reviews or checks.
The first preparation rejected an explicit input that was already tracked in the
baseline (`install.json`); removing that redundant input restored a valid complete
scope. No gate or safety check was bypassed. The initial snapshot was
`7e11ccecb4986aed5eda42f08f205349581df7ed535106dbae571172db2263cb`.

Fresh agents `/root/trial_standards` and `/root/trial_behavior` received only the
branch/request pointer and reconstructed requirements and prepared scope. The
behavioral verifier's first gate could not spawn ruff: the isolated checkout had
no optional Python development tools installed. The implementer explicitly ran
`uv sync --offline --all-extras` in that checkout from the existing locked cache;
the verifier reran `verify check` for the unchanged snapshot. All seven stages
passed. The guide now documents this prerequisite. Manual independent probes also
confirmed Unicode/punctuation, missing/extra argument diagnostics and literal
whitespace preservation. No application behavior defect was found.

The maintainability reviewer identified an actual test-category violation:
subprocess tests lacked integration/e2e markers and category placement, so fast
suite selection would still include them. Its CONCERNS report was recorded
alongside behavioral PASS; overall proof correctly remained FAIL. The human was
shown the finding and asked to direct a bounded correction to
`tests/integration/` plus the integration marker, preserving greeting behavior.
Those live steps remain unperformed and are now explicitly deferred under the
2026-09-26 acceptance revision.

## Assembled policy and brownfield boundaries

The entry guides now lead from generation to `/implement → /review → /ship`,
observable output, findings, bounded fixes, fresh-session fallback and recovery.
Protocol and maintainer detail follows that journey or is linked from it. Existing
review/ship commands and reviewer definitions retain their settled responsibilities;
pinned upstream skills remain unchanged.

`011-complete-journey.yaml` checks entry-guide ordering and agreement with the
existing verification/publication instructions. Existing evals cover local commit
authorization, actual independent reports, isolation, human direction, settled
decisions and publication retries. These are static consistency checks. The
optional authenticated prompt evals, including the settled-decision scenario,
are not run or claimed as model behavior evidence.

The migration guidance remains external to fresh applications. Adoption, legacy
upgrade and semantic finalization retain the onboarding routes from
[onboarding evidence](onboarding-evidence.md). Existing template and migration
closure suites exercise external access, explicit acceptance, cleanup pending,
removal/retention, changed-artifact protection and safe retries. This ticket adds
no migration runtime, deletes no existing installation artifacts and does not
claim acceptance/closure of the earlier onboarding trial.

## Maintainer verification preparation

The initial independent branch run passed `make check` and all 11 static evals
(5 optional prompt cases skipped). `make engineering-test` reported 302 passed
and 15 failed: the Graft integration cases require the actual installed runtime,
but the first plan declared only its package metadata, sufficient for doctor.
The new journey integration case passed. The full regular installed Graft runtime
was subsequently declared; that independent rerun passed all 317 tests, all seven
ordinary check stages and 11 static evals. This
is an explicit preparation correction, not a test bypass; the failed run remains
historical evidence. Consult `complete-journey` for current authoritative results.

## Limits

The live greeting is deliberately tiny, with navigation roots explicitly empty;
no configured Graft graph is claimed. It uses fresh sub-agent sessions under this
runtime, not authenticated prompt evals or Claude hook execution. Real provider
authentication, external push/PR availability, production applications and every
possible model response remain unverified. Fake hosting coverage is local only;
no real test PR or remote template was published. Local commits, successful checks
and this narrative do not grant human acceptance or publication authorization.
