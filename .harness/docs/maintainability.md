# Maintainability contract

Prefer cohesive modules with explicit public surfaces and stable dependency
direction. Before adding substantial code, inspect the natural owning module,
search existing abstractions, and consider whether the responsibility belongs
in its own module. Avoid central-file accumulation, generic utils, duplicate
domain logic, circular dependencies, deeply nested control flow, and functions
with unrelated responsibilities. Prefer local/simple abstractions over global
frameworks; do not create speculative interfaces or meaningless tiny files.

Run `uv run --no-project --isolated --python 3.12 python factory maintainability` (or `./factory maintainability` with
Python 3.12+ on PATH). The normal full gate includes this check. `--base BRANCH`
uses that branch's merge base; otherwise existing harness base resolution applies.
The gate selects an isolated Python 3.12 runtime, preserving downstream project
metadata and virtual environments, including projects using Python 3.11. uv may
install that tooling interpreter on first use.
Missing history fails visibly; `--all` explicitly requests size-only warnings.
`--verbose` includes counts and status for passing changed files. The full gate
uses its standard quiet wrapper; `VERBOSE=1 make check` also shows successful
growth details and warnings. Failures always retain complete output.

Defaults are warning above **300 code lines**, maximum **500**, and substantial
growth of **150 net added code lines**. New files above the maximum fail.
Existing oversized files fail only with substantial growth; smaller growth warns.
These are maintainability signals, not correctness proofs.

Set overrides under `project.maintainability` in
`.harness/template-manifest.json`, for example:

```json
{"enabled": true, "warn_file_lines": 300, "max_file_lines": 500,
 "substantial_growth_lines": 150,
 "exceptions": [{"path": "src/schema.py", "reason": "Generated schema"}]}
```

Exceptions require unique exact existing paths and nonempty reviewed reasons;
wildcards and symlinks are rejected. Do not grant yourself an exception solely to
pass a check. Explicit disabling is reported. Manifest regeneration preserves
project overrides. Blank lines, comment-only lines and Python docstrings do not
count; ordinary multiline string data and executable code on docstring lines do.

Python is the v1 supported language. Other detected source languages are reported
as unanalyzed. Git-tracked and non-ignored untracked Python files include hidden
harness tooling. Deleted files, virtual environments, caches, node_modules,
vendor/vendored directories and generated Graft cache data are excluded. Generated
Python, fixtures, migrations and schemas can use reasoned path exceptions; there
is no blanket exemption based on an easy-to-add inline magic comment.

New DEEP program designs describe Code Shape before implementation. STANDARD may
abbreviate that section. Keep accepted historical designs unchanged.
