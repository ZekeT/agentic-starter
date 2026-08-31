# Testing

How tests are organised and what belongs where. Python-centric; the layout ideas
carry to other stacks, the tooling does not.

The agent-facing short version lives in the `python-standards` skill. This is the
full reference.

---

## Layout

```
tests/
  conftest.py              # fixtures shared by every suite — keep it small
  unit/                    # mirrors src/ layout
    conftest.py
    <package>/
      test_<module>.py
  integration/             # crosses a real boundary
    conftest.py
    test_<subsystem>.py
  e2e/                     # optional: whole system via its public entrypoint
    test_<journey>.py
```

`tests/unit/` mirrors `src/` one-for-one. When a reviewer opens
`src/billing/invoice.py`, they should be able to guess that its tests are at
`tests/unit/billing/test_invoice.py` without looking. Integration and e2e are
organised by subsystem or user journey instead, because they rarely map to a
single module.

## Which folder does this test go in?

Decide by **what the test touches**, never by what it is called. The question is
not "is this testing one function?" but "what has to exist for this to run?"

| | `unit/` | `integration/` | `e2e/` |
|---|---|---|---|
| Filesystem, network, DB, subprocess | never | yes, real ones | yes |
| Test doubles | yes, for collaborators you own | only for third parties you don't control | none |
| Typical runtime | < 10ms | < 1s | seconds |
| Fails when a service is down | no | yes, and that's correct | yes |
| Entry point | one module's public API | a subsystem's seam | the system's public entrypoint |

The rule that resolves most arguments: **if it can fail because something outside
the process is unavailable, it is not a unit test.** A test using `tmp_path` is
touching a real filesystem, so it is an integration test even though it looks
small and runs fast. That is not pedantry — it is the difference between a suite
you can trust on a plane and one you cannot.

Mocking a real boundary to keep a test in `unit/` is usually the wrong trade. It
couples the test to the implementation and stops proving the boundary works. Put
it in `integration/` and let it use the real thing.

## Markers

Registered in `pyproject.toml`, so category selection never depends on paths:

```bash
pytest                                   # everything (make test)
pytest -m "not integration and not e2e"  # fast feedback while working
pytest -m integration                    # just the boundary-crossing ones
pytest -m "not slow"                     # skip anything deliberately expensive
```

`--strict-markers` is on: an unregistered marker is an error, not a silent
typo that quietly selects nothing.

```python
import pytest


@pytest.mark.integration
def test_writes_invoice_to_disk(tmp_path): ...


@pytest.mark.slow
@pytest.mark.integration
def test_full_reconciliation_run(): ...
```

Mark by hand rather than by directory. Being explicit at the test is what makes
a misplaced test visible in review.

## Fixtures

- Put a fixture in the **narrowest** `conftest.py` that serves it. A fixture used
  by one file belongs in that file.
- Root `conftest.py` is for things genuinely universal. It is loaded for every
  test, so anything expensive there taxes the whole suite.
- Default to function scope. Widen to `session` only when construction is
  genuinely expensive, and only for something immutable — a shared mutable
  fixture creates order-dependent tests, which fail in ways that waste hours.
- Name fixtures as nouns (`invoice`, `db_session`), tests as behaviours.

## Naming

```python
def test_rejects_negative_amount(): ...        # behaviour + condition
def test_retries_three_times_then_raises(): ...
```

Not `test_invoice_1`, not `test_it_works`. The name is what a reader sees in the
failure output, and it should say what broke without opening the file.

Files are `test_<module>.py`, classes `Test<Thing>`, functions `test_<behaviour>`.
Group with a class only when tests share fixtures; a class purely for tidiness
adds indentation and nothing else.

## What to test

- **The failure path**, not just the happy one. Untested error handling is where
  bugs live, and it is the most commonly skipped case.
- **Boundaries**: empty, one, many, and one past the limit.
- **Observable behaviour**, not internals. If the test breaks when you rename a
  private method without changing what the code does, it is testing the wrong
  thing and will punish every future refactor.
- New behaviour needs a test that **fails without the change**. Write it first,
  watch it fail, then make it pass — otherwise you have not proven it tests
  anything.

Do not test third-party libraries, or code that only wires other code together
with no logic of its own.

## Manual tests

Some things resist automation: a rendered UI, a third-party sandbox, a migration
against a production-sized dataset. Manual verification is legitimate, but it is
only evidence if it is **recorded**.

In the PR's "How this was tested" section, write the steps and the observed
result:

```
Manual:
1. `make run`, opened http://localhost:8000/invoices
2. Created an invoice for -5.00
3. Observed: form rejected with "Amount must be positive"; no DB row written
```

Not "tested manually" or "works locally" — neither tells a reviewer what was
covered, so neither is checkable.

If something needs manual testing *every* release, that is a gap worth an
automated test. Note it in the PR so it can become one.

## Coverage

`make check` reports coverage but does not gate on it, deliberately. A coverage
threshold reliably produces tests written to raise the number rather than to
catch bugs.

Use it as a **signal**: an uncovered branch is a question ("should this be
tested?"), not a defect. The answer is sometimes no.

To gate coverage in a mature project, add `--cov-fail-under=N` to `addopts` in
`pyproject.toml`. Set N to slightly below where you already are, and raise it
when it is comfortably exceeded — a threshold above the current number just
blocks everyone until someone writes filler tests.

## Running

```bash
make test                                # full suite, with coverage
make check                               # fmt + lint + test — the commit gate
uv run pytest tests/unit -q              # fast loop while working
uv run pytest -k invoice                 # by name
uv run pytest --lf                       # only what failed last run
uv run pytest -x -vv                     # stop at first failure, verbose
```
