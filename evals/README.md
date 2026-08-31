# Harness evals

This repo **is** agent configuration. `CLAUDE.md`, `REVIEW.md`, the skills, and
the hooks steer every downstream project, and `tests/` only covers the two Python
scripts. Everything that actually shapes agent behaviour is unversioned prose
with no regression test. That is what these cover.

Two kinds of case, deliberately:

- **`static`** — assertions about the repo itself: a skill's frontmatter parses,
  a deleted command stays deleted, an invariant is stated in `CLAUDE.md`. Fast,
  free, deterministic. Runs in CI on every push.
- **`prompt`** — runs `claude -p` and asserts on the response. Catches what
  static checks can't: whether the instructions actually *steer* the model. Costs
  tokens and needs auth, so it's opt-in via `make evals-full`.

Adding a case beats arguing about wording. When a session does the wrong thing
and you fix the prose, add the case that would have caught it.

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
