# 0003 — CLAUDE.md is the single agent-instruction file

- **Status**: Accepted
- **Date**: 2026-08-31

## Context

The template previously shipped two instruction files: `AGENTS.md`, following
the cross-tool convention that any coding agent reads it, and a thin `CLAUDE.md`
that pulled it in with `@AGENTS.md`. The stated goal was portability — a fork
using Cursor, Codex, or Aider would get the same project facts without editing
anything.

Three things worked against it.

**Two files meant two things to keep coherent.** The split was never clean in
practice: Claude Code-specific mechanics (hook wiring, `/crystallize`, the
worktree mutex) had nowhere natural to live, so they accumulated in whichever
file the last editor had open.

**`@import` loads eagerly.** The import pulled `AGENTS.md` into every session
before anything asked for it, so the two-file split bought no lazy loading — it
bought one file's worth of content spread across two files' worth of headers,
plus an eval budget that had to cover both.

**The starter is Claude Code-first and says so.** Hooks, agents, slash commands,
skills, and `configure.py` all target `.claude/`. Portability to a non-Claude
agent was never actually delivered by the second file; it was signalled by it.

The reversal itself was made during the 1.3.0 cleanup and left no record beyond
a line in `setup_update.py`'s manual-steps output telling downstream projects to
drop the file. A reversed decision with no ADR is exactly the case this
convention exists for.

## Decision

`CLAUDE.md` is the single agent-instruction file. `AGENTS.md` is not shipped,
and nothing in the template writes or imports one.

`scripts/configure.py` is the only automated writer, and it owns one section
(`## Active Model Config`) of one file. Eval 006 budgets that file at 120 lines
excluding the generated block, so the cost of the merge is visible and bounded:
adding to `CLAUDE.md` means cutting from it.

A fork targeting several agents can reintroduce `AGENTS.md` as a thin file that
imports nothing and restates the same facts. At that point the fork owns keeping
the two in sync — which is the cost this decision declines to pay by default,
not a capability the template forbids.

## Consequences

**Gained.** One file to keep true, one writer touching it, one budget governing
it. Claude Code-specific mechanics have an obvious home rather than drifting
between two files.

**Cost.** No out-of-the-box portability to non-Claude agents. A fork that needs
it does the duplication by hand and maintains it — the template offers no help
there, and no test catches the two files diverging.

**Not reopened by.** A fork adding `AGENTS.md` for its own reasons. This ADR
records what the *template* ships, not what a fork may do.
