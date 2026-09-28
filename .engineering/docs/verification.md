# Reusable independent verification

Build, Verify, Accept and Publish are separate responsibilities. A local commit
is not proof or human acceptance. After implementation, hand off automatically to
fresh independent reviewers when supported. Review obtains missing evidence and
consumes current evidence. [Publication](publication.md) reuses current proof
without repeating semantic review or authoritative checks.

## Prepare the intended change

Discover the complete proposed PR scope against the comparison base, including
intended staged, unstaged and new files. Include requirement documents in tracked
context or explicit inputs when their bytes matter. Do not reduce scope just to
pass. Inspect check commands and version probes before running them: these are
explicit project-owned executables, not data downloaded by the evidence tool.

Keep plans, reports and records under ignored local
`.engineering/state/verification/`. Example `plan.json`:

```json
{
  "base": "main",
  "requirement": "The agreed request, or a ticket/spec pointer",
  "paths": ["src/example.py", "tests/test_example.py"],
  "checks": [["make", "check"]],
  "tools": [["python3", "--version"], ["uv", "--version"]],
  "inputs": [],
  "tier": "ordinary",
  "tier_reason": "Why this review tier fits the change"
}
```

Use exact paths including deletions, not directory/glob selectors. Commands are
argument arrays, without implicit shell interpolation. List actual relevant
runtimes/check tools in `tools`; status runs those read-only version probes, not
the suite. `inputs` names additional ignored non-secret files influencing results.
All tracked configuration/locks and ignored managed dependency evidence are
included automatically. A URL alone is not a requirement-content fingerprint.
Reviewers independently assess plan completeness and the declared review tier.

Planning reads the installation role, `maintainer` or `consumer`, from the
proposed `.engineering/state/install.json` in the verified content: the
committed state, or working bytes only when that path is in the plan's paths.
The stricter of the base and proposed roles applies (`maintainer` is stricter),
so a role change takes effect only after it merges.
An out-of-scope working edit never supplies or changes the role; `status`,
`check` and `record` re-validate it. Generation and adoption record
`consumer`; the maintainer checkout records `maintainer`. No role is ever
assumed: when it is missing, `prepare` fails INCOMPLETE and names the fix. From
a starter checkout, preview `engineering update <project>` and apply it; the
update records the role as an Engineering migration. An unknown role also fails.

Required checks follow the role and each path's ownership in the proposed
`.engineering/manifest.json` (the base manifest too, so dropping an entry
cannot lower them), never which Make targets exist:

| Changed path | Role | Required in addition to `make check` |
|---|---|---|
| Project configuration (`preserve` entries) | both | `make engineering-check` |
| Integration sections and hooks (`section`, `hooks`) | both | `make engineering-check` |
| `.engineering/manifest.json`, `.engineering/state/install.json` | consumer | `make engineering-check` |
| `.engineering/manifest.json`, `.engineering/state/install.json` | maintainer | `make engineering-check`, `make engineering-test`, `make engineering-evals` |
| Managed implementation (`file` entries) | maintainer | `make engineering-test`, `make engineering-evals` |
| Starter tooling under `.engineering/` `template/`, `tests/`, `evals/`, `scripts/`, `migrations/` | maintainer | `make engineering-test`, `make engineering-evals` |
| Managed implementation edited or deleted | consumer | Rejected: INCOMPLETE, never PASS |
| Any other path | both | nothing further |

Any consumer change to a path owned as `file` in the base or proposed manifest
is rejected, whatever the manifest digests say: the manifest is proposed content
too, so it cannot vouch for the file. Restore the file and obtain changes with
`engineering update <project>` from a starter checkout, or propose them
upstream. A consumer starter-update PR is therefore not yet verifiable by this
workflow. In the maintainer checkout the installation metadata is maintainer
source as well: the manifest is the ownership contract every consumer receives.
Invalid project configuration fails preparation, naming the file. The recorded role is
trusted and fails closed: a consumer declaring `maintainer` must run suites it
lacks; a maintainer checkout proposing `consumer` keeps maintainer requirements
until that change merges. A role change is visible in the diff. Configured application roots require
`.engineering/bin/graft check` while `[navigation] provider = "graft"` (never
with `none`). Add project-specific checks as needed.
Formatting and graph building remain implementer preparation. Probes time out
after 15 seconds, each check after 15 minutes. uv stays offline with interpreter
downloads disabled.

```bash
./engineering verify prepare --change example --plan .engineering/state/verification/plan.json
./engineering verify status --change example
```

Prepare returns a snapshot and existing current proof or an INCOMPLETE handoff.
It does not run checks/reviewers. Status exits zero only for current complete
PASS; missing, stale, malformed or failed evidence is nonzero. Prepare and record
exit zero when bookkeeping succeeds even if proof is incomplete; inspect their
JSON status. No result grants acceptance or publication authorization.

Snapshots include tracked context, explicit inputs, working bytes/executable bits,
comparison base/tip, plan and tool-version outputs. Content-preserving commits
retain proof; changed inputs do not. Base movement is assessed locally without
fetching. Elapsed time and failed transport alone do not invalidate proof.

Verification always prepares an isolated temporary checkout under ignored local
state. The JSON `checkout` path identifies the tree all reviewers inspect and
where `verify check` runs commands. It contains comparison-base context plus
intended working bytes and executable modes (committed, staged, unstaged and new
files, including deletions). A path's working bytes are the proposed final version;
index-only intermediate versions are not a second version of the PR. Unrelated
local edits and new files are excluded without stash, commit or workspace writes.
Committed changes outside `paths` fail preparation: they cannot be omitted from
the proposed PR. Include each side of a rename.

Version probes also run in isolation. Explicit `inputs` and installed dependency
evidence are copied and fingerprinted; tracked explicit inputs must be in `paths`.
Ignored environments, installed tool directories and caches are not silently
copied or linked from the working tree. Checks needing additional regular files
must declare them as inputs. Missing tools/dependencies or preparation failures
leave proof INCOMPLETE, never PASS. Install/prepare dependencies explicitly before
verification as needed; no command installs them on your behalf. This is content
isolation, not a security sandbox: approved project executables can access the
machine and absolute paths. Inspect commands and probes accordingly.

For the generated Python application, the implementer prepares the reported
checkout with `uv sync --offline --all-extras` before handing it to reviewers.
This installs locked development tools from the existing cache; `uv run` alone
does not select optional development dependencies in a new environment. If the
cache is missing packages, explicit dependency installation is needed before
the offline gate can pass. Declare the installed Matt skill outputs and required
Graft files as inputs for doctor/navigation. Maintainer Graft integration tests
need the full installed runtime, not just its package metadata. Do not copy a
populated working-tree Python environment or treat a missing executable as
successful verification.

The isolated checkout remains available for independent inspection and check
artifacts. Source mutations there invalidate proof; prepare again to build a
fresh checkout and clear reports. Old ignored checkouts can be removed when no
review is using them. Missing local checkouts require preparing fresh evidence.
Symlinks, submodules/nonregular inputs, unmerged entries and secret paths fail
closed; the public `.env.template` is permitted. Secret/environment values are
not fingerprinted. Disclose material external/environment gaps; this is not a
hermetic snapshot of the machine or external services.

## Review tiers

Each plan declares a review tier with a reason. The tier decides the required
reviewer roles; it never adds or removes checks.

| Tier | Required reports | Sessions |
|---|---|---|
| `documentation` | behavioral | one fresh session |
| `ordinary` | maintainability, behavioral | one fresh session may file both |
| `sensitive` | maintainability, behavioral, security | a separate fresh session per role |

Preparation computes a tier floor from the changed paths and rejects a plan that
declares less, naming each path and the rule that set the floor. A mixed change
takes the highest path floor. Declare a higher tier with a reason when risk the
paths cannot show applies, such as authentication, secrets or untrusted input.
Starter-owned rules always apply:

- `sensitive`: dependency manifests and locks (`pyproject.toml`, `uv.lock`,
  `package*.json`, `.engineering/dependencies.toml`), `.claude/settings*.json`,
  hooks, `.github/workflows/**`, `Makefile` and Engineering launchers. In the
  maintainer checkout also the dependency, skill-installation, apply,
  transaction, update, migration, publication and verification modules.
- `ordinary`: agent policy is never documentation: `CLAUDE.md`, `AGENTS.md`,
  `.claude/**` including skills, `REVIEW.md`, `ENGINEERING.md`, Engineering docs
  and agent docs. Every other path is `ordinary` until project review settings
  name documentation paths.

A combined ordinary session files two separate reports, one per role, each with
its own verdict and the same `reviewer` identifier. Reports sharing a `reviewer`
identifier across roles are rejected for `sensitive` changes, both when recorded
and in status. The evidence record stores the floor, per-tier paths with their
rules, required checks and roles. `verify status` reports the tier, its reason,
the floor, required and missing roles, and any reviewer covering several roles.
Status and publication recompute the floor for the current scope, so evidence
whose tier falls below it cannot pass or ship. Records from before review tiers
are unsupported: prepare again; no tier is inferred for old evidence.

## Obtain fresh evidence

Fresh reviewers for the roles the tier requires receive only the
branch/request/spec/ticket pointer. They independently discover requirements,
actual scope and prepared plan; no implementer reasoning/self-review is handed
over. The plan is a discoverable scope/execution contract, not proof.

Capture the snapshot and `checkout` path before inspecting or running anything.
Inspect source and diffs inside that checkout, including its uncommitted/new
files relative to the comparison base. Invoke evidence commands from the original
repository, where the plan and records live. The behavioral
verifier executes required checks once through:

```bash
./engineering verify check --change example --snapshot <prepared-token>
```

This records argv, stdout, stderr and exit codes, clearing old check and behavioral
proof first so interruption cannot leave an old PASS. Source mutations prevent
current proof. Avoid secrets in commands/reports and inspect output before sharing.

Each reviewer supplies a report in ignored local storage:

```json
{
  "snapshot": "identity captured before review",
  "role": "behavioral",
  "reviewer": "fresh reviewer session identifier",
  "independent": true,
  "verdict": "PASS",
  "summary": "Observed behavior and relevant coverage",
  "findings": [],
  "coverage_gaps": ["Explicitly state what remains unverified"]
}
```

Roles are `maintainability`, `behavioral`, `security`; verdicts are `PASS`, `FAIL`
or `CONCERNS`. Findings are readable strings with evidence/references. Behavioral
PASS requires successful recorded authoritative checks. Non-PASS reports prevent
PASS; missing roles the tier requires remain INCOMPLETE.

```bash
./engineering verify record --change example --report .engineering/state/verification/report.json
./engineering verify status --change example
```

Serialize evidence writes: run checks before recording the behavioral report and
record reports one at a time. Never edit stored records manually. If inputs change,
prepare again and obtain fresh proof; never relabel old findings with a new token.
Changed inputs clear active reports and checks. Preparation saves the previous
record in the new checkout's sibling `previous.json`, exposed as
`previous_evidence`. This is historical reference only, never current proof.

## Interpret proof honestly

The tool validates freshness and reviewer attestations, but does not authenticate
a model/session, launch a runtime-specific agent, or prove that an asserted
independent review occurred. Actual independent sessions and runtime instructions
provide that boundary. Never fabricate reports from implementer self-review.
If fresh reviewers are unavailable, leave INCOMPLETE evidence and hand off the
branch/request pointer, plan and missing roles to a fresh session. Shipping waits.

Before reuse, compare the plan with the actual request, scope and applicable
checks. PASS for the wrong requirement or omitted relevant input is insufficient.
Human acceptance remains separate. Put a concise scope/evidence/gaps summary in
the eventual PR, not local bookkeeping. Another checkout without records
regenerates verification. This is not a ticket tracker or workflow database.

## Review corrections

After human-directed fixes, prepare the same change with its current complete
scope. The previous evidence reference preserves the old snapshot, reports,
checks and checkout pointer for comparison, including findings still unresolved.
Never edit history or relabel an old report with the current token. Missing or
untrustworthy history requires fresh review of the relevant areas.

Fresh independent reviewers compare the prior and current proposed content and
inspect the fix and affected behavior. In each new report's `summary`, identify
resolved and remaining finding evidence, the correction inspected, and any retained
unchanged-area evidence by previous record path, snapshot and role. Explain why
that coverage remains applicable, including relevant dependencies and call sites;
unchanged file bytes alone do not prove unaffected behavior. Use `coverage_gaps`
for limits. Each required role supplies a current independent attestation; a
reviewer can incorporate justified prior coverage without repeating that inspection.
Changed requirements, scope, architecture, check configuration or tools require
broader inspection as appropriate. Historical failures cannot be ignored: explain
resolution or retain the finding and a non-PASS verdict.

The behavioral reviewer reruns `verify check` for the current snapshot after code
fixes, then records observed behavior. Old checks cannot satisfy the new snapshot.
The tool validates freshness, not the semantic validity of retention justifications
or human fix authorization. Follow REVIEW.md for human direction, the two-attempt
pause and settled-decision escalation. Present the corrected scope and evidence
for human acceptance; history does not transfer acceptance to changed content.
