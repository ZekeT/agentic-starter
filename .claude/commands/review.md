# /review

Verify an implementation against the change it claims to implement. This is
the **human's gate**: `/dev-change` stops without committing and hands the
branch over, and this is what you run before deciding to `/commit-push-pr`.

No agent calls this command. Running it is the decision to look.

Usage:
- `/review` — review the checked-out branch, uncommitted work included
- `/review <branch>` — review that branch (e.g. `feat/add-auth-g2`)
- `/review <slug>` — review the checked-out branch against that change slug

---

```bash
bash .harness/scripts/cmd_review.sh $ARGUMENTS
```

Run the passes defined in `REVIEW.md`. The compliance pass is the one this
harness exists to enable: check the diff against the delta specs and the task
group above, not just against general good taste.

`make check` is not run here — `REVIEW.md`'s **Skip entirely** section says not
to relitigate what the gate decides. If you have no hand-off result for this
branch, run `make check` yourself before trusting the diff.

Produce: Summary / Must Fix / Should Fix / Notes / Verdict.

For security-sensitive changes, also dispatch the `security-reviewer` agent.

End by telling the user what the verdict means for the next command: nothing
is committed yet, so **REQUEST CHANGES** means fix the branch and re-run this,
and **APPROVE** means they can run `/commit-push-pr`.
