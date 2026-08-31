# Review Policy

What every review of this repo checks, in what order. `/review` and the
`security-reviewer` agent both follow this file — they hold the *procedure*, this
holds the *policy*, so tuning review behaviour means editing one file rather than
three.

Tune it monthly. If a class of bug keeps reaching `main`, add a pass. If a pass
never finds anything in three months, delete it.

---

## Skip entirely

Reviewing these wastes attention that the passes below need:

- Anything `make check` already enforces — formatting, import order, docstring
  coverage, `mypy --strict`, test failures. If it passed the gate, don't relitigate it.
- Anything a hook already blocks — secrets in writes, `.env` reads, dangerous bash.
- Generated files: `template-manifest.json`, `uv.lock`, `.claude/commands/opsx/`,
  `.claude/skills/openspec-*/`, `openspec/specs/` (only ever written by
  `/archive-change`).

## Pass 1 — Correctness

Bugs, in rough order of how often they actually bite:

- Off-by-one, boundary, and empty-collection handling
- Unhandled error paths; bare `except:`; swallowed exceptions
- Concurrency: two sessions, two worktrees, or two processes hitting the same file
- Shell portability in commands and hooks — **BSD vs GNU** `sed`/`awk` differ, and
  this harness runs on both. `sed -E`, not `\+`. (This has already caused one bug.)
- Resource cleanup on the failure path, not just the happy one

## Pass 2 — Security

Full detail is the `security-reviewer` agent's remit; dispatch it for anything
touching auth, input handling, subprocess, or deserialization. At minimum:

- External data validated at the boundary (pydantic/marshmallow), never trusted inward
- No credential, token, or key material in code, logs, or error messages
- Subprocess calls never interpolate unsanitised input
- Dependency versions with known CVEs

## Pass 3 — Compliance against spec and plan

**This is the pass this harness exists to enable**, and the one no generic
reviewer can run. It is only possible because the delta specs and `tasks.md` are
committed artifacts.

- Does the diff satisfy every `#### Scenario:` in the change's delta specs?
- Does it do anything the specs *don't* describe? Unspecced behaviour is either
  scope creep or a missing requirement — say which.
- Does it match the claimed task group, and only that group? Work bleeding across
  groups is what makes the one-group-per-PR split stop working.
- If implementation departed from `tasks.md`, was `tasks.md` updated in the same
  commit?
- Did anything edit `openspec/specs/` directly? That is always wrong outside
  `/archive-change`.

## Pass 4 — Tests

- New behaviour has a test that fails without the change
- Tests assert on observable behaviour, not implementation detail
- The failure path is tested, not just the happy path

---

## Important vs nit

**Important** — block the merge:

- Any Pass 1 or Pass 2 finding
- A delta-spec scenario the diff does not satisfy
- Behaviour with no test
- `openspec/specs/` edited outside `/archive-change`

**Nit** — mention at most **three**, prefixed `nit:`, and never block on them:

- Naming, comment wording, formatting `make check` allows
- Structural preferences with no behavioural difference

The cap is deliberate. A review with twenty nits and one real bug gets the bug
skimmed past.

---

## Verdict

End every review with exactly one:

- **APPROVE** — no Important findings
- **APPROVE WITH COMMENTS** — no Important findings, nits worth fixing
- **REQUEST CHANGES** — at least one Important finding, each with file:line and a
  concrete failure scenario

Never report a finding you have not traced to a specific line. "This might have a
race condition" is not a finding; "two `/dev-change` sessions on groups 1 and 2
both write `tasks.md` at line 40" is.
