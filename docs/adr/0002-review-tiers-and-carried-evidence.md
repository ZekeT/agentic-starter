# Review tiers and carried evidence

Status: accepted (2026-09-28)

Each verification plan declares a review tier — `documentation`, `ordinary` or `sensitive` — that decides the required reviewer roles and whether one session may cover two of them. A deterministic tier floor, computed from changed paths, sets the minimum; the plan may raise it but never lower it. Starter-owned lists always win: agent-policy Markdown is never documentation tier, and dependency, hook, settings, workflow and destructive-operation paths are always sensitive. Projects can extend these lists but not reduce them, and the floor uses the stricter of base and proposed configuration. Tiers change reviewers, not checks.

Only project review settings are read from both base and proposed content. The starter lists stay in code and come from the running implementation. They live in a module that is itself sensitive in the maintainer checkout and managed implementation in consumers. Independent consumer edits are rejected; ticket 08 permits updates that match a fetched, pinned starter distribution. Such updates always require the sensitive tier, including security review of the chosen source and any policy change. A data file would not change the execution boundary: the running verifier decides whether to read it. Source identity also participates in snapshot freshness and carry-forward eligibility.

Reviewer reports carry forward across a clean rebase — identical own diff, unchanged plan, tools and checks, and no upstream change to the scope — but authoritative checks always rerun on the new snapshot. Because rerunning recorded argv carries no judgment, anyone, including the implementer, may run those checks for a carried snapshot. Base-tip movement without a rebase no longer invalidates evidence; the merge-base still defines content identity.

## Considered options

Recorded so the decision is not reopened in a loop:

- **Implementer-declared tier only** — rejected: the author of a change would decide how much independent review it gets.
- **Separate `security_required` beside the tier** — rejected: two fields describing one risk decision can disagree.
- **Size threshold for a single combined reviewer** — rejected: easy to game and needs tuning; the tier already carries the risk signal.
- **Documentation tier with no reviewer** — rejected: documents that contradict code are the real risk, and nothing may self-certify.
- **Mapping reviewer roles to paths for partial re-review after an overlapping rebase** — rejected: no reliable mapping; the existing review-corrections procedure already allows justified retention.
- **Always a fresh verifier session to rerun checks for carried evidence** — rejected: a full session for a deterministic rerun whose argv and output the tool records.
- **Inferring tiers for existing evidence records** — rejected for the same downgrade reason as ADR 0001; legacy records are re-prepared.
