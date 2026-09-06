# /dev-change

Implement one task group from an OpenSpec change, on its own branch. One task
group = one branch = one PR.

Usage:
- `/dev-change <slug> <group>` — work on task group `<group>` of that change
- `/dev-change <slug>` — claim the lowest-numbered group with unchecked tasks
- `--worktree` — claim into `.worktrees/<slug>-g<N>` instead of switching this
  checkout. Worth it **only** when running several sessions at once, which is
  what the isolation is for. A single session pays for it in editor visibility
  and a system-prompt refresh on `EnterWorktree`, and gains nothing.

The mutex that stops two sessions implementing the same group is **branch
existence**: claiming a group means winning the race to create
`feat/<slug>-g<N>`. `git switch -c` and `git worktree add` both fail on an
existing branch, so the mutex holds either way. Nothing about the claim is
recorded in a file, so there is no state to reconcile if a session dies — the
branch either exists or it does not.

Task groups come from `openspec/changes/<slug>/tasks.md`, whose `## N.` headings
are written to be independently shippable (enforced by the `tasks` rule in
`openspec/config.yaml`). If a group cannot ship on its own, that is a bug in the
change's planning, not something to work around here.

---

```bash
bash .harness/scripts/cmd_dev_change.sh $ARGUMENTS
```

After the preamble runs:

1. If a worktree path was printed, call `EnterWorktree` with it. Otherwise this
   checkout is already on the branch — do not create a worktree.
2. Work **only** the tasks in the claimed group. The other groups belong to
   other branches; touching them here creates the merge conflicts this
   one-group-per-PR split exists to prevent.
3. The proposal, delta specs, and design printed above are the full context.
4. **The task group is the plan. Do not re-plan it.** It was written by
   `/crystallize` and accepted at a human gate, and it is already on screen.
   Implement it directly in this session, driving each task with the Superpowers
   **`test-driven-development`** skill: failing test, minimal code, refactor.
   Do **not** invoke `subagent-driven-development` here — it dispatches a fresh
   implementer and a fresh reviewer per task, each re-reading this context cold,
   to re-derive a plan you already have.
5. As each task completes, tick its checkbox in `openspec/changes/<slug>/tasks.md`
   (`- [ ]` → `- [x]`), and update the task text in the same commit if
   implementation departed from it (see CLAUDE.md **Rules**).
6. If this group adds a feature directory under `src/`, or changes what an
   existing one is for, write or update that directory's own `CLAUDE.md` in the
   same commit — purpose, entry points, invariants, gotchas; ~30 lines. This is
   what stops the next session re-deriving the feature from its source. Stable
   facts only: never implementation status, which is `tasks.md`'s job.
7. CLAUDE.md's **Rules** govern here and are already loaded — in particular,
   what to do when a delta spec turns out to be wrong, and when to stop and ask
   rather than guess. A bug attempted twice without success is one of those
   stopping points.
8. Run `make check`. It must pass before you hand anything to a human, and its
   result is what you hand over — nothing downstream runs it again until
   `/commit-push-pr`.
9. Dispatch the **`verifier`** subagent. Fresh context, so its verdict is not
   coloured by the assumptions that produced the code — this session has
   already convinced itself. Give it the change slug and group number; it runs
   the change and reports mismatches without fixing anything. A FAIL is yours
   to resolve now: either the code is wrong or the delta spec is (step 7).
10. Worktree mode only: call `ExitWorktree` with `action: "keep"`.
11. **Stop here. Do not commit, and do not open a PR.** Print, for the user:
    the branch name, the `make check` result, the verifier's report verbatim,
    the tasks now ticked, the remaining unchecked groups, and the two commands
    that come next —

    ```
    /review           # verify the implementation against the spec
    /commit-push-pr   # commit and open the PR, once satisfied
    ```

    The human gate sits *before* the commit. Nothing this session wrote reaches
    git history or GitHub until a person has read `/review`'s verdict and chosen
    to run `/commit-push-pr` themselves.
