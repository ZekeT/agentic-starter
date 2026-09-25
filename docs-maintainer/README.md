# Engineering maintainers

This directory belongs to the Engineering source repository. It is excluded from
consumer generation; generated applications use their own README and operational
`ENGINEERING.md`. Consumer projects do not run maintainer release or eval tools.

## Build and verify

Run `make setup` in this checkout to install required pinned tools. The positive
inclusion list `.engineering/template/files.json` selects consumer files, including
separate README, Makefile and configuration inputs. Tracking a file in Git does
not add it to the payload. Keep runtime policy in shared files and development
history here. Migration code stays in the source checkout for external use.

After changing managed source, run `make fmt` and `make manifest` here to refresh
distribution fingerprints. Never use manifest regeneration to repair a customized
consumer installation. Follow independent review policy and run `make check`,
`make engineering-test` and `make engineering-evals` before distributing changes.
Optional authenticated model evals require an explicit choice.

Build with `make template DEST=/absolute/new-directory`; the parent must exist and
the destination must not exist. Build twice to compare bytes and executable modes
when changing packaging. Initialize the output with Git, run setup and ordinary
gates, then make an application change without regenerating a manifest. Never
copy populated install state, dependency caches, tracker artifacts or historical
documents into the payload. Remote template branch/repository publication remains
deferred; the supported release artifact is a generated directory. Pushes, PRs
and merges remain separate authorized actions.

## Onboarding verification

[Onboarding evidence](onboarding-evidence.md) records the four onboarding routes,
commands, observations, fixture boundaries and remaining human decisions.
`.engineering/tests/integration/test_onboarding.py` exercises adoption and legacy
upgrade through public commands, while `test_template.py` covers generation,
setup and consumer ownership. Migration tests cover preview, refusal, rollback,
retry and closure. The six scenarios in
[the semantic fixtures](../.engineering/tests/fixtures/openspec-brownfield/README.md)
are authored acceptance/refusal examples, not proof of model judgment.

## Retained history

[Historical migration material](history/README.md) preserves this starter's old
migration reports and source review packages. It is evidence of earlier work,
not current onboarding instructions or an approval to act on remaining tasks.
Use [ENGINEERING.md](../ENGINEERING.md) for current operations. The existing v2
recognition baseline remains in `.engineering/migrations/baselines/` because
migration runtime uses it; it is not a historical document to relocate.
