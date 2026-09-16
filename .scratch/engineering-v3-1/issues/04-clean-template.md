# 04: Build and initialize a clean consumer template

**Status:** ready-for-agent

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

- [ ] Deliver the behavior described above and its approved acceptance criteria.
- [ ] Add meaningful behavioral coverage at the approved seams.
- [ ] Update applicable user documentation.
- [ ] Pass targeted validation; record evidence and outstanding limitations.

## Comments

Published after explicit user approval of the breakdown. No commit or shipping authorization.
