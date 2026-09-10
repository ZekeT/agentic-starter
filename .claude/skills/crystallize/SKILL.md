---
name: crystallize
description: >
  Turn accepted intent into proposal, delta specs and design. STANDARD also
  generates task groups; DEEP stops for architecture approval before shape-change.
  Use /crystallize after the intent gate, never to skip exploration.
---

# Crystallize

Announce: **"Using crystallize to spec `<slug>`."**

Read `openspec/changes/<slug>/intent.md` first. If absent or not accepted, stop
and direct the user to `/explore` and its intent gate. Read only relevant
canonical capability specs and recorded decisions. Never edit `openspec/specs/`.

Read the intent's `Workflow:` and `Reason:`. Existing intents without a tier
remain STANDARD unless new complexity warrants promotion; surface that promotion.
FAST behavior-neutral work needs no crystallize stage or OpenSpec change.
Never silently demote DEEP after architectural uncertainty has been identified.

If `proposal.md` already exists, do not overwrite accepted artifacts. For DEEP
without final tasks, report the architecture/spec gate and `/shape-change <slug>`.
For an already populated STANDARD `tasks.md`, report its groups and the next
`/dev-change` command; it does not need program design. If artifacts are partly
written, show what is missing and ask whether to resume rather than inventing
acceptance of unfinished work.

## Generate the shared artifacts

Use OpenSpec's artifact instructions:

```bash
openspec instructions proposal --change <slug>
openspec instructions specs --change <slug>
openspec instructions design --change <slug>
```

- `proposal.md`: why, changes, new/modified capabilities, impact. State whether
  it is architecture-affecting and record the workflow tier.
- Delta `specs/`: observable requirements and `#### Scenario:` WHEN/THEN cases.
  Carry requirements from intent and cite the affected current capability.
- `design.md`: approach, architectural decisions, rejected alternatives,
  evidence, and surviving unknowns. Preserve and extend an existing spike's
  findings rather than replacing them. Record durable decisions as ADRs using
  `docs/decisions/index.md`'s convention when relevant.

For spec-less architecture/tooling work, follow the repository's `skip_specs`
convention; never invent behavior to appease validation.

## STANDARD: generate tasks

```bash
openspec instructions tasks --change <slug>
```

Create `tasks.md` with `## N.` groups and `- [ ] N.M ...` claims. Each group
must be a vertical, independently shippable slice: one group = one branch = one
PR. Include behavior, integration, and tests together. Add a short `Context:`
list of relevant spec scenarios and design sections per group, plus prerequisite
groups when applicable. A fresh implementer should need only that group and its
referenced sections. The group is the plan; do not add a second planning file.

Validate with `openspec validate <slug>`. Present proposal, specs, design and
task groups at the human gate. Stop and name `/dev-change <slug> 1` as next.

## DEEP: architecture gate before shaping

Generate proposal, delta specs and architectural design only. Do not generate
final `tasks.md` or run the tasks artifact instruction in this stage.
`design.md` covers architectural approach and decisions, not implementation by
file; implementation types, files and test design belong in program design.

Validate the available change artifacts with `openspec validate <slug>`.
Missing final tasks is expected at this stage; never manufacture tasks merely
to mark the change implementation-ready. Report real validation errors.

STOP at the human architecture/spec gate. Present the design, evidence and
unresolved decisions, then direct the user to `/shape-change <slug>` after
acceptance. Do not start shaping or implementation yourself.

Artifact commits require human approval. A new session can begin from these
accepted artifacts and repository state; it needs no exploration transcript.
