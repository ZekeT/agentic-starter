# Commits and PRs

The conventions `/commit-push-pr` follows. Both exist so that six months from
now, `git log` and the PR list answer "why is this like this?" without anyone
having to remember.

---

## Commits — Conventional Commits

```
type(scope): description

body — why, not what

footer
```

**Subject.** Imperative mood ("add", not "added" or "adds"), lower case after the
colon, no trailing period, ≤ 72 characters. It completes the sentence *"if
applied, this commit will…"*.

| Type | Use for |
|---|---|
| `feat` | new user-visible behaviour |
| `fix` | a bug fix |
| `docs` | documentation only |
| `test` | adding or fixing tests, no production change |
| `refactor` | behaviour identical, structure different |
| `perf` | a change made for performance |
| `chore` | tooling, deps, config, housekeeping |
| `ci` | CI configuration |

Scope is the area touched — a package, a capability, a change slug:
`feat(billing):`, `chore(harness):`, `fix(auth):`.

**Body.** Optional for an obvious one-liner, expected otherwise. The diff already
shows *what* changed; the body's job is *why* — the constraint, the alternative
rejected, the bug's actual cause. A body restating the diff is wasted.

Write it for whoever runs `git blame` on this line in a year, having no idea what
you were dealing with today.

**Footer.** `BREAKING CHANGE: <what and the migration path>` when applicable, plus
any issue reference.

```
fix(dev-change): guard awk group selection against END re-running

awk runs the END block even after `exit`, so both the main rule and END
printed a group number. The shell captured "2\n2", which silently broke
every downstream check that compared GROUP to a single value.

Guarded with a `found` flag rather than restructuring, to keep the
selection logic readable.
```

**One commit, one idea.** A commit doing two things cannot be reverted for one of
them. If the body needs the word "also", it is probably two commits.

## Pull requests

The body is `.github/pull_request_template.md`, which GitHub loads automatically.
Fill every section; delete one only with a one-line reason.

**Title.** Same format as a commit subject. It becomes the squash-merge commit,
so it is what `git log` shows on `main` forever.

**Scope.** One task group per PR. `/dev-change <slug> <group>` enforces this by
giving each group its own branch. A PR spanning groups is a review-fatigue
problem and a merge-conflict problem at once.

**The test evidence is the point.** `REVIEW.md` Pass 4 checks whether new
behaviour has a test; the template's "How this was tested" is where the author
answers it in advance. "Tested locally" is not an answer — name the tests, or
record the manual steps and what was observed.

**"Not covered" is the most valuable line.** It tells the reviewer where to spend
attention. A PR claiming everything is covered gets a shallower review than one
that admits a gap.

## What not to do

- Don't commit with `--no-verify`, and don't bypass `make check`. The hooks and
  the gate are the deal.
- Don't force-push a branch under review — the reviewer loses their place.
- Don't mix a refactor into a behaviour change. The behaviour change becomes
  invisible inside the noise, which is exactly when bugs get merged.
- Don't open a PR whose description is only its title.
