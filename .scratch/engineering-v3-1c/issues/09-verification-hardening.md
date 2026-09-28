# 09: Harden verification requirement edge cases

**Spec:** Follow-ups from independent reviews of tickets 03 and 05; not part of the [spec](../spec.md) slices.

**What to build:** Close the non-blocking gaps reviewers found in role- and
ownership-based verification requirements and dependency handling, each with a
command-level test, without reopening the settled Decisions in ticket 03.

**Blocked by:** 03 (merged).

## Decisions (triage 2026-09-28, human-approved)

- **Executable bit:** compare the file mode against the base; a mode-only change to a consumer `file`-owned managed path is rejected like a content change. Docs keep "any change".
- **Plan base:** the plan base must be the configured `[verification] base_branch` (or its remote-tracking equivalent). Any other base fails unless the plan states an explicit reason, which is recorded in the evidence.
- **Maintainer new files** and **dependency-owned content:** do as described below.
- **Non-Graft npm dependencies:** deferred (`wontfix` for now) until a second npm dependency exists; unreachable today.

**Status:** ready-for-agent

- [ ] Executable-bit-only changes: a consumer change that only flips the executable mode of a `file`-owned managed path is rejected like a content change (mode compared against the base) (ticket 03 security and behavioral reviews).
- [ ] Plan base: verification refuses a comparison base other than the configured `[verification] base_branch` or its remote-tracking equivalent unless the plan states a reason, recorded in evidence (e.g. a base equal to the feature branch hides committed changes) (ticket 03 security review).
- [ ] Maintainer new files: in the maintainer checkout, a new file under a distributed tooling location not yet in the manifest (e.g. `.engineering/engineering/`, `.engineering/docs/`) is treated as maintainer source rather than an ordinary project path (ticket 03 behavioral review).
- [ ] ~~Non-Graft npm dependencies~~ (deferred by triage): `deps` no longer installs every npm dependency the Graft way, and an npm dependency without a content owner is not reported OK without checking that the package is installed (ticket 05 behavioral review; unreachable today because the registry only allows Graft).
- [ ] Dependency-owned content: after navigation content moved to Graft dependency outputs, consumer edits to `.engineering/bin/graft`, `.engineering/graft/package*.json` and `.engineering/state/dependencies.json` need only `make check`; adopted projects may not run doctor. Classify dependency-owned outputs and dependency state as managed integration so they require `make engineering-check` (ticket 05 security review).
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments
