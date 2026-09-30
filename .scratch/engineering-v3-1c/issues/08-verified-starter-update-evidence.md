# 08: Verify consumer starter-update output against its source

**Spec:** Follow-up from the ticket 03 security review (2026-09-27); not part of the [spec](../spec.md) slices.

**What to build:** A consumer pull request that applies `./engineering update`
output becomes verifiable. Today ticket 03 rejects every consumer change to a
`file`-mode managed path, because the proposed `.engineering/manifest.json` is
consumer-controlled and cannot vouch for the bytes it describes. Accept such a
change only when the verification plan names the starter source checkout as an
explicit input and the proposed bytes (and removals) match that source's
manifest, not the proposed one.

**Blocked by:** 03 (merged), 10 (Make generation and update agree on the distributed file set).

**Status:** implemented with authorized security correction — current independent evidence is tracked under `v3-1c-08`; human acceptance/publication outstanding

## Design question

What identifies a trustworthy starter source: a local checkout path, a pinned
commit or tag of the starter repository, or a signed/released manifest? How is
it fingerprinted in the plan so reviewers see which source vouched for the
update, and how does a stale or altered source fail closed?

## Decisions (triage 2026-09-28, human-approved)

- **Source of truth:** a pinned starter commit or tag named in the plan, fetched
  and compared — not a local checkout path (trusts whatever is on disk) and not a
  signed release manifest (no release signing exists yet). The pinned source is
  fingerprinted in the evidence so reviewers see which source vouched for the
  update; an unreachable, moved or altered source fails closed (INCOMPLETE).
- **Split:** the generation-versus-update distributed file-set mismatch moved to
  ticket 10, which blocks this ticket.
- **Priority:** after slice B (review tiers), ticket 06 and ticket 09.

## Acceptance ideas

- [x] The plan names a pinned starter commit or tag as the update source; without it, a managed-file change stays rejected (INCOMPLETE).
- [x] Proposed managed bytes and removals are compared against the source's manifest and distribution, never the proposed manifest. — Includes the authorized Git-environment isolation correction described below.
- [x] A forged proposed manifest digest or a dropped entry is still rejected.
- [x] An update PR produced by `./engineering update --apply` from that source prepares a valid plan requiring `make check` and `make engineering-check`.
- [x] Documentation replaces "consumer starter-update PRs are not yet verifiable" with the supported route.

## Implementation preparation (2026-09-30)

Branch `feat/v3-1c-08-verified-starter-update` starts at `origin/main` merge
commit `86c3df2`, which includes ticket 10 / PR #43. Existing unrelated local
files are preserved. Ticket 09 remains outstanding; this request selects 08.

Inspected verification planning, snapshot identity, checkout isolation, ownership
classification and the shared distribution resolver. Proposed test seams are
`verify prepare/status/check` and an end-to-end `engineering update --apply`
case. The human confirmed those seams before implementation.
This preparation entry predates implementation; the handoff below describes
the resulting scope.

## Implementation and review handoff

Branch: `feat/v3-1c-08-verified-starter-update`, based on merged ticket 10
at `86c3df2`. The human confirmed command-level test seams on 2026-09-30.

Plans optionally name `starter_source` with a repository URL, full commit SHA
and optional `refs/tags/` guard. Verification fetches Git objects, validates the
source distribution with the shared resolver, and compares proposed managed
bytes, executable modes, removals and manifest against that source. The
repository, revision and manifest fingerprint participate in evidence freshness
and carry-forward. Source failure blocks prepare and reuse. Source-backed
updates require sensitive review and project/Engineering health checks.

The command regressions cover an applied update with additions and removals,
forged and dropped manifest entries, bytes/modes, omitted paths, changed tags,
unavailable sources, invalid source distributions and mapped payload files.
Targeted validation passed the first 25 cases plus the two mapping/tag-object
cases; typechecking and the maintainability gate passed. Existing verification
regressions and the authoritative full suite are recorded in the verification
evidence.
The acceptance checkboxes describe implemented behavior supported by these
regressions; they are not human acceptance or independent certification.

Independent verification: change `v3-1c-08`, plan
`.engineering/state/verification/v3-1c-08-plan.json`. Run:

```bash
./engineering verify status --change v3-1c-08
```

That record is the current authority for the complete proposed snapshot, all
required checks and independent behavioral, maintainability and security
reports. Reviewers inspect the prepared checkout and this ticket. Any missing
or failed proof remains explicit in that record; a local commit is not proof.
Human review, publication and merge remain separate and outstanding.

Usage and the trust boundary are documented in
[the verification guide](../../../.engineering/docs/verification.md#verify-a-consumer-starter-update).
The approved source choice is an explicit review decision; this does not add
release signing. Ticket 09's broader verification hardening remains separate.

### Independent review and correction handoff (2026-09-30)

Implementation head `d3d2faa`, snapshot
`0559436d87cb34e043ff51390bbffd15881086cc4580387cd46b4d242fe2f085`:
maintainability PASS, security FAIL, behavioral CONCERNS. The recorded overall
result is FAIL. Reports are stored under `.engineering/state/verification/` as
`v3-1c-08-maintainability-report.json`, `v3-1c-08-security-review.json` and
`v3-1c-08-behavioral-review.json`.

**Blocking security finding (P1):** fetching isolates Git's environment, but
`verification_source.py` then calls `verification_git.baseline_content`, whose
Git readers inherit `GIT_DIR` and replacement refs. The reviewer reproduced
substitution of local bytes while the evidence still named the genuine fetched
commit. This violates the source-authority requirement. Recommended correction:
use the isolated environment for every fetched-source Git read (including batch
`cat-file`), explicitly disable replacement objects, and add an integration
regression. Human direction was requested under REVIEW.md before editing.

The authoritative run passed `make check`, `make engineering-check`, and
13 static evals (five optional prompt cases skipped). `make engineering-test`
recorded 513 passed and 27 fixture setup errors in 854.40 seconds because the
sandbox denied localhost socket binding. The independent verifier reran those
27 update cases with the required execution permission; all passed in 93.97
seconds. That supplemental result does not replace the recorded failed gate.
After correction, run full authoritative verification with localhost fixture
access and obtain current independent reports.

This tracking update follows review and changes snapshot identity. The reports
above remain evidence for `d3d2faa`, not certification of this later tracking
snapshot. Preparing the correction must preserve those reports as historical
evidence; never relabel them. Source code is unchanged since the reviewed head.
Human acceptance, publication and merge remain outstanding.

### Authorized security correction (2026-09-30)

The human authorized the recommended fix and fresh verification. Fetching, tree
reads and batch blob reads now share the isolated Git environment. Inherited
`GIT_*` overrides and global/system Git configuration are excluded, and
`GIT_NO_REPLACE_OBJECTS=1` explicitly disables replacement interpretation. The
shared reader also applies those safeguards to verification/publication baseline
objects. The fetch transport restrictions remain in force.

The new command-level regression first reproduced successful preparation of a
substituted local distribution while evidence named the genuine remote pin.
The correction rejects that proposal against the actual pinned source manifest.
Cases cover both commit replacement and individual blob replacement with an
inherited `GIT_DIR`. This follows the already agreed command-level test seams.

The current complete scope is prepared under the same plan/change. Independent
reviewers compare the correction against the prior findings; current reports
and checks live in the evidence record and historical reports remain preserved.
The behavioral verifier must run the full gate with permission for localhost
Git fixtures. The earlier failed sandbox run is not reused as a passing gate.
Consult `./engineering verify status --change v3-1c-08` for the current outcome.
This tracking entry is included before verification so reporting its result does
not require a later source edit. Human acceptance, publication and merge remain
separate and outstanding.
