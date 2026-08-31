# /commit-push-pr

Stage, commit, push, and open a PR against the project's conventions. Used dozens
of times a day, so it pre-computes git context to avoid back-and-forth.

Usage: `/commit-push-pr "feat(auth): add JWT validation"` (message optional)

Conventions: `docs/harness/commits-and-prs.md`. PR body:
`.github/pull_request_template.md`.

---

```bash
echo "=== Branch ===" && git branch --show-current
echo "=== Status ===" && git status --short
echo "=== Diff stat vs main ===" && git diff main --stat

BRANCH=$(git rev-parse --abbrev-ref HEAD)
SLUG=$(echo "$BRANCH" | sed -nE 's|^feat/(.*)-g[0-9]+$|\1|p')
GROUP=$(echo "$BRANCH" | sed -nE 's|^feat/.*-g([0-9]+)$|\1|p')

if [ -n "$SLUG" ] && [ -d "openspec/changes/$SLUG" ]; then
  echo "=== Change: $SLUG (task group ${GROUP:-?}) ==="
  echo "--- delta specs this diff must satisfy ---"
  find "openspec/changes/$SLUG/specs" -name '*.md' \
    -exec echo '### {}' \; -exec cat {} \; 2>/dev/null
  echo "--- task group $GROUP ---"
  awk -v g="$GROUP" '
    /^##[[:space:]]+[0-9]+\./ {
      match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
      inblock = (n == g)
    }
    inblock
  ' "openspec/changes/$SLUG/tasks.md" 2>/dev/null

  UNCHECKED=$(awk -v g="$GROUP" '
    /^##[[:space:]]+[0-9]+\./ {
      match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
      inblock = (n == g)
    }
    inblock && /^[[:space:]]*-[[:space:]]*\[[[:space:]]\]/
  ' "openspec/changes/$SLUG/tasks.md" 2>/dev/null)
  if [ -n "$UNCHECKED" ]; then
    echo "!!! Tasks in group $GROUP still unchecked:"
    echo "$UNCHECKED"
    echo "!!! Tick them if done, or finish them. tasks.md is the plan of record."
  fi
else
  echo "=== No change folder resolved from branch name ==="
  echo "(fine for a hotfix or chore — say so in the PR's Change line)"
fi

echo "=== Tests touched by this diff ==="
git diff main --name-only | grep -E '^tests/' || echo "(none — is that right for this change?)"

echo "=== make check ===" && make check 2>&1 | tail -15
```

Only proceed if `make check` passes. If it fails, stop and report the failures —
never commit past a red gate.

Then:

1. `git add -A`
2. Commit. Use `$ARGUMENTS` if given; otherwise write a Conventional Commits
   message per `docs/harness/commits-and-prs.md` — imperative subject, and a body
   explaining **why** rather than restating the diff.
3. `git push -u origin HEAD`
4. Open the PR with `.github/pull_request_template.md` as the body, filled in:

   ```bash
   gh pr create --title "<subject>" --body-file <(...)   # or --body "<filled template>"
   ```

   - **What & why** — the problem solved, plus the change slug and task group
     printed above (or "none" with a reason).
   - **How this was tested** — name the actual tests covering the new behaviour.
     Use the tests-touched list above. If nothing under `tests/` changed, say why
     that's correct. For manual verification, record the steps *and the observed
     result*; "tested locally" is not evidence.
   - **Not covered** — state honestly what this change does not verify. Do not
     leave it blank to look thorough; it is the line reviewers rely on most.
   - **Spec compliance** — tick only boxes you actually checked against the delta
     specs printed above.
   - **Risk** — what breaks if this is wrong, and how it rolls back.

5. Print the PR URL.

Never tick a checklist box you have not verified. An inaccurate template is worse
than an empty one: it costs the reviewer the trust that makes the checklist worth
having.
