# 04: Build and initialize a clean consumer template

**Status:** implemented — review pending

**Spec:** ../spec.md

**Blocked by:** 03: Finalize only accepted, current migration outputs

**What to build:**

- Audit tracked files into one positive inclusion manifest; build deterministic
     output with consumer README/Makefile/configuration, project-owned migration
     skill and required runtime. Keep maintainer suites/history out. Bootstrap
     missing install state at setup without resetting existing baselines. Test
     integrity, fresh initialization and consumer commands.
   - Ordering follows the requested phases so the payload packages the completed
     migration surface; there is no inherent architectural dependency on finalization.

- [x] Deliver the behavior described above and its approved acceptance criteria.
- [x] Add meaningful behavioral coverage at the approved seams.
- [x] Update applicable user documentation.
- [x] Pass targeted validation; record evidence and outstanding limitations.

## Comments

Published after explicit user approval of the breakdown. No commit or shipping authorization.

## Implementation evidence — 2026-09-23

- `make template DEST=<new-directory>` builds from the explicit positive mappings
  in `.engineering/template/files.json`, with consumer README, Makefile,
  configuration and test package marker. It reuses distribution fingerprint
  generation and validation, preserves executable modes and refuses existing
  destinations, symlinks, missing sources and unsafe paths.
- Runtime, pinned dependency inputs, the migration skill and legacy recognition
  baseline remain available. Maintainer suites, release scripts, tracker/history
  artifacts, installed dependencies and populated state are absent. This ticket
  retains the approved self-contained migration choice; v3.1b issue 06 revises it.
- Setup initializes missing state before network work. It verifies distribution
  bytes, preserves and validates existing baselines, and refuses corrupted state
  or customized uninitialized distributions. Consumer gates omit maintainer evals;
  dependency-install guidance distinguishes consumer checks from upstream checks.
- Public command tests cover repeatable payloads, fresh setup, repeat setup,
  doctor, normal application gates, downstream ticket tracking, migration
  inventory and refusal paths. Network installers are fixture executables;
  Engineering, Git and Python checks execute normally.
- A disposable generated project also completed real pinned dependency setup,
  repeat setup, doctor, `make check` and `make engineering-check`, with a tested
  application greeting and no manifest regeneration. The real run exposed the
  need for the test package marker, which is now part of the generated scaffold.
- Independent review and authoritative check evidence are recorded locally under
  `.engineering/state/verification/` for change `clean-consumer-template`.
  Optional authenticated prompt evals and remote template publication are excluded.

The current `/implement` invocation authorizes scoped local commits under
CLAUDE.md; it does not authorize push, PR creation or merge.
