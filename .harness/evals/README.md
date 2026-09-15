# Harness evals

This repo **is** agent configuration. `CLAUDE.md`, `REVIEW.md`, the skills, and
the hooks steer every downstream project. `.harness/tests/` exercises executable
tooling; these evals guard the instructions that shape agent behavior.

Two kinds of case, deliberately:

- **`static`** — assertions about the repo itself: a skill's frontmatter parses,
  a deleted command stays deleted, an invariant is stated in `CLAUDE.md`. Fast,
  free, deterministic. Runs in CI on every push.
- **`prompt`** — runs `claude -p` and asserts on the response. Catches what
  static checks can't: whether the instructions actually *steer* the model. Costs
  tokens and needs auth, so it's opt-in via `make evals-full`.

Adding a case beats arguing about wording. When a session does the wrong thing
and you fix the prose, add the case that would have caught it.

**Review cadence.** Read through the suite whenever you bump `TEMPLATE_VERSION`.
Delete any case whose `why` no longer describes a failure that could actually
happen — a case guarding a deleted command is pure runtime. A case that has
never failed is not automatically healthy: confirm it still fails when you break
the thing it guards, or it is asserting nothing.

```bash
make evals        # static only — CI default
make evals-full   # + prompt cases (needs `claude` on PATH)
```

## Case format

One YAML-ish block per file in `cases/`. Fields:

| Field | Meaning |
|---|---|
| `id` | Unique slug, used in output |
| `kind` | `static` or `prompt` |
| `why` | The failure this guards against — required, so a stale case can be judged |
| `shell` | (static) Command; exit 0 = pass |
| `prompt` | (prompt) Sent to `claude -p` |
| `expect` | (prompt) Substrings that must ALL appear, case-insensitive, one per line |
| `reject` | (prompt) Substrings that must NOT appear |

Doctor and the runner use the same stdlib parser in `factory/eval_config.py`.
Inline fields and `|`/`>` blocks follow the runner's existing YAML-ish subset;
this is not a general YAML loader. Required fields must contain non-whitespace
content, kinds must be `static` or `prompt`, and duplicate field names are
rejected. Doctor parses cases without importing the inspected runner or executing
their bodies.

Routing prompt cases cover FAST cosmetic maintenance, STANDARD product behavior,
and DEEP architectural migration. Static cases cover the artifact split, lazy
context loading, independent verification, final shipping gate, skill policy,
and packaging. Record representative workflow costs with
[workflow-runs.md](workflow-runs.md); routing evals alone do not measure full runs.

The safe-owned-lifecycle static case checks manifest/state agreement, installed
ownership, shared adapters and the update decision contract without credentials.
Filesystem round trips, malformed inputs, clean-Git preflight and injected recovery
failures live in the harness integration tests. A static PASS is not evidence that
prompt behavior, remote CI or external dependency provisioning was exercised.
