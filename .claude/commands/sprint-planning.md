# /sprint-planning

Break the approved PRD and architecture into self-contained story files.
Invokes the scrum-master agent. Human gate required before moving stories to ready/.

Usage: `/sprint-planning`

---

```bash
echo "=== PRD ===" && cat docs/prd.md 2>/dev/null || echo "docs/prd.md not found"
echo "=== Architecture ===" && cat docs/architecture.md 2>/dev/null || echo "docs/architecture.md not found"
echo "=== Existing stories ===" && find stories -name "*.md" | sort
```

Use the scrum-master agent to:
1. Read `docs/prd.md` and `docs/architecture.md`
2. Identify independently deliverable units of work
3. Create `stories/draft/story-{NNN}-{slug}.md` for each
4. Present the full sprint plan for human review

**Stop after presenting the plan. Wait for human approval before
moving any story to `stories/ready/`.**
