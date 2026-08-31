# 0001 — Adopt the OpenSpec change loop

- **Status**: Accepted
- **Date**: 2026-08-31

## Context

The harness ran a waterfall: `docs/prd.md` → `docs/architecture.md` → stories →
code. Two problems compounded.

**Nothing recorded what the system currently does.** The PRD recorded what was
once wanted. Stories recorded what was once built. Neither was maintained, so
answering "what is true about X today?" meant reading code. Both documents drifted
the moment implementation departed from them, and nothing forced them back.

**Planning loaded everything eagerly.** `/sprint-planning` hard-failed without
both documents and `cat`-ed them wholesale into context regardless of relevance.

OpenSpec offers a change lifecycle built on the missing piece: `openspec/specs/`
is a living statement of current behaviour, mutated only when a change archives,
so the reviewable unit becomes a **spec diff** rather than a pile of generated
lines.

This also had to satisfy Anthropic's AI-Native SDLC playbook artifact chain
(intent → spec → plan → diff+tests → PR+review). The playbook's chain is an audit
trail of what was asked and decided; it has no canonical living statement of
current behaviour. The archive step is where this harness deliberately goes beyond
it.

## Decision

Replace the waterfall with an iterative change loop.

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

Specific decisions taken during implementation:

1. **OpenSpec writes no agent-instruction file.** Verified in the Phase 1 spike:
   `openspec init --tools claude` and `openspec update` touch neither `CLAUDE.md`
   nor `AGENTS.md`. It owns only `openspec/`, `.claude/commands/opsx/`, and
   `.claude/skills/openspec-*/`. `configure.py`'s `## Active Model Config` section
   therefore **stays in `CLAUDE.md`** — the contemplated fallback of moving it to
   a separate file was unnecessary.

2. **`docs/prd.md` is deleted, not kept as a seed.** A vestigial PRD is exactly
   the artifact this change exists to remove: forking developers fill it in, then
   are misled by it. `docs/product.md` holds durable product intent;
   `openspec/changes/<slug>/intent.md` holds per-change intent.

3. **`stories/` is removed entirely; `tasks.md` is the plannable unit.** Keeping
   both meant two overlapping task lists to hold in sync — the drift this change
   exists to eliminate. Verified in the spike that `openspec archive` succeeds
   with only `proposal` + `specs` present, so nothing forces a `tasks.md`, and
   nothing forced stories either.

   The playbook treats its `plan.md` slot as a durable committed artifact that PR
   review checks the diff against. `openspec/changes/<slug>/tasks.md` is committed
   and satisfies that. It is also *less* eagerly-loaded than a story file, which
   was by design self-contained and therefore fat.

   Two things were lost and deliberately replaced rather than dropped:
   - The `draft/ → ready/` folder move was the git-visible human gate. Its
     replacement is the PR on the change folder itself — intent as one commit,
     spec + tasks as the next. This maps 1:1 onto the playbook's two gates, which
     a folder move never did.
   - Branch-existence-as-mutex was per story. `/dev-change <slug> <group>` keys
     the worktree to a `## N` task group instead, so each group is one branch, one
     worktree, one PR. Granularity and the mutex both survive.

4. **`crystallize` wraps `openspec-propose` rather than reimplementing it.**
   OpenSpec ships six skills that already create and validate change folders.
   `crystallize` adds only what OpenSpec lacks: classification against existing
   truth, separating findings from decisions from assumptions from unknowns, the
   `intent.md` gate, ADR drafting, and surfacing conflicts with existing ADRs.

5. **`intent.md` lives inside the change folder** as a harness-owned extra file.
   It is not an OpenSpec artifact, so `openspec status` and `openspec validate`
   ignore it — acceptable, because its value is the two-commit gate structure and
   the two leading indicators readable straight from `git log` on the change
   folder: time from first conversation to accepted intent, and intent to spec.

6. **Local-model profiles and the advisor strategy were removed** (see the phase 0
   commit). The advisor was the named escape hatch for architectural ambiguity;
   its replacement is the human — agents stop and ask rather than guess.

7. **The repo is the source of truth for every artifact.** Any external tracker
   holds a commit SHA and links back. Stated so it survives future tool additions.

8. **`docs/harness/superpowers/specs/` was renamed to `design/`.** Those files are
   historical design notes, not behaviour contracts, and the name collided with
   the newly-canonical `openspec/specs/`. `docs/specs/` was considered and
   deliberately not created.

## Consequences

**Gained.** A living behaviour spec, so "what is currently true?" is answerable
without reading code. Review shrinks to a spec diff. Context loads lazily —
per-change, not per-project. Two cheap leading indicators fall out of git log.

**Cost.** A Node dependency (`openspec`, Node ≥ 20.19) in an otherwise pure
Python/uv harness — checked in `harness_setup.sh` as a warning, never a hard fail,
so everything else works without it. Two tools now write into `.claude/`, kept
apart by explicit path-prefix exclusions in both `generate_template_manifest.py`
and `setup_update.py`; `openspec update` owns its files, the manifest never
hashes them.

**Unresolved.** Capability granularity in `openspec/specs/` — the working
heuristic is *a capability is something you would plausibly rewrite or delete as a
unit*. Untested. Pressure-test it on the first two real changes before treating it
as settled.

`graphify` stays opt-in and unmodified. Its remaining distinct value is
cross-artefact impact discovery, which is unverified; revisit only after the loop
has run on a real change.
