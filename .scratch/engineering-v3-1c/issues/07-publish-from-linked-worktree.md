# 07: Publish safely from a linked Git worktree

**Spec:** Defect found while publishing v3.1c tickets 01, 02 and 04; not part of the [spec](../spec.md) slices.

**What to build:** `engineering publish run` works from a linked Git worktree
exactly as from a main checkout. Today, Git exports an absolute `GIT_DIR` (and
related variables) to hooks run inside a linked worktree. The publication
pre-push guard then runs nested Git commands against its temporary verification
clone (for example `git -C <clone> update-ref HEAD <base>`), which inherit that
environment and act on the worktree's repository instead: the publishing branch
is reset to the comparison base, content validation fails, and the push stops.
Nested Git commands run by Engineering tooling must target only the repository
they name.

**Blocked by:** None (can start immediately).

**Status:** implemented — awaiting independent verification

- [x] Nested Git commands started from the pre-push guard (and any other Engineering code path running inside Git hooks) ignore hook-provided repository environment such as `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_COMMON_DIR` and `GIT_PREFIX`, while the caller's original Git configuration handling is preserved.
- [x] Publishing from a linked worktree never moves the publishing branch or any other ref, and pushes the accepted commit.
- [x] A command-level fixture test publishes from a linked worktree to a local bare remote with a fake provider and asserts the branch ref is unchanged and the pushed head equals the accepted commit.
- [x] Existing publication behaviour and tests from a main checkout are unchanged.
- [x] Publication documentation notes linked-worktree support if wording is affected.
- [ ] `make check`, `make engineering-test` and `make engineering-evals` pass with independent review.

## Comments

- Implementation evidence (not verification or acceptance): root cause confirmed.
  Git exports an absolute `GIT_DIR` to hooks in a linked worktree; the guard's
  nested `git -C <verification clone> update-ref HEAD <base>` inherited it and
  reset the publishing branch. `pre_push_guard` now drops hook-provided
  repository variables (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`,
  `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`,
  `GIT_PREFIX`) after the original hook runs with Git's environment and before
  Engineering's own nested work; `GIT_CONFIG_PARAMETERS` handling is unchanged.
  `integration/test_publication_worktree.py` failed before the fix with the
  observed "Committed content differs" stop and passes after it. All 44
  publication integration tests pass; `make check`, `make engineering-evals` (11/11)
  and `make engineering-test` (318 passed) pass locally. Remaining: independent review and human acceptance.
