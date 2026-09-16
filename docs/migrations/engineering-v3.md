# Engineering System v3 migration summary

## Before

Repository-owned Factory/Harness workflow, OpenSpec lifecycle, workflow tiers,
vendored methodology skills and coupled setup/update instructions.

## After

Matt Pocock's pinned upstream skills own the workflow. The Engineering System
owns repository policy, checks, reviews, Graft integration and safe maintenance.
Local Markdown is the default tracker, independent of the Git hosting provider.
Large coding work follows `/wayfinder` → `/to-spec` → `/to-tickets` → `/implement`.

## Removed

- Factory/Harness runtime names, old lifecycle commands and workflow tiers.
- OpenSpec runtime and Superpowers project integration.
- Vendored methodology skills and Wayfinder Maps as a default dependency.

## Retained

- `make check`, maintainability checks, four Claude hooks and Graft navigation.
- Read-only maintainability/security reviewers, independent verifier and human shipping authorization.
- Ownership-aware adoption and three-way updates that preserve project changes.

## Added

- `ENGINEERING.md`, `engineering` CLI and `.engineering/` configuration/runtime.
- Pinned dependency registry with separate status, plan, install and update operations.
- Offline doctor; optional show-me and Karpathy skill installation.
- Plan-first OpenSpec and v2 starter migrations with clean-Git preconditions,
  conflict checks, source evidence, rollback and repeat-run validation.

## Manual migration actions

1. Commit existing work in the target repository. Review the default migration
   plan from a v3 checkout before explicitly applying it. See
   [migration commands](../../ENGINEERING.md) for both migration routes.
2. Reconcile reported customized managed files; preserve project-specific policy
   from the saved legacy documentation. Unknown project files and global tools
   remain project-owned.
3. Review extracted OpenSpec context candidates and active-change packages.
   Decide their final specs/tickets through Matt's configured tracker; extraction
   does not authorize implementation or infer architectural decisions.
4. Run `./engineering deps install --apply`, configure Graft application roots,
   then run `./engineering doctor` and the project's native checks.
5. Inspect the diff and migration report before committing. Migration is one-way;
   recovery uses the recorded pre-migration Git commit and listed new paths.

This starter's OpenSpec sources use Git history for preservation. Its migration
report and extracted review packages are checked in under `.engineering/migrations/`
and `docs/migrations/openspec/`. The runtime defaults other migrations to snapshots.

Wayfinder Maps is an optional ecosystem alternative only. There is no translator,
dual-write mechanism or modification of Matt's tracker format.
