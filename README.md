# Agentic Starter

A lightweight Engineering System for agent-assisted development. It supplies
repository instructions, deterministic quality gates, Graft navigation, fresh
independent verification, safe dependency management, adoption and migration.
Matt Pocock's upstream skills supply the development workflow.

## Choose your starting point

| Your project | Start here |
| --- | --- |
| New application | Generate a clean directory below |
| Existing project without Engineering | [Adopt it](ENGINEERING.md#existing-project-without-engineering) while preserving its native checks |
| Earlier Agentic Starter | [Upgrade the infrastructure](ENGINEERING.md#earlier-agentic-starter), then reconcile OpenSpec separately if present |
| OpenSpec project | [Prepare semantic migration](ENGINEERING.md#openspec-project) from an external Engineering checkout |
| Engineering maintainer | [Build, verify and release](docs-maintainer/README.md) |

## New application

Install Git, Python 3.12+, uv and Node.js 22.12+ with npm, then:

For a new application, build a clean directory from this Engineering checkout:

```bash
make template DEST=/path/to/new-application
cd /path/to/new-application
git init -b main
make setup
git add .
git commit -m "Initialize application"
make check
```

The destination must not exist and its parent must exist. The generated README
belongs to your application. Maintainer suites, tracker history, installed skills,
migration implementations, migration skills, legacy baselines and populated local
state are excluded; setup installs dependencies from pins. Application changes
need no `make manifest` or fingerprint repair. Use a separate Engineering checkout
for brownfield migration; existing installations retain their migration files.

## Daily development

Choose a branch, then use `/implement → /review → /ship`. Implementation produces
working behavior, a runnable example, scoped local commits and independent
verification. Review presents current evidence, findings and gaps; try the example
and direct any corrections. After completed review, ship accepts the unchanged
presented result and creates the actual PR/MR. Merge remains a separate decision.

Current verification is reused. Missing independent execution produces an explicit
INCOMPLETE fresh-session handoff; a local commit is neither verification nor human
acceptance. If a push fails after committing, restore connectivity and use the
reported retry command without duplicating commits or checks. Follow the
[daily development guide](ENGINEERING.md#daily-development-implement--review--ship)
for examples, corrections, provider setup and recovery.

For large coding work: `/wayfinder` → `/to-spec` → `/to-tickets` → `/implement`.
Local Markdown is the default tracker regardless of hosting provider.

## Work on Engineering itself

In this maintainer checkout, use `make setup` then `./engineering doctor`.
Setup installs required pinned dependencies through the network. Optional
show-me and Karpathy skills are explicit choices. See the
[maintainer guide](docs-maintainer/README.md) for distribution checks and releases.

Read [ENGINEERING.md](ENGINEERING.md) for onboarding, skill selection, navigation,
verification, system/dependency updates, adoption and legacy migration.
[REVIEW.md](REVIEW.md) defines human review; [CLAUDE.md](CLAUDE.md) holds shared
agent policy and [AGENTS.md](AGENTS.md) points other runtimes to it.
