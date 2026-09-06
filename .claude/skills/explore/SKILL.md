---
name: explore
description: >
  Turn messy exploration — a pasted chat transcript, scattered notes, or a
  one-line idea — into a single reviewable `intent.md`, gated before any spec
  is written. Use when someone has an idea they want to build, before any
  planning or code. Trigger on: /explore, "I want to build X", "turn this into
  a change", "here's a transcript, what now", "spec this out".
---

# Explore

Announce at start: **"Using explore to turn this into an intent."**

One stage, one artifact, one gate: this skill produces
`openspec/changes/<slug>/intent.md` and stops. `/crystallize` turns an accepted
intent into the proposal, delta specs, design and tasks. Never do both in one
turn — the gate between them is the cheapest possible point to kill or redirect
a bad idea, and it only works if it is a real stop.

Exploration is cheap and unstructured. Specs are expensive and precise. This
skill is the translation layer between them.

It does **not** reimplement OpenSpec. `openspec new change` creates the change
folder; this skill adds the four things it doesn't: classification against
existing truth, the separation pass, the intent gate, and conflict surfacing.

## Before you start

| Situation | Do |
|---|---|
| The *how* is the unresolved part | Stop. `/spike <slug> <question>` settles an approach into an ADR and a `design.md` first, and writes this intent itself. Speccing an approach nobody has tested produces tasks that dissolve on contact with the code. |
| `openspec/changes/<slug>/intent.md` exists | The intent is already written. Say so and point at `/crystallize <slug>`. Do not rewrite it. |
| `openspec/changes/<slug>/` exists without `intent.md` | A spike wrote `design.md` there. Read it, and let it inform the intent you are about to write — its "Still unknown" section becomes your Open questions. |
| The user wants to be interrogated properly | Invoke the `grilling` skill and work the design tree in rounds before writing anything. It settles far more than a single pass of questions. |

## 1. Read cheaply first

Read in this order and stop as soon as you can classify:

```bash
openspec list --specs                 # the spec index — names only
cat docs/product.md                   # what this product is and is not
cat docs/decisions/index.md           # what has already been decided
openspec list                         # changes already in flight
```

Open an individual `openspec/specs/<capability>/spec.md` **only** when the index
suggests it's relevant. Reading five specs to write one intent is the
eager-context failure this harness exists to avoid.

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

The classification you land on is written into `intent.md`, because
`/crystallize` writes the delta specs from it.

### Naming a new capability

Run these before committing to a name — reasoning in `.harness/docs/design.md`:

1. **Naming test.** State the Purpose in one sentence. Needing "and" to join
   unrelated activities, or a container noun (`core`, `platform`, `utils`,
   `management`), means it is too coarse. Split before writing.
2. **Independent-change test.** Name a realistic change touching only some of
   the requirements. If you can, that subset is its own capability.
3. **Not modules.** A capability may span modules and a module may serve several.
   A capability list mirroring the directory tree specs the implementation, and
   will churn on every refactor.

Prefer coarse to fine: too-coarse announces itself in the purpose sentence,
too-fine is quietly wrong forever and multiplies. Nest (`domain/capability`) only
once the flat list stops scanning, ~8–10 entries, and by domain never by layer.

Retiring a capability is not a delta: `openspec archive` refuses a spec with zero
requirements, so a split is an ADD for the new capabilities plus a `git rm` of the
old spec directory.

## 3. Separate the input

This is the work that makes exploration reviewable. Sort everything in the input
into these buckets, and keep them apart — most bad specs come from an assumption
wearing the costume of a decision:

- **Findings & evidence** — what is observably true. Cite where you know it from.
- **Decisions** — choices actually made, and by whom.
- **Assumptions** — believed but unverified. Every one is a risk; say what breaks if it's wrong.
- **Unknowns** — open questions. These go in `intent.md`, and `/crystallize` carries any that survive into `design.md`.
- **Requirements** — observable behaviour the system must exhibit. `/crystallize` turns these into delta specs.
- **Rejected alternatives** — what was considered and dropped, with the reason. This is what stops the same debate recurring in three months.

If the input contains no requirements — only opinions and vibes — say so and ask
for what's missing rather than inventing them.

## 4. Write the intent, then stop

Derive a kebab-case slug, then:

```bash
openspec new change <slug>
```

Write `openspec/changes/<slug>/intent.md` to the shape in
[INTENT-FORMAT.md](./INTENT-FORMAT.md). Carry the separation buckets into it —
the **Rejected alternatives** and surviving **Unknowns** are what `/crystallize`
turns into `design.md`, so losing them here costs the change its memory.

`intent.md` is harness-owned, not an OpenSpec artifact. `openspec status` and
`openspec validate` ignore it. That's fine: its value is the gate, and the two
leading indicators it makes readable from `git log` on the change folder — time
from first conversation to accepted intent, and intent to spec.

Commit it alone:

```bash
git add openspec/changes/<slug>/
git commit -m "feat(<slug>): intent"
```

**Then stop and hand back to the user**, naming the next command:

```
/crystallize <slug>
```

Do not write the proposal, the delta specs, or `tasks.md`. That is the next
stage, and it runs only on the user's say-so.

## Collisions

Never overwrite an existing change folder. If `openspec/changes/<slug>/` already
exists, either fold the input into it (when it's the same work) or pick a
distinct slug — and say which you did and why.
