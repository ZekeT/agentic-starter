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

Full reference with rationale and examples: `docs/coding-standards.md`.
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
