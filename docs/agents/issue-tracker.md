# Issue tracker: local Markdown

Use Matt Pocock's installed local Markdown adapter:
[upstream tracker contract](../../.claude/skills/setup-matt-pocock-skills/issue-tracker-local.md).
It owns storage conventions and Wayfinding operations. Specs and tickets are
local repository files under `.scratch/`; keep durable work tracked in Git.

This is the default for new projects regardless of remote hosting provider.
No GitHub API or `gh` CLI is required. To select GitHub Issues or another tracker,
run `/setup-matt-pocock-skills` and update this project-owned configuration.
Do not publish issues remotely without explicit human instructions.

## Progress updates

For ticket-based work, read the ticket and its existing breakdown before starting.
Mark work in progress, then check off criteria as supporting implementation and
validation evidence becomes available. Leave incomplete or unverified criteria
unchecked and explain what remains. Update the ticket and breakdown together at
meaningful milestones and before handing work back or ending the session.

Record concise evidence pointers and distinguish implemented, independently
verified, awaiting human acceptance, published and merged outcomes. A commit does
not prove verification or acceptance. After authorized publication, record the
actual PR/MR link; record merged only from observed delivery evidence. Reconcile
stale tracking from code, tests, review records and Git/provider evidence, noting
any gaps instead of inventing historical checks or approvals. Retain original
dependency relationships and identify which prerequisites remain outstanding.

Include implementation tracking edits in the scope before final verification so
late bookkeeping does not silently invalidate proof. If tracking changes after
review, reassess freshness under the verification policy; never relabel old proof
as current. Use the configured tracker without patching pinned upstream skills,
adding a tracker parser to Engineering, or publishing remote issues without
authorization.
