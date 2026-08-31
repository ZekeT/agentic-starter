# /plan

Drive planning for a new feature or project phase. Produces the two documents
/sprint-planning requires. Never writes stories — that's /sprint-planning's job.

Usage: `/plan`

---

1. Invoke the Superpowers `brainstorming` skill to refine requirements with
   the user. When requirements are settled, write/update `docs/prd.md`:
   problem, users, functional requirements, non-goals, success criteria.
2. Invoke `writing-plans` for the technical design. Write/update
   `docs/architecture.md`: components, data flow, key decisions with
   rationale, constraints agents must respect.
3. If either file already exists, update it — show the user a diff summary
   rather than silently rewriting.
4. Stop. Tell the user to review both docs, then run /sprint-planning.
   Do not proceed to stories yourself — document approval is a human gate.