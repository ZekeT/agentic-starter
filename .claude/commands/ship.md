---
description: Publish the accepted unchanged scope using current independent evidence.
---

Read REVIEW.md, .engineering/docs/publication.md and
.engineering/docs/commits-and-prs.md. Inspect the intended diff and saved acceptance
summary, including committed, staged, unstaged and intended new paths. Completed
acceptance review is required; invoking /ship cannot supply missing review.

After completed review, /ship expresses human acceptance of the presented unchanged
scope and authorization to commit remaining accepted fixes, push and create the
actual PR/MR when blockers are resolved. Honor narrower requests and existing
explicit authorization. Never infer publication permission from /implement.
Never merge or force-push without separate specific authorization.

Use engineering publish preflight to check intended content/paths, current proof,
comparison base, branch/remote and unresolved blockers. Missing or stale evidence
returns to verification; missing/stale acceptance summary or blockers return to
/review and human-directed corrections. Reuse current semantic review and checks;
do not rerun unchanged authoritative checks during shipping.

Use engineering publish run with only the human-authorized commit/push/pr scope.
Reuse implementation commits and stage only accepted paths. Preserve unrelated
working and staged files. Hooks remain enforced; failures stop publication and
hook content mutations require reassessment before transport. Use the configured
provider, not an assumed GitHub repository. A PR body draft is not publication:
report the actual PR/MR URL, scope and useful test evidence. On failure report
completed steps and inspect Git/provider state before any retry.
