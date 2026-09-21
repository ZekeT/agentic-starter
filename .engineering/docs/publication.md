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
not skip hooks or rewrite repository hook configuration. Failed hooks stop the
flow. Changes caused by filters/hooks require evidence reassessment.

## Hosting providers and results

`provider: "github"` uses `gh pr create`; `"gitlab"` uses `glab mr create` with
explicit repository, source and target. Install/authenticate provider tools
separately. No hosting dependency is required for commit-only requests.

Other providers, including Bitbucket, use an explicit executable argument array,
for example `"provider": ["project-publish"]`. Inspect this project-owned adapter
before execution. It is invoked without a shell as `project-publish --request
<temporary-json-file>`. The request contains the review fields, exact committed
`head` and a `body_file` containing scope, checks, independent summaries and gaps.
The adapter must create the actual PR/MR and print only `{"url":"https://..."}`
on success; a drafted body is insufficient. Adapters own their provider API calls.
Fake adapters in disposable repositories test this contract without publishing
real PRs. Built-in providers must return a PR/MR URL as their final stdout line.

A successful result reports the URL. Failure reports the steps already completed
(preflight, commit, push, PR). Failed hooks may have changed local content or even
created a commit, and a provider may have created a PR before losing its response.
Inspect Git and hosting state before retrying; automatic resumable recovery and
duplicate detection belong to the follow-on recovery slice. Do not claim a failed
or ambiguous response as successful publication.
