# Harness design

Why the harness is shaped the way it is. This is the template's own decision
record, consolidated from three ADRs written days apart during the 1.4.0
cleanup. A fork inherits the ADR *practice* (`docs/decisions/`, append-only,
one file per decision) with an empty log — this document is the template's
history, not a pattern to keep extending here.

---

## Why the OpenSpec change loop

The harness used to run a waterfall: `docs/prd.md` → `docs/architecture.md` →
stories → code. Two problems compounded.

**Nothing recorded what the system currently does.** The PRD recorded what was
once wanted. Stories recorded what was once built. Neither was maintained, so
answering "what is true about X today?" meant reading code. Both documents
drifted the moment implementation departed from them, and nothing forced them
back.

**Planning loaded everything eagerly.** `/sprint-planning` hard-failed without
both documents and `cat`-ed them wholesale into context regardless of
relevance.

OpenSpec offers a change lifecycle built on the missing piece:
`openspec/specs/` is a living statement of current behaviour, mutated only
when a change archives, so the reviewable unit becomes a **spec diff** rather
than a pile of generated lines.

This also had to satisfy Anthropic's AI-Native SDLC playbook artifact chain
(intent → spec → plan → diff+tests → PR+review). The playbook's chain is an
audit trail of what was asked and decided; it has no canonical living
statement of current behaviour. **The archive step is where this harness
deliberately goes beyond it** — a fifth stage the playbook doesn't have,
whose entire job is folding the diff back into a `specs/` tree that stays
true.

The loop:

```
exploration → /crystallize → openspec/changes/<slug>/
            → /dev-change <slug> <group> → code + tests
            → /archive-change → deltas merge into openspec/specs/
```

Ownership is split so that no artifact has two masters:

| Layer | Owner | Lifetime |
|---|---|---|
| Product intent (`docs/product.md`, `docs/architecture.md`, `docs/decisions/`) | human + agent, hand-maintained, small | durable |
| Behaviour specs (`openspec/specs/`) | OpenSpec, mutated only at archive | durable |
| In-flight change (`openspec/changes/<slug>/`) | OpenSpec | until archived |
| Implementation tasks | Superpowers, driven from `tasks.md` | ephemeral |

A few decisions worth recording:

- **`docs/prd.md` is gone, not kept as a seed.** A vestigial PRD is exactly
  the artifact this change exists to remove: forking developers fill it in,
  then are misled by it. `docs/product.md` holds durable product intent;
  `openspec/changes/<slug>/intent.md` holds per-change intent.
- **`stories/` is removed; `tasks.md` is the plannable unit.** Keeping both
  meant two overlapping task lists to hold in sync. `openspec archive`
  succeeds with only `proposal` + `specs` present, so nothing forces a
  `tasks.md`, and nothing forced stories either. The `draft/ → ready/` folder
  move (the git-visible human gate) is replaced by the PR on the change
  folder itself — intent as one commit, spec + tasks as the next.
  Branch-existence-as-mutex, previously per story, is replaced by
  `/dev-change <slug> <group>` keying the worktree to a `## N` task group, so
  each group is one branch, one worktree, one PR.
- **`crystallize` wraps `openspec-propose` rather than reimplementing it.**
  OpenSpec ships skills that already create and validate change folders;
  `crystallize` adds only what OpenSpec lacks — classification against
  existing truth, separating findings from decisions from assumptions from
  unknowns, the `intent.md` gate, ADR drafting, and surfacing conflicts with
  existing decisions.
- **`intent.md` lives inside the change folder**, ignored by `openspec
  status`/`validate`. Its value is the two-commit gate and two leading
  indicators readable straight from `git log` on the change folder: time from
  first conversation to accepted intent, and intent to spec.
- **The repo is the source of truth for every artifact.** Any external
  tracker holds a commit SHA and links back, never the reverse.

**Cost.** A Node dependency (`openspec`, Node ≥ 20.19) in an otherwise pure
Python/uv harness, checked in setup as a warning, never a hard fail — the rest
of the harness works without it.

---

## Capability granularity

How big is a capability in `openspec/specs/`? The stakes are retrieval, not
tidiness: the capability is the unit of lookup, and the entire argument for
the change loop is answering "what is currently true about X?" from
`openspec list --specs` plus one named file. A capability spanning several
unrelated topics forces every reader to load all of them to learn one.

A capability is right-sized when it passes three tests, applied in order of
cost:

**1. The naming test.** The Purpose must be one sentence that does not use
"and" to join unrelated activities, and the name must not be a generic
container noun — `core`, `platform`, `utils`, `management`, `handling`,
`common`. Run this before committing a new capability; it costs nothing and
catches most cases. A purpose sentence needing "and" to join unrelated
activities (e.g. "how work is tested, **and** committed, **and** proposed for
review") has already told you it needs to split — the signal is present at
authoring time and easy to skip if nothing prompts you to look.

**2. The independent-change test.** Try to name a realistic change that
touches exactly one subset of the requirements and none of the others. If you
can, that subset is a separate capability. This is the decisive test: it asks
about *behaviour* changing, not code changing — an earlier heuristic ("would
you rewrite this code together?") asked an implementation question of a
behaviour artifact, and code and behaviour don't share seams, so the answer
could mislead.

**3. The touch-count test.** Across `openspec/changes/archive/`, count
capabilities touched per change. Mostly one is healthy. Mostly three or more
means capabilities are too fine. Changes repeatedly touching a small slice of
one large capability means it is too coarse. This is the only empirical
signal, and it needs history before it says anything — useless early, when
`archive/` is nearly empty, which is exactly when the taxonomy is being set.
The naming test carries the load until then.

Two supporting rules:

**Capabilities are not modules.** One capability may span modules; one module
may serve several. If the capability list mirrors the directory tree exactly,
the specs describe the implementation, and they will churn on every refactor
without any behaviour having changed.

**Start coarse; split when a change reveals the seam.** Seams are not knowable
in advance. A too-coarse capability announces itself loudly, in its own
purpose sentence. A too-fine taxonomy is quietly annoying forever and
multiplies — twenty wrong small capabilities is a worse mess than four
slightly large ones. Nesting (`domain/capability`) earns its keep once the
flat list stops scanning, around eight to ten entries. Nest by domain
(`billing/invoicing`), never by layer (`api/billing`) — layers are
implementation.

**A capability cannot be retired by a delta alone.** A `REMOVED` delta
covering every requirement in a capability fails at archive time —
`openspec archive` refuses to write a spec with zero requirements. Splitting
or retiring a capability is two operations: archive the change that ADDs the
new capabilities, then `git rm` the old spec directory by hand in the same
commit. Know this before writing the delta; the failure arrives after the
specs are already written.

---

## One instruction file

The template used to ship two instruction files: `AGENTS.md`, following the
cross-tool convention that any coding agent reads it, and a thin `CLAUDE.md`
that pulled it in with `@AGENTS.md`. The stated goal was portability — a fork
using Cursor, Codex, or Aider would get the same project facts without editing
anything.

Three things worked against it. **Two files meant two things to keep
coherent** — the split was never clean in practice, since Claude Code-specific
mechanics (hook wiring, `/crystallize`, the worktree mutex) had nowhere
natural to live, so they accumulated in whichever file the last editor had
open. **`@import` loads eagerly** — the import pulled `AGENTS.md` into every
session before anything asked for it, so the two-file split bought no lazy
loading, just one file's content spread across two files' headers, plus an
eval budget that had to cover both. **The starter is Claude Code-first and
says so** — hooks, agents, slash commands, and skills all target `.claude/`;
portability to a non-Claude agent was never actually delivered by the second
file, only signalled by it.

`CLAUDE.md` is the single agent-instruction file. `AGENTS.md` is not shipped,
and nothing in the template writes or imports one. The current rule: the
*whole file* is budgeted at 120 lines, checked by eval 006 — there is no
generated section to exclude any more, so the cost of adding to `CLAUDE.md` is
visible and immediate: adding means cutting.

A fork targeting several agents can reintroduce `AGENTS.md` as a thin file
that imports nothing and restates the same facts. At that point the fork owns
keeping the two in sync — a cost this decision declines to pay by default, not
a capability the template forbids.
