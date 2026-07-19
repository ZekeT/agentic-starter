# Design: Align template with BMAD 6.10 and Superpowers 6.1

Date: 2026-07-20
Status: approved (full-alignment option)

## Problem

- BMAD runtime is current (6.10.0), but the trimmed skill set and commands still
  use `bmad-create-prd` / `bmad-create-architecture`, which 6.10 marks DEPRECATED
  and v7 will remove. The replacement skills (`bmad-prd`, `bmad-architecture`)
  were deleted by the trim step, so the template ships shims that forward to
  skills that no longer exist on disk.
- Superpowers docs describe v5 behaviour (two-stage code review). v6 (latest
  6.1.1) uses a unified single-pass task reviewer, moved SDD scratch files to
  `.superpowers/sdd/`, and cut token usage ~50%. Skill names are unchanged.
- BMAD runtime scripts (`_bmad/scripts/resolve_customization.py`) require
  Python ≥ 3.11 (`tomllib`); the system python3 on macOS is 3.9.6.

## Changes

1. `scripts/trim_bmad_skills.py` — KEEP list swaps `bmad-create-prd` →
   `bmad-prd` and `bmad-create-architecture` → `bmad-architecture`; docstring
   and roles table updated.
2. `.claude/skills/` — install `bmad-prd` and `bmad-architecture` verbatim from
   the bmad-method 6.10.0 package (equivalent to `npx bmad-method install` +
   re-trim); delete the two deprecated shim stubs.
3. `.claude/commands/prd.md`, `architecture.md` — invoke the new skill names.
4. `CLAUDE.md` — command→stub tables, structure listing, v6 reviewer wording,
   rule about Python ≥ 3.11 for `_bmad/scripts/*.py`.
5. `docs/SETUP.md` — structure tree, staying-updatable section, Superpowers
   update instructions (v6+), Python note.
6. `setup.sh` — system-python warning in the BMAD step; `/plugin update` hint
   for machines with an older Superpowers install.
7. `.gitignore` — add `.superpowers/` (v6 SDD scratch dir).

## Out of scope

- Adopting BMAD 6.10 implementation skills (bmad-code-review, bmad-dev-story):
  implementation remains Superpowers' job in this template.
- Updating the Superpowers plugin itself — global, interactive
  (`/plugin update superpowers@superpowers-marketplace`), user action.
