# /implement

Pick up a story from `stories/ready/` and implement it using the
Superpowers TDD workflow.

Usage: `/implement story-001` or `/implement stories/ready/story-001.md`

---

```bash
# Pre-compute context so the agent doesn't have to ask
echo "=== Git status ===" && git status --short
echo "=== Story file ===" && cat stories/ready/$ARGUMENTS 2>/dev/null \
  || cat stories/ready/$ARGUMENTS.md 2>/dev/null \
  || find stories/ready -name "*$ARGUMENTS*" -exec cat {} \;
echo "=== Branch ===" && git branch --show-current
```

Move story to in-progress, then implement following the developer agent
workflow (Superpowers TDD: brainstorm → plan subtasks → tests first →
implement → verify with `make check`).

When done: open a PR and move the story to `stories/review/`.
