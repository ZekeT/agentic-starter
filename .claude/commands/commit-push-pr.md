# /commit-push-pr

Stage, commit, push, and open a PR. Used dozens of times a day.
Pre-computes git context so the model avoids back-and-forth.

Usage: `/commit-push-pr "feat(auth): add JWT validation"`

---

```bash
echo "=== Status ===" && git status --short
echo "=== Staged diff ===" && git diff --cached --stat
echo "=== Branch ===" && git branch --show-current
echo "=== Remote ===" && git remote -v | head -2
echo "=== make check ===" && make check 2>&1 | tail -10
```

Only proceed if `make check` passes. Then:
1. `git add -A`
2. `git commit -m "$ARGUMENTS"` (use conventional commit format if no message given)
3. `git push -u origin HEAD`
4. Open PR with title from commit message and body linking the story file.

If `make check` fails, stop and report the failures. Do not commit broken code.
