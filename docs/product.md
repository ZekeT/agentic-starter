# Product

> Durable product intent: what this is, who it's for, what it deliberately is not.
> Hand-maintained and small. Changes rarely — if you're editing it every week,
> the content belongs in a change proposal instead.
>
> This is **not** a requirements document. Per-change intent lives in
> `openspec/changes/<slug>/intent.md`; current behaviour lives in
> `openspec/specs/`. Replace this whole file when you fork the template.

---

## What this is

<!-- Two or three sentences. What does the product do? -->

## Who it's for

<!-- The primary user and the job they're hiring this to do. Name one, not five. -->

| User | What they need it for |
|---|---|
| <!-- role --> | <!-- job to be done --> |

## Why it exists

<!-- The problem that justifies building this rather than using something else. -->

## Non-goals

<!-- The most valuable section. Each line is a decision you won't relitigate.
     Non-goals are what stop scope creep from arriving one reasonable change
     at a time. -->

- <!-- something a reasonable person would expect this to do, that it will not do -->

## Success criteria

<!-- How you'll know it's working. Observable, not aspirational. -->

- <!-- criterion -->

---

## Where the rest of the truth lives

| Question | Read this |
|---|---|
| What does the system currently do? | `openspec/specs/` — `openspec list --specs` first |
| What's changing right now? | `openspec/changes/<slug>/` |
| Why was it built that way? | `docs/decisions/` |
| What is the system's shape? | `docs/architecture.md` |
