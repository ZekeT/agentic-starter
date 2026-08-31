---
name: crystallize
description: >
  Turn messy exploration — a pasted chat transcript, scattered notes, or a
  one-line idea — into a reviewable OpenSpec change, gated in two commits:
  intent first, spec second. Use when someone has an idea they want to build,
  before any planning or code. Trigger on: /crystallize, "turn this into a
  change", "spec this out", "I want to build X", "here's a transcript, what
  now".
---

# Crystallize

Announce at start: **"Using crystallize to turn this into an OpenSpec change."**

Exploration is cheap and unstructured. Specs are expensive and precise. This
skill is the translation layer between them — and the point where a bad idea is
cheapest to kill.

It does **not** reimplement OpenSpec. `openspec new change` and the
`openspec-propose` skill create and populate change folders; this skill adds the
five things they don't: classification against existing truth, the separation
pass, the intent gate, ADR drafting, and conflict surfacing.

Never write to `openspec/specs/` — that only ever changes at archive time.

## 1. Read cheaply first

Never bulk-read `openspec/` or `docs/`. Read in this order and stop as soon as
you can classify:

```bash
openspec list --specs                 # the spec index — names only
cat docs/product.md                   # what this product is and is not
cat docs/decisions/index.md           # what has already been decided
openspec list                         # changes already in flight
```

Open an individual `openspec/specs/<capability>/spec.md` **only** when the index
suggests it's relevant. Reading five specs to write one change is the eager-context
failure this harness exists to avoid.

## 2. Classify against current truth

Decide which of these the input is, and say so out loud before writing anything:

| Classification | What to do |
|---|---|
| **New capability** | Proceed. It becomes a new `specs/<capability>/spec.md` delta. |
| **Modification** of an existing capability | Proceed, but name the exact existing capability path. Only a real change in *behaviour* counts — an implementation change with identical observable behaviour is not a spec change. |
| **Architectural decision** | Draft an ADR in `docs/decisions/`. It may also need a change; often it doesn't. |
| **Already covered** by an existing spec | **Say so and stop.** Cite the capability and requirement. Do not open a redundant change. |
| **Conflicts** with an existing ADR or spec | **Surface the conflict and stop.** Name what it contradicts. The user decides whether to supersede the ADR or drop the idea — never silently override a recorded decision. |
| **Non-goal** in `docs/product.md` | Say so and stop, unless the user is explicitly revising the non-goal. |

Also check `openspec list`: if an in-flight change already covers this, fold it
in there rather than opening a second one.

## 3. Separate the input

This is the work that makes exploration reviewable. Sort everything in the input
into these buckets, and keep them apart — most bad specs come from an assumption
wearing the costume of a decision:

- **Findings & evidence** — what is observably true. Cite where you know it from.
- **Decisions** — choices actually made, and by whom.
- **Assumptions** — believed but unverified. Every one is a risk; say what breaks if it's wrong.
- **Unknowns** — open questions. These go in `intent.md` and, if unresolved, `design.md`.
- **Requirements** — observable behaviour the system must exhibit. These become delta specs.
- **Rejected alternatives** — what was considered and dropped, with the reason. Goes in `design.md`; this is what stops the same debate recurring in three months.

If the input contains no requirements — only opinions and vibes — say so and ask
for what's missing rather than inventing them.

## 4. Commit 1 — intent (STOP HERE)

Derive a kebab-case slug, then:

```bash
openspec new change <slug>
```

Write `openspec/changes/<slug>/intent.md`:

```markdown
# Intent: <slug>

## Problem
What is wrong today. Observable, not aspirational. If you can't state the
problem without naming the solution, you don't have one yet.

## Proposed outcome
What is true after this ships. Still no implementation.

## Affected users and systems
Who notices, and what else this touches.

## Constraints
Budget, compatibility, deadline, regulatory — anything that bounds the solution.

## Open questions
The unknowns from step 3. Empty is a red flag on anything non-trivial.

## Areas of concern
Conflicts with existing ADRs, specs, or policies encoded in skills. State them
here even if you think they're acceptable — this is the section a reviewer
reads first.
```

`intent.md` is harness-owned, not an OpenSpec artifact. `openspec status` and
`openspec validate` will ignore it. That's fine: its value is the gate and the
two leading indicators it makes readable from `git log` on the change folder —
time from first conversation to accepted intent, and intent to spec.

Commit it alone:

```bash
git add openspec/changes/<slug>/
git commit -m "feat(<slug>): intent"
```

**Then stop and hand back to the user.** Do not write the proposal in the same
turn. This gate is the cheapest possible point to kill or redirect a bad idea,
and it only works if it's a real stop.

## 5. Commit 2 — spec (only after intent is accepted)

Delegate the artifact generation to OpenSpec rather than hand-rolling it:

```bash
openspec instructions proposal --change <slug>
openspec instructions specs --change <slug>
openspec instructions design --change <slug>
openspec instructions tasks --change <slug>
```

Follow those instructions, carrying across the buckets from step 3:

- **`proposal.md`** — why, what changes, capabilities (New/Modified), impact.
  State explicitly whether the change is **architecture-affecting**; `/dev-change`
  keys off that to decide whether to load `docs/architecture.md`.
- **Delta specs** — requirements as observable behaviour, each with at least one
  `#### Scenario:` block using WHEN/THEN. No internal class or library names.
- **`design.md`** — the unknowns and rejected alternatives from step 3, plus how.
- **`tasks.md`** — each `## N` group must be **independently shippable**: one
  group = one branch = one PR under `/dev-change`. If a group can't ship alone,
  regroup until it can.

Where the work settled a durable architectural question, also draft
`docs/decisions/NNNN-slug.md` (Context / Decision / Consequences) and add its row
to `docs/decisions/index.md`.

Validate before handing back:

```bash
openspec validate <slug>
```

A change with no spec-level behaviour change (pure refactor, tooling, docs) must
set `skip_specs: true` in its `.openspec.yaml`. Never invent a requirement just
to satisfy the validator.

```bash
git add openspec/changes/<slug>/ docs/decisions/
git commit -m "feat(<slug>): proposal, specs, design, tasks"
```

## 6. Stop at the gate

Report the change slug, its task groups, and any areas of concern. Then stop.

**Never run `/dev-change` yourself.** Accepting the spec is the user's gate, and
implementation begins only on their explicit next instruction.

## Collisions

Never overwrite an existing change folder. If `openspec/changes/<slug>/` already
exists, either fold the input into it (when it's the same work) or pick a
distinct slug — and say which you did and why.
