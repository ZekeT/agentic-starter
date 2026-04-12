# Coding Standards

> Referenced by `CLAUDE.md`. This is the full reference for all agents and developers.
> Sources: Google Style Guide, PEP 8, PEP 257, project conventions.
> CLAUDE.md carries the agent-facing summary; this document carries the reasoning.

---

## Python (primary language)

### Functions & Simplicity

**Rule: Functions do one thing.**

A function should have a single, clearly nameable responsibility. If you find yourself
writing "and" in the function name, it's a signal to split it.

```python
# Bad — does two things
def validate_and_save_user(data: dict) -> User:
    ...

# Good — two responsibilities, two functions
def validate_user_data(data: dict) -> UserCreate:
    ...

def save_user(user: UserCreate) -> User:
    ...
```

**Heuristic: aim for < 20 lines.**

This isn't a hard rule — a 25-line function with a clear purpose is better than
two 12-line functions with confusing names. The real test: if you struggle to name
it without "and", it's doing too much.

**Prefer early returns over deep nesting.**

Deep nesting is a sign of complex conditional logic. Return or raise early for
guard clauses; put the happy path last and unindented.

```python
# Bad — nested
def process_order(order: Order) -> Receipt:
    if order.is_valid():
        if order.has_stock():
            if order.payment_confirmed():
                return charge_and_fulfil(order)

# Good — early returns
def process_order(order: Order) -> Receipt:
    if not order.is_valid():
        raise InvalidOrderError(order.id)
    if not order.has_stock():
        raise OutOfStockError(order.id)
    if not order.payment_confirmed():
        raise PaymentNotConfirmedError(order.id)
    return charge_and_fulfil(order)
```

---

### DRY (Don't Repeat Yourself)

If you write the same logic twice, extract it. Three places means it definitely
needs a module.

The cost of duplication isn't just the code — it's every future bug fix that
has to be applied in N places, and the N-1 places you'll forget.

---

### KISS — Minimize Classes

**Use classes only for managing state. Use functions for procedural logic.**

Most Python code does not need classes. Before writing a class, ask:
does this need to hold mutable state across multiple method calls?
If no — use functions.

```python
# Bad — a class as a namespace for functions
class UserValidator:
    def validate_email(self, email: str) -> bool: ...
    def validate_age(self, age: int) -> bool: ...

# Good — just functions
def validate_email(email: str) -> bool: ...
def validate_age(age: int) -> bool: ...
```

**Avoid "God classes"** — classes with too many responsibilities, too many
methods, too many dependencies. They're the class equivalent of a function
that does too much. Split by responsibility.

---

### Naming

| Thing | Convention | Example |
|-------|-----------|---------|
| Variables | `snake_case` | `user_count`, `is_valid` |
| Functions | `snake_case`, verb-first | `fetch_user()`, `validate_token()` |
| Classes | `PascalCase` | `UserService`, `PaymentProcessor` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | leading `_` | `_internal_cache` |
| Booleans | `is_`, `has_`, `can_` | `is_active`, `has_permission` |

**No single-letter names** except conventional loop counters (`i`, `j`) and
math (`x`, `y`). Even then, prefer descriptive names in production code.

**Source:** Google Python Style Guide §3.16, PEP 8 §Naming Conventions

---

### Type Hints

All public function signatures require type hints. This is enforced by `mypy`.

```python
# Bad
def fetch_user(user_id):
    ...

# Good
def fetch_user(user_id: int) -> User:
    ...
```

**Rules:**
- `from __future__ import annotations` for forward references (avoids circular imports).
- Prefer specific types: `list[str]` not `List[str]` (Python 3.9+).
- Use `X | None` over `Optional[X]` (Python 3.10+).
- Use `Any` only when necessary — always add a comment explaining why.
- Type-only imports go inside `if TYPE_CHECKING:` to avoid runtime overhead.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mymodule import HeavyClass

def process(obj: HeavyClass) -> None:
    ...
```

**Source:** Google Python Style Guide §2.21, PEP 484

---

### Docstrings (Google style)

Use Google-style docstrings. `interrogate` enforces ≥ 80% coverage on public APIs.

```python
def fetch_rows(
    table: str,
    keys: list[str],
    require_all: bool = False,
) -> dict[str, tuple[str, ...]]:
    """Fetch rows from the database by key.

    Args:
        table: The name of the table to query.
        keys: A list of row keys to fetch.
        require_all: If True, raise if any key is missing.

    Returns:
        A dict mapping keys to row data tuples.

    Raises:
        KeyError: If require_all is True and a key is not found.
    """
```

**Short functions** can use a one-liner: `"""Return the user's full name."""`

**Exempt from interrogate:** `__init__`, `__dunder__`, private methods (`_name`),
test functions (interrogate config excludes `tests/`).

**Source:** Google Python Style Guide §3.8, PEP 257

---

### Imports

Grouped in this order (isort enforces this automatically):

```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third-party
import httpx
from pydantic import BaseModel

# 3. Local
from myproject.models import User
from myproject.utils import format_name
```

**Rules:**
- Never `from module import *` — pollutes namespace and breaks static analysis.
- Use standard aliases: `import numpy as np`, `import pandas as pd`.
- No relative imports beyond one level: `from . import utils` is fine,
  `from ....utils import x` is not.
- Conditional imports (heavy deps) go inside `if TYPE_CHECKING:` block.

**Source:** Google Python Style Guide §2.2, PEP 8 §Imports

---

### Exception Handling

**Never use bare `except:`** — it catches `SystemExit` and `KeyboardInterrupt`,
making your program impossible to kill and hiding real errors.

```python
# Bad
try:
    result = fetch(url)
except:
    pass

# Bad — too wide, silently swallows
try:
    result = fetch(url)
except Exception:
    pass

# Good — specific, explicit, logged
try:
    result = fetch(url)
except httpx.TimeoutException as e:
    logger.warning("Request timed out after %ds: %s", TIMEOUT, e)
    raise RetryableError("fetch timed out") from e
except httpx.HTTPStatusError as e:
    logger.error("HTTP %d from %s", e.response.status_code, url)
    raise
```

**Rules:**
- Catch the most specific exception type possible.
- Always log or re-raise — never silently swallow.
- Keep `try` blocks as small as possible (minimum code inside).
- Use `raise X from e` to preserve the original traceback.

**Source:** Google Python Style Guide §2.4, PEP 8 §Programming Recommendations

---

### Data Validation

Use `pydantic` (preferred) or `marshmallow` for any external data:
API payloads, config files, environment variables, CLI args.

```python
from pydantic import BaseModel, EmailStr, field_validator

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

Never trust unvalidated external input. Validate at the boundary (API/CLI layer),
then pass typed objects inward. The service and data layers should never see raw dicts.

---

### Immutability Preference

Prefer immutable types when data shouldn't change — makes intent clear and
prevents accidental mutation bugs.

```python
# Mutable (can be accidentally modified)
ALLOWED_ROLES = ["admin", "editor", "viewer"]

# Immutable (intent is clear)
ALLOWED_ROLES: tuple[str, ...] = ("admin", "editor", "viewer")
```

Use `tuple` over `list`, `frozenset` over `set` for fixed collections.

---

### Resources & Context Managers

Always use context managers for resources. Never rely on manual `.close()`.

```python
# Bad
f = open("data.txt")
content = f.read()
f.close()  # won't run if an exception is raised above

# Good
with open("data.txt") as f:
    content = f.read()
```

Applies to: files, database connections, locks, temp directories, HTTP sessions.

---

### Separation of Concerns

```
HTTP request → API layer (validate, route)
                  ↓
           Service layer (business logic)
                  ↓
           Data layer (DB, external APIs)
```

**Rules:**
- No database queries in API handlers.
- No business logic in data models.
- No HTTP concerns in service functions.
- Services take typed objects, return typed objects. They know nothing about HTTP.

---

### Strings

- **f-strings** for interpolation: `f"Hello, {name}!"` not `"Hello, %s" % name`.
- **Triple `"""`** for all docstrings (never `'''`).
- Long strings: use implicit concatenation inside parentheses, not `\` continuation.

```python
# Good
message = (
    "This is a very long string that "
    "spans multiple lines cleanly."
)
```

---

### Misc

- `subprocess.run(["cmd", "arg"], check=True)` not `os.system("cmd arg")`.
  Reason: `os.system` doesn't capture output, ignores errors, and is a shell injection risk.
- `pathlib.Path("dir") / "file.txt"` not `os.path.join("dir", "file.txt")`.
  Reason: cleaner, cross-platform, chainable.
- `key in dict` not `dict.has_key(key)` — Python 2 pattern, doesn't exist in Python 3.
- `for key in dict:` not `for key in dict.keys():` — redundant, slower.
- Prefer generators over list comprehensions when you only iterate once:
  `sum(x**2 for x in range(100))` not `sum([x**2 for x in range(100)])`.

---

## HTML (when needed)

> Source: Google HTML/CSS Style Guide

**Formatting:**
- 2-space indent.
- Lowercase all element names and attributes.
- Double quotes for attribute values.
- One attribute per line for elements with multiple attributes.

**Elements:**
- Omit `type` attribute on `<script>` and `<style>` — it's the default in HTML5.
- Use semantic elements: `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`.
- Prefer `<button>` over `<div onclick>` for interactive elements.

**Separation:**
- No inline styles. CSS in `.css` files or `<style>` blocks.
- No inline event handlers (`onclick="..."`). JS in `.js` files.

---

## JavaScript (when needed)

> Source: Google JavaScript Style Guide
> Tooling: `eslint-config-google` — `npm install --save-dev eslint eslint-config-google`

**Variables:**
- `const` by default. `let` when reassignment is needed. Never `var`.
- Destructuring: `const { name, age } = user` over `const name = user.name`.

**Functions:**
- Arrow functions for callbacks and short expressions: `items.map(x => x.id)`.
- Named function declarations for top-level functions (better stack traces).
- No `arguments` object — use rest params: `function fn(...args)`.

**Equality:**
- Always `===` and `!==`. Never `==` or `!=`.

**Style:**
- 2-space indent.
- Semicolons required.
- Single quotes for strings (except JSON).
- Template literals over string concatenation: `` `Hello, ${name}!` ``.

**Prohibited:**
- No `eval()` — security risk.
- No modifying built-in prototypes.
- No `with` statements.

**Documentation:**
- JSDoc on all public functions:
```javascript
/**
 * Fetches a user by ID.
 * @param {number} userId - The user's unique identifier.
 * @returns {Promise<User>} The user object.
 */
async function fetchUser(userId) { ... }
```

---

## TypeScript (when needed)

> Source: Google TypeScript Style Guide
> Tooling: `gts` — `npx gts init` (zero-config, wraps ESLint + Prettier)

**Types:**
- Explicit return types on all public functions.
- No `any` without a comment explaining why it's unavoidable.
- `interface` for object shapes that can be extended/implemented.
- `type` for unions, intersections, primitives: `type Status = "active" | "inactive"`.
- `import type` for type-only imports (avoids runtime load).

```typescript
// Bad
function process(data: any): any { ... }

// Good
function process(data: UserPayload): ProcessedUser { ... }
```

**Naming:**
- `camelCase` for variables and functions.
- `PascalCase` for classes, interfaces, types, enums.
- `UPPER_SNAKE_CASE` for constants.
- `I`-prefix on interfaces is discouraged (Google style): `User` not `IUser`.

**Classes:**
- Same KISS principle as Python — only use classes for stateful objects.
- Getters/setters are fine but must be pure (no side effects in getters).
- Avoid `namespace` — use ES modules instead.

**Null handling:**
- Enable `strictNullChecks`. Always.
- Prefer `undefined` over `null` for optional values.
- Use optional chaining `?.` and nullish coalescing `??`.

**Prohibited:**
- No `// @ts-ignore` without explanation.
- No non-null assertion `!` without explanation.
- No `Object` (capital O) type — use `object` or a specific interface.
