---
name: caveman
description: Use when sending inter-agent messages, status updates to orchestrators, or intermediate reasoning steps where human-readable prose wastes tokens.
---

# Caveman Skill

Cuts ~75% of output tokens by stripping filler words while keeping
full technical accuracy. Useful for inter-agent messages where
human-readable prose wastes tokens.

Trigger: `/caveman`, "talk like caveman", "less tokens please"
Stop:    "stop caveman", "normal mode"
Auto:    subagents use this style for all inter-agent messages (see CLAUDE.md)

---

## When to use

- Inter-agent messages (developer → reviewer handoff notes)
- Status updates to orchestrator agents
- Intermediate reasoning steps that won't be read by humans

## When NOT to use

- Human-facing output: reviews, CLAUDE.md updates, PR descriptions
- Code (caveman never touches code blocks)
- Git commits and PR titles

## What it strips

| Thing | Caveman behaviour |
|-------|-------------------|
| Filler phrases ("I'd be happy to...") | Removed |
| Articles (a, an, the) | Removed |
| Hedging ("it might be worth considering") | Removed |
| Code blocks | Unchanged |
| Technical terms | Unchanged (polymorphism stays polymorphism) |
| Error messages | Quoted exactly |

## Example

Normal (69 tokens):
> "The reason your component is re-rendering is likely because you're
> creating a new object reference on each render cycle..."

Caveman (19 tokens):
> "New object ref each render. Inline object prop = new ref = re-render.
> Wrap in `useMemo`."

Same fix. 75% fewer tokens.
