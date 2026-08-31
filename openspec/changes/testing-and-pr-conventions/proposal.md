## Why
An agent follows what is written down and enforced. Testing conventions are
currently neither: there is no testing section anywhere in the harness, and PR
bodies have no required verification evidence. `REVIEW.md` Pass 4 asks whether
new behaviour has a test, but nothing makes the author state how they checked.

## What Changes
- Adds `docs/harness/testing.md`: layout, the unit/integration/e2e decision rule,
  pytest markers, fixture placement, and how to record a manual test.
- Adds a testing section to the `python-standards` skill (agent-facing, short).
- Adds `.github/pull_request_template.md` with a required "How this was tested"
  section covering unit, integration, and manual.
- Registers pytest markers in `pyproject.toml` and splits `testpaths`.
- Restructures the harness's own `tests/` into `tests/unit/` so the template
  follows its own convention.
- `/commit-push-pr` fills the PR template rather than improvising a body.
- Not architecture-affecting.

## Capabilities

### New Capabilities
- `contribution-conventions`: how changes are tested, committed, and proposed

### Modified Capabilities

## Impact
`pyproject.toml`, `tests/`, `.github/`, `docs/harness/`, the `python-standards`
skill, `/commit-push-pr`, and `REVIEW.md`. No runtime code; no new dependency.
