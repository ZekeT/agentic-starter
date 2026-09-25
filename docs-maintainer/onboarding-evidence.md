# Onboarding evidence — 2026-09-25

Scope: v3.1 issue 05, based on source commit `83fcca9`, with the onboarding
changes on `docs/onboarding-verification`. The later v3.1b issue 08 owns the full
implement/review/fix/ship journey; this record does not claim that journey.

## Existing ordinary project and legacy starter

Run from this checkout:

```bash
uv run pytest .engineering/tests/integration/test_onboarding.py -o addopts='' -q
```

Both parameterized cases passed after the regression fix. Each creates a clean
committed target with a native unittest Makefile, package metadata, CI, OpenSpec
source and an OpenSpec command. Legacy setup uses the existing v2 fixture and a
project-owned check outside the managed region. Public `engineering adopt` or
`engineering migrate legacy-starter --target ...` preview leaves bytes unchanged;
apply preserves native content and all OpenSpec source/commands. Dependency
installation, doctor, native `make check` and `make engineering-check` succeed.
A deliberately broken native test then fails `make check`, confirming installation
did not replace it with an echo-only gate. Legacy retry leaves content unchanged.

Initially both tests failed: installed `engineering-check` ran a maintainer eval
which required `.engineering/template/files.json`, absent from adopted/upgraded
projects. The shared target now runs doctor and maintainability only; the separate
required maintainer `engineering-evals` target remains available. No failing gate
is skipped and native checks are unchanged.

Fixture boundary: network installers and dependency discovery use the existing
`template_toolchain` doubles. Engineering CLI, Git, filesystem changes, doctor,
maintainability and the native unittest process run normally. This is regression
coverage for the public command boundary, not live external dependency testing.

## Fresh application with real pinned setup

A disposable trial ran the documented commands with the real toolchain:

```bash
make template DEST=<canonical-trial-root>/fresh
# In fresh:
git init -b main
make setup
git add .
git commit -m "Initialize disposable application"
make setup
./engineering doctor
make check
make engineering-check
```

Every command passed. Added `src/total.py` and `tests/test_total.py` with the known
order total 125 + 250 = 375 cents, then ran `make fmt`, `make check` and
`make engineering-check`: all passed. Distribution manifest and installation
baseline bytes stayed identical; no `make manifest` was run in the application.
Migration implementation and `docs-maintainer/` were absent. Application roots
remained explicitly empty; this is not evidence of a configured Graft graph.

The first build attempt used the macOS `/var` symlink and was refused before
creation. Resolving the trial path to `/private/var` allowed generation; the
builder's path protection remained enforced. Setup emitted only expected warnings
for optional, uninstalled skills. Live pinned downloads/install commands completed;
this does not certify external services or future availability.

## Guided semantic trial on an arbitrary OpenSpec project

The disposable `merchant-exports` project starts from scenario D source files
without Engineering. It has real account/export Python code and unittest tests,
canonical account prose, a partially implemented export change, and a native
`make check`. The agent inspected the source prose, implementation and tests;
known authored scenario expectations were available, so this is a guided semantic
trial, not a blind model benchmark or production migration.

From the external Engineering checkout:

```bash
./engineering adopt <target>
./engineering adopt <target> --apply
# In target:
./engineering deps install --apply
./engineering doctor
make check
# Commit the reviewed infrastructure installation in this disposable repository.
make engineering-check
# Back in the external Engineering checkout:
./engineering migrate openspec-project --target <target> --plan
./engineering migrate openspec-project --target <target> --apply
./engineering migrate openspec-project --target <target> --finalize --plan
```

All commands passed. Actual required dependencies were installed, native tests
passed and adoption preserved source. Adoption copied this source checkout's
explicit `legacy_history = "snapshot"` configuration; inventory selected snapshot
preservation and retained original bytes in its workspace snapshot as well as Git.
This trial does not prove the git-only default for targets without an override.
The semantic proposal drops duplicate five-attempt access prose, retains the
merchant/delegate domain distinction and routes only unimplemented background
export delivery/retry/deduplication to upstream `/to-spec`. It preserves the
serializer, database-outbox decision, retry limit, tenant isolation and rejected
Kafka alternative. No approved Matt spec or implementation is fabricated.

The exact preview writes `docs/context/accounts.md` and
`.scratch/export-retries/migration-input.md`, deletes six inventoried OpenSpec
files and preserves application code/tests and installation. The user approved the corrected exact proposal. `--finalize --apply` then passed
real doctor, both native unittest cases and the explicit Graft NOT APPLICABLE
check. The two proposed documents were written and six OpenSpec source files
removed. Application code/tests and all retained snapshot files remained byte-identical.
An unchanged retry made no changes and preserved the validation receipt bytes.
Subsequent doctor, native `make check` and `make engineering-check` passed.

Human acceptance of the validated fixture outputs and temporary cleanup remain
pending; neither is inferred from approval to finalize. Snapshot artifacts are
retained. This records successful finalization, not accepted/closed migration.

Manifest SHA-256: `3a9c2fa3210db85ae7f35a6b9f04763d26fb50c450d660c557621e660c8f04a8`.
Recovery/source commit: `367a341e7af2bd216cc11393c0a84e2756b811fa`.

Local disposable evidence for this run is under `/private/var/folders/xg/_yzxmgmd0vjfvx5898tkw4100000gn/T/onboarding-05-epgy_jk6`:
`commands.log`, `merchant-exports/.engineering/migration-work/openspec/` and the
fresh application. Preparation/reconciliation scripts are `/tmp/onboarding-05-prepare.py`
`/tmp/onboarding-05-reconcile.py` and `/tmp/onboarding-05-finalize.py`. These paths are local trial evidence, not
consumer prerequisites or durable services. Retain or remove them explicitly after
review; normal application development does not depend on them.

## Coverage and limits

The existing six authored semantic fixtures exercise matching behavior, conflict,
decided active work, partial implementation, unresolved architecture and a
non-starter OpenSpec repository. Finalization and closure suites cover refusal,
rollback, retries, acceptance and retained/removed cleanup. Their authored manifests
and substituted target gates do not establish autonomous semantic judgment.

Authoritative branch check/review results are maintained under change `onboarding`
in ignored `.engineering/state/verification/`; use its current snapshot status
rather than treating this narrative as a verification attestation. Optional
authenticated model evals and remote template publication are not part of this
trial. Retained starter history was relocated without reinterpreting old tasks;
no production migration or external issue publication was performed.

## Review correction

Independent behavioral review identified an incorrect git-only claim in the trial
record and semantic plan. The user directed correction to the observed snapshot
policy. The agent corrected both descriptions and regenerated the exact preview;
the digest above supersedes the earlier proposal. No target configuration was
changed. The human then approved this corrected proposal before the finalization
run recorded above. The initial review snapshot became stale when the correction
changed its inputs; it is not reused as passing authoritative proof.
