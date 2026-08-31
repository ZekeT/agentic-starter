## 1. Test layout and configuration

- [x] 1.1 Write `docs/harness/testing.md` covering layout, the unit/integration/e2e
      decision rule, markers, fixtures, and manual-test recording; verify every
      command it shows actually runs
- [x] 1.2 Register `integration`, `e2e`, and `slow` markers in `pyproject.toml` and
      verify `pytest -m "not integration"` emits no unknown-marker warning
- [x] 1.3 Move the harness's own tests into `tests/unit/` and verify `make check`
      still passes with the corrected import paths

## 2. PR and commit conventions

- [x] 2.1 Add `.github/pull_request_template.md` with a required "How this was
      tested" section; verify `gh pr create` picks it up by default
- [x] 2.2 Update `/commit-push-pr` to fill the template rather than improvise a
      body, and to refuse when the test evidence is empty
- [x] 2.3 Point `REVIEW.md` Pass 4 at the PR template's evidence section

## 3. Make the convention discoverable to agents

- [x] 3.1 Add a short testing section to the `python-standards` skill pointing at
      `docs/harness/testing.md`; verify the skill still parses
- [x] 3.2 Add an eval asserting the layout, markers, and PR template stay in place,
      and verify it fails when each is removed
- [x] 3.3 Register the new files as template-owned in the manifest and the
      migration script; verify `make manifest` and the migration tests pass
