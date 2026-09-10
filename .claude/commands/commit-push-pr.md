# /commit-push-pr

Stage, commit, push, and open a PR against the project's conventions. Used dozens
of times a day, so it pre-computes git context to avoid back-and-forth.

Usage: `/commit-push-pr [--base <branch>] "feat(auth): add JWT validation"`
(both optional)

`--base` is the branch the PR targets. Unset, it resolves in order:
`git config harness.baseBranch` → the remote's default branch (`origin/HEAD`) →
`main`. The preamble prints which one it picked; a team that merges to `develop`
sets the default once with `git config harness.baseBranch develop` instead of
typing the flag every time.

Conventions: `.harness/docs/commits-and-prs.md`. PR body:
`.github/pull_request_template.md`.

---

Pass `--base <branch>` through **only** if `$ARGUMENTS` contains it — never the
commit message, which is not shell-safe:

```bash
bash .harness/scripts/cmd_commit_push_pr.sh          # or: … --base <branch>
```

`make check` above is the final non-mutating full gate before committing.
The fresh verifier ran it before human review; repeat it here to catch edits
made since verification. Never replace it with a cached verdict.

Only proceed if `make check` passes. If it fails, stop and report the failures —
never commit past a red gate.

Then:

1. `git add -A`
2. Commit. Use `$ARGUMENTS` if given, minus any `--base <branch>`; otherwise
   write a Conventional Commits
   message per `.harness/docs/commits-and-prs.md` — imperative subject, and a body
   explaining **why** rather than restating the diff.
3. `git push -u origin HEAD`
4. Open the PR against the base printed above — always pass `--base`
   explicitly, so the target is in the command rather than in `gh`'s default —
   with `.github/pull_request_template.md` as the body, filled in:

   ```bash
   gh pr create --base "<PR base from above>" --title "<subject>" \
     --body-file <(...)   # or --body "<filled template>"
   ```

   - **What & why** — the problem solved, plus the change slug and task group
     printed above (or "none" with a reason).
   - **How this was tested** — name the actual tests covering the new behaviour,
     using the tests-touched list above, and paste the `verifier` agent's report
     from `/dev-change`. If nothing under `tests/` changed, say why that's
     correct. For manual verification, record the steps *and the observed
     result*; "tested locally" is not evidence.
   - **Not covered** — state honestly what this change does not verify. Do not
     leave it blank to look thorough; it is the line reviewers rely on most.
   - **Spec compliance** — tick only boxes you actually checked against the
     scenarios listed above. If a scenario's wording matters, open its file
     rather than guessing.
   - **Risk** — what breaks if this is wrong, and how it rolls back.

5. Print the PR URL.

Never tick a checklist box you have not verified. An inaccurate template is worse
than an empty one: it costs the reviewer the trust that makes the checklist worth
having.
