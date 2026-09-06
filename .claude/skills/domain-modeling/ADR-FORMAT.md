# ADR Format

**This repo's ADRs live in `docs/decisions/`.** That directory's `index.md`
holds the convention and is the authority — read it before writing one. In
summary:

- Filename `NNNN-slug.md`, zero-padded, numbered in merge order. Scan
  `docs/decisions/` for the highest number and increment.
- Sections: **Context** (the forces, including what you did not know) →
  **Decision** (what was chosen, active voice) → **Consequences** (what this
  costs, not only what it buys).
- Status: `Accepted` · `Superseded by NNNN` · `Deprecated`.
- **Append-only.** Never edit a merged ADR. A decision that turns out wrong gets
  a new ADR superseding it — the record of having been wrong is the point.
- Add a row to the `index.md` table in the same commit.

The three sections are required here, unlike the upstream version of this skill
which allows a single paragraph. Consequences is the one people skip and the one
future readers need.

An ADR records *why*. What the system currently does is `openspec/specs/`; what
shape it has is `docs/architecture.md`; what a term means is `CONTEXT.md`.

## When to offer an ADR

All three of these must be true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If a decision is easy to reverse, skip it: you'll just reverse it. If it's not surprising, nobody will wonder why. If there was no real alternative, there's nothing to record beyond "we did the obvious thing."

### What qualifies

- **Architectural shape.** "We're using a monorepo." "The write model is event-sourced, the read model is projected into Postgres."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target. Not every library: just the ones that would take a quarter to swap out.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; other contexts reference it by ID only." The explicit no-s are as valuable as the yes-s.
- **Deliberate deviations from the obvious path.** "We're using manual SQL instead of an ORM because X." Anything where a reasonable reader would assume the opposite. These stop the next engineer from "fixing" something that was deliberate.
- **Constraints not visible in the code.** "We can't use AWS because of compliance requirements." "Response times must be under 200ms because of the partner API contract."
- **Rejected alternatives when the rejection is non-obvious.** If you considered GraphQL and picked REST for subtle reasons, record it; otherwise someone will suggest GraphQL again in six months.
