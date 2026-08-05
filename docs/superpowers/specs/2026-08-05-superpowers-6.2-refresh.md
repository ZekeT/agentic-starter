# Design: Refresh template for Superpowers 6.2.0

Date: 2026-08-05
Status: approved

## Problem

- BMAD runtime is already current: locally installed `_bmad/` and npm both
  report `6.10.0` as latest (only `6.10.1-next.*` prereleases exist beyond
  it). No template changes needed on the BMAD side.
- Superpowers has moved from 6.1.1 (the version [[2026-07-20 alignment
  design]] targeted) to 6.2.0, latest per `git ls-remote --tags
  obra/superpowers`. Locally cached plugin data was stale at 5.1.0 — a
  per-machine `/plugin update` issue, not a template issue.
- v6.2.0's only externally-visible change relevant to this template: the SDD
  scratch workspace is now plan-scoped (`.superpowers/sdd/<plan-basename>/`
  instead of a flat `.superpowers/sdd/`), fixing cross-plan ledger
  contamination. Skill names, install commands, and marketplace/plugin names
  are all unchanged since 6.1.1.

## Changes

1. `CLAUDE.md` — bump "Superpowers v6+" to "v6.2+"; describe the SDD scratch
   path as plan-scoped (`.superpowers/sdd/<plan-basename>/`).
2. `docs/SETUP.md` — same version bump and SDD path wording; note 6.2+ is
   latest as of 2026-08-05.
3. `setup.sh` — bump the `/plugin update` hint from "v6+" to "v6.2+".
4. `template-manifest.json` / `TEMPLATE_VERSION` — regenerated, patch bump
   (1.0.0 → 1.0.1) since only wording in template-owned docs/scripts changed,
   no structural changes.

## Out of scope

- Bumping BMAD version references — already current.
- Updating the Superpowers plugin itself — global, interactive, per-machine
  user action (`/plugin update superpowers@superpowers-marketplace`).
- Adopting any new Superpowers skills — 6.2.0 didn't add or rename any.
