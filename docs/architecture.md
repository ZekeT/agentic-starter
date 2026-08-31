# Architecture

> **System shape only** — containers, boundaries, and constraints that cut across
> every change. Behaviour does not belong here: it lives in `openspec/specs/`,
> which the archive step keeps current automatically. This file is hand-maintained,
> so anything duplicated from the specs will go stale and start lying.
>
> Load this only when a change is marked architecture-affecting in its proposal.

---

## Containers

<!-- The major deployable/runnable pieces and how they talk. One diagram beats
     three paragraphs. Keep it to things that would survive a rewrite. -->

```
[component A] → [component B] → [component C]
```

| Container | Responsibility | Talks to |
|---|---|---|
| <!-- name --> | <!-- one line --> | <!-- neighbours --> |

## Boundaries

<!-- Where the seams are, and what may not cross them. These are the rules that
     make a diff reviewable without reading the whole system. -->

- <!-- e.g. the API layer never touches the database directly -->

## Cross-cutting constraints

Hard rules every change must respect, regardless of what it touches.

- Python ≥ 3.11
- Line length 88 (black); `make check` is the gate
- All public APIs carry docstrings (interrogate, 80% floor)
- External data is validated at the boundary (pydantic/marshmallow), never trusted inward

## External dependencies

<!-- Third-party services, APIs, datastores — and the blast radius if each one
     is unavailable. -->

| Dependency | Used for | If it's down |
|---|---|---|
| <!-- name --> | <!-- purpose --> | <!-- degradation --> |

---

Architectural decisions and their rationale are **not** recorded here — one file
per decision in `docs/decisions/`, append-only. This file describes the shape that
results from those decisions.
