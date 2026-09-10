---
name: handoff
description: Write a compact restart packet for an explicitly requested context transfer after an interruption.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

# Handoff

User-invoked only. Normal factory stages restart from accepted artifacts and
repository state; use this for exceptional interruptions, not as another plan.

Save a compact restart packet in the operating system's temporary directory,
then give the user its path. If arguments specify the next session's focus,
tailor the packet accordingly. Include:

- Goal
- Current stage
- Accepted artifacts (paths; distinguish drafts from accepted decisions)
- Current branch/change/group (FAST has a branch, no change/group)
- Decisions already made
- Open blockers
- Exact next action
- Files the next agent should read first (paths and relevant sections)

Reference specs, program design, task groups, ADRs and diffs by path or commit.
Do not copy large artifact contents, conversation history, or implementation
reasoning into the packet. Do not create a new implementation plan or recommend
another planning methodology. A verifier still receives only its prescribed
identifiers, never this implementation handoff. Omit secrets and sensitive data.
