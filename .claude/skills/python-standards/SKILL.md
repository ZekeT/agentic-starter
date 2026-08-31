---
name: python-standards
description: >
  Project Python conventions to apply when writing or reviewing Python code in
  this repo. Covers only what a linter doesn't already catch — layering,
  validation, exception handling, naming, docstring style. `make check`
  (black/isort/mypy/interrogate/pytest) enforces everything else; this skill
  doesn't repeat it.
---

# Python Standards

Full reference with rationale and examples: `docs/harness/coding-standards.md`.
Testing layout and conventions: `docs/harness/testing.md`.
This skill is the trimmed, agent-facing version — only the rules `make check`
can't verify for you.

## Separation of concerns

- API layer: request/response handling, validation, routing — nothing else.
- Service layer: business logic, orchestration.
- Data layer: database access, external APIs.
- Never put database queries in API handlers. Never put business logic in models.

## Data validation

- Use `pydantic` (preferred) or `marshmallow` to validate external data (API
  payloads, config) at the boundary. Never trust unvalidated external input.

## Exception handling

- Never use bare `except:` — it catches `SystemExit` and `KeyboardInterrupt`.
- Catch the most specific exception type possible.
- Always log or re-raise — don't silently swallow exceptions.

```python
# Bad
try:
    result = fetch(url)
except:
    pass

# Good
try:
    result = fetch(url)
except httpx.TimeoutException as e:
    logger.warning("Request timed out: %s", e)
    raise
```

## Subprocess and paths

- No `os.system()` — use `subprocess.run()` with explicit args and `check=True`.
- Always use `pathlib.Path`, not string concatenation, for file paths.

## Naming

| Kind | Convention |
|------|-----------|
| Variables & functions | `snake_case`, descriptive, no single-letter names except loop counters |
| Classes | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` |
| Booleans | `is_`, `has_`, `can_` prefix (`is_valid`, `has_token`) |
| Functions | named as verbs (`fetch_user()`, `validate_payload()`), not nouns |

## Docstrings (Google style)

```python
def fetch_user(user_id: int) -> User:
    """Fetch a user record by ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The User object matching the given ID.

    Raises:
        UserNotFoundError: If no user exists with that ID.
    """
```

One-line docstrings are fine for trivial functions:
`"""Return the user's full name."""`

## Tests

Layout — full reference in `docs/harness/testing.md`:

```
tests/unit/          mirrors src/; no I/O, no network, no subprocess
tests/integration/   crosses a real boundary; mark @pytest.mark.integration
tests/e2e/           optional; whole system via its public entrypoint
```

Which folder is decided by **what the test touches**, not what it is named. If it
can fail because something outside the process is unavailable, it is not a unit
test — and that includes `tmp_path`, which is a real filesystem.

Don't mock a real boundary to keep a test in `unit/`. That couples the test to
the implementation and stops proving the boundary works; put it in
`integration/` and use the real thing.

- Name tests for the behaviour: `test_rejects_negative_amount`, never
  `test_invoice_1`.
- New behaviour needs a test that **fails without the change** — write it first
  and watch it fail, or you haven't shown it tests anything.
- Test the failure path and the boundaries (empty, one, many, one past the
  limit), not just the happy path.
- Assert on observable behaviour. A test that breaks when you rename a private
  method is testing the wrong thing.
- Fixtures go in the narrowest `conftest.py` that serves them; default to
  function scope.

```bash
uv run pytest -m "not integration and not e2e"   # fast loop while working
make check                                       # the commit gate
```
