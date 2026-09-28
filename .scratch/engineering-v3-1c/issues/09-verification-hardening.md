# 09: Harden verification requirement edge cases

**Spec:** Follow-ups from independent reviews of tickets 03 and 05; not part of the [spec](../spec.md) slices.

**What to build:** Close the non-blocking gaps reviewers found in role- and
ownership-based verification requirements and dependency handling, each with a
command-level test, without reopening the settled Decisions in ticket 03.

**Blocked by:** 03 (merged).

**Status:** needs-triage

- [ ] Executable-bit-only changes: a consumer change that only flips the executable mode of a `file`-owned managed path is rejected like a content change (compare mode against the base), or the verification guide is narrowed to say content only. Decide which (ticket 03 security and behavioral reviews).
- [ ] Plan base: verification refuses or clearly reports a comparison base that is not the configured default branch (e.g. a plan whose base is the feature branch itself hides committed changes). Decide the rule; the base and tip are already recorded in evidence (ticket 03 security review).
- [ ] Maintainer new files: in the maintainer checkout, a new file under a distributed tooling location not yet in the manifest (e.g. `.engineering/engineering/`, `.engineering/docs/`) is treated as maintainer source rather than an ordinary project path (ticket 03 behavioral review).
- [ ] Non-Graft npm dependencies: `deps` no longer installs every npm dependency the Graft way, and an npm dependency without a content owner is not reported OK without checking that the package is installed (ticket 05 behavioral review; unreachable today because the registry only allows Graft).
- [ ] Dependency-owned content: after navigation content moved to Graft dependency outputs, consumer edits to `.engineering/bin/graft`, `.engineering/graft/package*.json` and `.engineering/state/dependencies.json` need only `make check`; adopted projects may not run doctor. Classify dependency-owned outputs and dependency state as managed integration so they require `make engineering-check` (ticket 05 security review).
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments
