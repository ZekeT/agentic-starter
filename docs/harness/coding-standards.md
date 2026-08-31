# Coding Standards

> The full reference behind the `python-standards` skill. The skill is the
> agent-facing summary; this document carries the reasoning, and only the
> reasoning a tool cannot supply.
>
> **What is not here.** Anything `make check` decides: formatting and line
> length (black), import order (isort), annotation coverage and strictness
> (mypy `strict`), docstring coverage (interrogate `fail-under = 80`). Those
> live in `pyproject.toml`, which is the only place they should be stated —
> a doc that repeats a tool setting is a doc that will contradict it.
> Test layout and conventions: `docs/harness/testing.md`.
>
> Sources: Google Python Style Guide, PEP 8, PEP 257.

---

## Functions and simplicity

**Functions do one thing.** A function has a single, clearly nameable
responsibility. Writing "and" in the name is the signal to split it.

```python
def validate_and_save_user(data: dict) -> User: ...   # bad: two things
def validate_user_data(data: dict) -> UserCreate: ...  # good
def save_user(user: UserCreate) -> User: ...           # good
```

**Aim for under 20 lines, as a heuristic and not a rule.** A 25-line function
with a clear purpose beats two 12-line functions with confusing names. The real
test is naming: if you cannot name it without "and", it is doing too much.

**Prefer early returns over deep nesting.** Three nested `if`s that all have to
be true is one guard clause per condition, each raising the error that names
what actually went wrong. The happy path goes last, unindented.

```python
def process_order(order: Order) -> Receipt:
    if not order.is_valid():
        raise InvalidOrderError(order.id)
    if not order.has_stock():
        raise OutOfStockError(order.id)
    return charge_and_fulfil(order)
```

---

## DRY

Write the same logic twice, extract it; three places means it needs a module.
The cost of duplication is not the extra lines — it is every future bug fix that
must be applied in N places, and the N−1 places you will forget.

---

## Classes only for state

**Use classes to manage state. Use functions for procedural logic.** Before
writing a class, ask whether it needs to hold mutable state across method calls.
If not, write functions.

A class whose methods never touch `self` is a namespace with extra steps —
`UserValidator.validate_email(...)` should be `validate_email(...)`.

A "god class" — too many responsibilities, methods, and dependencies — is the
class-shaped version of a function that does too much. Split by responsibility.

---

## Naming

The conventions table lives in the `python-standards` skill, which is what an
agent actually loads. Two rules worth the reasoning:

- **No single-letter names** outside conventional loop counters (`i`, `j`) and
  maths (`x`, `y`). A name is the cheapest documentation in the file.
- **Functions are verbs, values are nouns.** `fetch_user()` is a function;
  `user` is what it returns. A noun-named function reads as a value at every
  call site, and the mismatch costs a reader a lookup every time.

---

## Type hints

mypy `strict` already requires annotations on every definition. What it does not
decide:

- `from __future__ import annotations` at the top of every module — forward
  references without quoting, and no import cycles for typing-only needs.
- Prefer built-in generics: `list[str]`, not `List[str]`.
- `X | None`, not `Optional[X]`.
- `Any` only where unavoidable, always with a comment saying why. `Any` is not a
  type; it is a hole in the type system, and the comment is what stops the hole
  spreading.
- Type-only imports go inside `if TYPE_CHECKING:` so they cost nothing at
  runtime.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mymodule import HeavyClass

def process(obj: HeavyClass) -> None: ...
```

---

## Docstrings

Google style; the skill carries the worked example. interrogate enforces the
*coverage* percentage and nothing about the content — so what matters here is
what a docstring is for: **why and what, never how.** The code shows how, and a
docstring restating it is a second thing to keep true.

Document `Raises:` whenever a caller must handle the exception. That is the part
a reader cannot get from the signature.

Exempt from coverage (interrogate config): `__init__`, dunder methods, and
`tests/`.

---

## Imports

isort owns the grouping and order. It does not catch:

- **Never `from module import *`.** It hides the origin of every name and
  defeats static analysis.
- Standard aliases only: `import numpy as np`, `import pandas as pd`. An
  invented alias makes a familiar library unsearchable.
- No relative imports beyond one level. `from . import utils` is fine;
  `from ....utils import x` means the package layout is wrong.

---

## Exception handling

**Never use a bare `except:`.** It catches `SystemExit` and `KeyboardInterrupt`,
which makes the program impossible to kill and hides the errors you needed to
see. `except Exception: pass` is the same bug with better manners.

```python
try:
    result = fetch(url)
except httpx.TimeoutException as e:
    logger.warning("Request timed out after %ds: %s", TIMEOUT, e)
    raise RetryableError("fetch timed out") from e
```

- Catch the most specific type available.
- Always log or re-raise. Never silently swallow.
- Keep the `try` block to the statement that can actually fail — a wide `try`
  catches the exception you did not mean to handle.
- `raise X from e` preserves the original traceback. Without `from`, the cause
  is lost and the report starts at the wrapper.

---

## Data validation

Validate external data — API payloads, config files, environment variables, CLI
args — with `pydantic` (preferred) or `marshmallow`.

```python
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("age must be non-negative")
        return v
```

**Validate at the boundary, then pass typed objects inward.** The service and
data layers should never see a raw dict. Validation scattered through the inner
layers means no layer can state what it can rely on.

---

## Immutability

Prefer immutable types where data should not change — `tuple` over `list`,
`frozenset` over `set` — for anything fixed:
`ALLOWED_ROLES: tuple[str, ...] = ("admin", "editor", "viewer")`.

The point is not performance. A mutable module-level constant is a shared
mutable global, and the bug it produces appears far from the line that caused it.

---

## Resources

Always use a context manager — files, database connections, locks, temp
directories, HTTP sessions. A manual `.close()` does not run when an exception
is raised above it, which is exactly when you need the resource released.

---

## Separation of concerns

```
HTTP request → API layer (validate, route)
                  ↓
           Service layer (business logic)
                  ↓
           Data layer (DB, external APIs)
```

- No database queries in API handlers.
- No business logic in data models.
- No HTTP concerns in service functions: a service takes typed objects and
  returns typed objects, and knows nothing about the transport that called it.
  That is what makes it testable without a server.

---

## Small things with reasons

- f-strings for interpolation, not `%` or `.format()`.
- Long strings use implicit concatenation inside parentheses, never a `\`
  continuation — a trailing backslash breaks silently on trailing whitespace.
- `subprocess.run([...], check=True)`, never `os.system()`: `os.system` ignores
  the exit status, cannot capture output, and passes the string to a shell.
- `pathlib.Path("dir") / "file.txt"`, not `os.path.join` — chainable, and
  correct on Windows without thinking about it.
- Prefer a generator to a list comprehension when you iterate once:
  `sum(x**2 for x in range(100))` builds nothing.

---

## Other languages

This template's toolchain is Python-only. A project adding another language
adopts that language's standard formatter and linter in the same spirit — one
config, wired into `make check`, and no doc restating what the config decides:
`gts` for TypeScript (`npx gts init`, wraps ESLint + Prettier), `eslint` with
`eslint-config-google` for JavaScript, Prettier for HTML and CSS.

Two rules no formatter decides: keep `strictNullChecks` on, and never write
`any` or `// @ts-ignore` without a comment saying why; and keep behaviour out of
markup — no inline styles, no inline event handlers.
