---
name: crystallize
description: >
  Turn an accepted `intent.md` into the OpenSpec change artifacts — proposal,
  delta specs, design, and independently-shippable task groups — ready for
  /dev-change. Runs after the intent gate, never before it. Trigger on:
  /crystallize, "write the spec", "turn the intent into a change", "generate
  the tasks".
---

# Crystallize

Announce at start: **"Using crystallize to spec `<slug>`."**

One stage, one gate: this skill reads an accepted `intent.md` and writes
`proposal.md`, `specs/`, `design.md` and `tasks.md`. `/explore` wrote the
intent; `/dev-change` consumes the tasks.

## Preflight

| On disk in `openspec/changes/<slug>/` | Do |
|---|---|
| `intent.md`, no `proposal.md` | Proceed. This is the normal case. |
| `intent.md` **and** `design.md` | A `/spike` settled the *how*. Treat `design.md` as authored: build the specs and tasks around it and extend it if speccing reveals more — never rewrite it. |
| `proposal.md` already present | The change is already specced. Say so, name its task groups, and stop. |
| no `intent.md` | Stop. Run `/explore` first — speccing an unaccepted intent skips the gate that makes a bad idea cheap to kill. |

Read `intent.md` before anything else. Its **Classification** line names the
capability path these deltas attach to, and its **Open questions** are the
unknowns `design.md` must carry.

## 1. Generate the artifacts

Delegate generation to OpenSpec rather than hand-rolling it:

```bash
openspec instructions proposal --change <slug>
openspec instructions specs --change <slug>
openspec instructions design --change <slug>
openspec instructions tasks --change <slug>
```

Follow those instructions, carrying the intent across:

- **`proposal.md`** — why, what changes, capabilities (New/Modified), impact.
  State explicitly whether the change is **architecture-affecting**;
  `/dev-change` keys off that to decide whether to load `docs/architecture.md`.
- **Delta specs** — requirements as observable behaviour, each with at least one
  `#### Scenario:` block using WHEN/THEN. No internal class or library names.
- **`design.md`** — the intent's open questions and rejected alternatives, plus
  how. If a spike already wrote this file, extend it rather than replacing it.
- **`tasks.md`** — each `## N` group must be **independently shippable**: one
  group = one branch = one PR under `/dev-change`. If a group can't ship alone,
  regroup until it can.

Where the work settled a durable architectural question, also draft
`docs/decisions/NNNN-slug.md` (Context / Decision / Consequences) and add its row
to `docs/decisions/index.md`.

## 2. Validate

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

## 3. Stop at the gate

Report the change slug, its task groups, and any areas of concern. Then stop,
naming the next command:

```
/dev-change <slug> 1
```

**Never run `/dev-change` yourself.** Accepting the spec is the user's gate, and
implementation begins only on their explicit next instruction.
