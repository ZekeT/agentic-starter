# Your application

Describe the application, its users and how to run it here.

## Start development

Prerequisites: Git, Python 3.12+, uv, Node.js 22.12+ and npm/npx.
From this generated directory:

```bash
git init -b main
make setup
git add .
git commit -m "Initialize application"
make check
```

Setup initializes missing Engineering installation state and explicitly installs
pinned development dependencies. It preserves existing installation baselines.
No global agent settings are changed. Repeating setup is supported.

Add application code in `src/` and tests in `tests/`. Set
`[navigation].application_roots` in `.engineering/config.toml` when code exists,
then explicitly run `.engineering/bin/graft build` before verification. Add
feature instructions as described in `docs/agents/domain.md`.

Run `make fmt` while developing, then `make check` for the ordinary gate.
`./engineering doctor` diagnoses installation health offline. Local Markdown
specs and tickets under `.scratch/` remain trackable in Git.

Read [CLAUDE.md](CLAUDE.md) for agent policy, [ENGINEERING.md](ENGINEERING.md)
for setup and workflows, and [REVIEW.md](REVIEW.md) for human review.
Starter release scripts, self-tests and evals belong in a separate Engineering
maintainer checkout; this application does not need them for normal checks.

Application development never requires `make manifest` or fingerprint repair.
Engineering owns its managed scopes; application code, tests, README, package
metadata and the application portions of shared files remain yours.

Fresh applications omit migration implementations, migration skills and legacy
baselines. For a brownfield project, use a separate Engineering checkout:

```bash
/path/to/engineering-checkout/engineering migrate openspec-project --target /path/to/project --plan
```

See the migration guidance in [ENGINEERING.md](ENGINEERING.md) before applying.

For an existing application, follow [adoption](ENGINEERING.md#existing-project-without-engineering)
from a separate Engineering source checkout. Do not overlay this generated
project onto it. Earlier starters use [the legacy upgrade](ENGINEERING.md#earlier-agentic-starter)
before any OpenSpec reconciliation. Each target keeps its own language, package
manager and native checks.
