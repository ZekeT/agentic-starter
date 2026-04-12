# /review

Run a code review on the current PR or a named story in `stories/review/`.

Usage: `/review` (current branch) or `/review story-001`

---

```bash
echo "=== Changed files ===" && git diff main --name-only
echo "=== Diff ===" && git diff main
echo "=== Story ===" && find stories/review -name "*$ARGUMENTS*" -exec cat {} \; 2>/dev/null || echo "(no story filter)"
echo "=== make check output ===" && make check 2>&1 | tail -30
```

Review using the code-reviewer agent checklist. Produce a structured
review (Summary / Must Fix / Should Fix / Notes / Verdict).

For security-sensitive changes, also run `/security-scan`.
