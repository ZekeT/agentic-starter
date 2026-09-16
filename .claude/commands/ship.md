---
description: Run the final gate and ship only the scope authorized by the human.
---

Read REVIEW.md and .engineering/docs/commits-and-prs.md. Inspect Git status and
the full intended diff, including untracked files; show the proposed commit
scope. Require completed independent review/verification and resolve material
concerns. Run make check; any failure stops shipping.

Do not commit, push, create a PR/MR, or merge unless requested by the human.
Honor explicit authorization already provided in the session. Otherwise show
the concrete scope and ask for the missing shipping authorization as the final
step. Stage named intended paths; do not sweep unrelated user work into a commit.
Use ordinary Git and the configured hosting provider's tooling. GitHub/gh is
optional; local commits, GitLab and Bitbucket are supported by project policy.
Never merge or force-push without specific authorization. Do not infer shipping
permission from invoking /implement. This command has no planning-state input.
