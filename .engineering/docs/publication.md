# Publish accepted content

The daily loop is `/implement` → `/review` → `/ship`. Implementation can commit
locally. Review obtains independent proof and presents behavior, scope, findings,
checks and gaps. After that presentation, `/ship` accepts the unchanged scope and
authorizes remaining scoped commits, push and actual PR/MR creation. Missing
review is not supplied by invoking ship. Narrower requests limit these actions;
merge and force-push require separate authorization.

Publication consumes current verification instead of repeating semantic review or
`make check`. Content-preserving commits retain evidence. Missing/stale proof goes
back to verification; changed acceptance scope or unresolved blockers goes back
to review. Hooks are enforced. Hook mutations stop publication for reassessment.
Unrelated working and staged changes remain in place.

## Record the presented review

After presenting the current acceptance summary, record it in ignored local
verification storage with `engineering publish review`. This is an attestation
that the presentation occurred, not human acceptance or an authentication system.
Never synthesize it merely because the human invoked ship. The snapshot is the
identity actually inspected and presented, not a newly obtained replacement.

Example `.engineering/state/verification/acceptance.json`:

```json
{
  "snapshot": "snapshot-from-current-verification",
  "summary": "Explain behavior, requirement coverage, consequences and risks.",
  "blockers": [],
  "branch": "feature/example",
  "remote": "origin",
  "remote_url": "https://github.com/owner/project.git",
  "base": "main",
  "provider": "github",
  "title": "feat: add the accepted behavior"
}
```

Use the exact configured push URL. `base` names the provider's target branch;
its remote tip must match the verified comparison tip. Preflight contacts the
remote read-only without silently fetching or changing proof. Reviewers determine
whether findings are blockers; preference-only alternatives remain non-blocking.
Store unresolved material findings in `blockers`, and present a fresh summary
after authorized corrections and reverification.

```bash
./engineering publish review --change example --plan .engineering/state/verification/acceptance.json
./engineering publish preflight --change example
# Only after the corresponding human authorization:
./engineering publish run --change example --authorize pr
```

Authorization scopes are cumulative: `commit` permits a remaining scoped commit,
`push` permits that commit and push, `pr` additionally permits PR/MR creation.
They never permit merge or force-push. The runtime must derive the option from
the human's request; a machine flag cannot prove human intent.

Existing implementation commits are reused. Remaining working bytes are staged
only for accepted paths; `git commit --only` preserves unrelated index entries.
Committed bytes and executable modes must equal the verified proposed tree.
An enforced pre-push guard runs the configured pre-push hook with its original
arguments and stdin, then validates content before Git transmits objects. It does
not skip hooks or rewrite repository hook configuration. The guard restores the
caller's Git configuration before invoking the original hook, so nested Git
commands retain their configured hooks. Scoped pushes explicitly disable tag
following; unrelated annotated tags remain local even when `push.followTags` is
enabled. Failed hooks stop the flow. Changes caused by filters/hooks require
evidence reassessment.

## Hosting providers and results

`provider: "github"` uses `gh pr create`; `"gitlab"` uses `glab mr create` with
explicit repository, source and target. Install/authenticate provider tools
separately. No hosting dependency is required for commit-only requests.

Other providers, including Bitbucket, use an explicit executable argument array,
for example `"provider": ["project-publish"]`. Inspect this project-owned adapter
before execution. It is invoked without a shell as `project-publish --request
<temporary-json-file>`. The request contains the review fields, exact committed
`head` and a `body_file` containing scope, checks, independent summaries and gaps.
The adapter receives an `action` field. For `"create"`, it must create the actual
PR/MR and print only `{"url":"https://..."}` on success; a drafted body is
insufficient. For `"lookup"`, it must read hosting state for the exact repository,
source branch and target branch, without creating anything. Return exactly
`{"url":null}` only when absence is established. For an existing request, return
`{"url":"https://...","head":"<commit SHA>","state":"open"}`. An ambiguous,
failed or incomplete lookup must exit nonzero. Closed/merged requests or a
mismatched head stop recovery for inspection. Update older create-only adapters
before use: lookup is now required and cannot be treated as creation. Adapters
own their provider API calls. Fake adapters in disposable repositories test this
contract without publishing real PRs. Built-in providers must return a PR/MR URL
as their final creation stdout line.

## Resume a partial publication

A successful result reports the URL. A stopped result reports `completed` steps
confirmed during this invocation, the `failed` operation, its error and a concrete
retry command. A failed push or creation response can be uncertain: the server
may have completed it before the response was lost. Do not interpret a missing
step in `completed` as proof that no remote change occurred.

After restoring connectivity or fixing the reported hook/provider failure, run:

```bash
./engineering publish run --change example
```

The first authorized run saves its scope in ignored local verification storage,
bound to the exact presented review. Retry reuses that scope; it does not require
another human authorization for unchanged work. Passing an explicitly authorized
narrower scope replaces the saved scope. A changed review cannot inherit it.
Missing records require supplying the human-authorized scope again; flags and
local records remain attestations, not authentication of human intent.

Every retry checks current content, evidence, branch, push URL and comparison
base. Content-preserving commits and transport failure do not rerun review or
checks. Changed content or relevant evidence inputs return to verification and
acceptance review. An existing accepted commit is reused. The actual push
destination is queried, so a completed push is skipped even after an uncertain
response. A divergent branch gets an ordinary push rejection, never an automatic
force-push. A push that is still needed runs all existing hooks.

Before creating a PR/MR, a read-only provider lookup finds matching requests,
including closed/merged ones. GitHub and GitLab lookup syntax follows their
[GitHub CLI](https://cli.github.com/manual/gh_pr_list) and
[GitLab CLI](https://docs.gitlab.com/cli/mr/list/) documentation. An open request
with the exact committed head is reused and its URL reported. Ambiguous,
truncated, malformed, unavailable or conflicting results stop publication;
resolve the reported condition before retrying. This also recovers a creation
whose successful response was lost. Provider consistency and accurate adapter
lookups are required; serialize publication for a branch across checkouts.
