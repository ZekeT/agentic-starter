# Reusable independent verification

Build, Verify, Accept and Publish are separate responsibilities. A local commit
is not proof or human acceptance. After implementation, hand off automatically to
fresh independent reviewers when supported. Review obtains missing evidence and
consumes current evidence. Ship still runs its existing final check until the
publishing slice changes that policy.

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
  "security_required": false,
  "security_reason": "Explain why security review is or is not applicable"
}
```

Use exact paths including deletions, not directory/glob selectors. Commands are
argument arrays, without implicit shell interpolation. List actual relevant
runtimes/check tools in `tools`; status runs those read-only version probes, not
the suite. `inputs` names additional ignored non-secret files influencing results.
All tracked configuration/locks and ignored managed dependency evidence are
included automatically. A URL alone is not a requirement-content fingerprint.
Reviewers independently assess plan completeness and security classification.

`make check` is mandatory. Starter tooling scope also requires `make
engineering-test` and `make engineering-evals`; configured application roots
require `.engineering/bin/graft check`. Add project-specific checks as needed.
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

The isolated checkout remains available for independent inspection and check
artifacts. Source mutations there invalidate proof; prepare again to build a
fresh checkout and clear reports. Old ignored checkouts can be removed when no
review is using them. Missing local checkouts require preparing fresh evidence.
Symlinks, submodules/nonregular inputs, unmerged entries and secret paths fail
closed; the public `.env.template` is permitted. Secret/environment values are
not fingerprinted. Disclose material external/environment gaps; this is not a
hermetic snapshot of the machine or external services.

## Obtain fresh evidence

Fresh maintainability, behavioral and applicable security reviewers receive only
the branch/request/spec/ticket pointer. They independently discover requirements,
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
PASS; required missing roles remain INCOMPLETE.

```bash
./engineering verify record --change example --report .engineering/state/verification/report.json
./engineering verify status --change example
```

Serialize evidence writes: run checks before recording the behavioral report and
record reports one at a time. Never edit stored records manually. If inputs change,
prepare again and obtain fresh proof; never relabel old findings with a new token.
Incremental fix review is a later slice; changed inputs currently clear all reports.

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
