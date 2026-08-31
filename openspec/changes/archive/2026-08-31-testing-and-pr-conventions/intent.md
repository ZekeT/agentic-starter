# Intent: testing-and-pr-conventions

## Problem
The harness has no stated testing convention and no PR template. Three concrete
consequences:

- `docs/harness/coding-standards.md` has no testing section at all, and neither
  does the `python-standards` skill. An agent writing tests has nothing to follow,
  so every session invents its own layout.
- `tests/` is flat, with no distinction between tests that are fast and
  dependency-free and tests that cross a real boundary. There is no way to run
  only the fast ones.
- `/commit-push-pr` opens PRs with an ad-hoc body. Nothing requires the author to
  say how the change was verified, so `REVIEW.md`'s Pass 4 (Tests) has nothing to
  check against beyond the diff itself.

## Proposed outcome
A test layout and a PR template that every change follows by default, with
"how this was tested" a required field rather than a habit.

## Affected users and systems
Everyone using the harness, and every downstream project created from it.
`/commit-push-pr`, `REVIEW.md`, `pyproject.toml`, and the `python-standards`
skill all change.

## Constraints
- Must not add a dependency; pytest is already present.
- Must not slow `make check` for a project with no integration tests.
- The PR template must work for a human opening a PR by hand, not only for an
  agent — so it belongs at `.github/pull_request_template.md` where GitHub picks
  it up automatically.

## Open questions
None material. The unit/integration/e2e split and pytest markers are settled
convention, not a novel design.

## Areas of concern
The harness's own `tests/` is currently flat, so adopting this makes the template
violate its own standard until it is restructured. The change therefore has to
move the existing tests, not just document the target.
