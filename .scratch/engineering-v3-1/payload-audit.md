# Consumer payload audit

Audit of every tracked path before v3.1 implementation. This is design evidence,
not a second packaging manifest. The final positive inclusion manifest is the
packaging authority. File contents of secrets were not read.

| Source path | Disposition | Reason |
|---|---|---|
| `.claude/agents/maintainability-reviewer.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/agents/security-reviewer.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/agents/verifier.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/commands/review.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/commands/ship.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/hooks/post_tool_lint.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/hooks/post_tool_secrets.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/hooks/pre_tool_dangerous.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/hooks/pre_tool_env_guard.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/output-styles/asd-ste100.md` | Upstream only | Optional maintainer writing preference; not wired by runtime settings. |
| `.claude/settings.json` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.claude/statusline.sh` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/TEMPLATE_VERSION` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/bin/graft` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/config.toml` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/dependencies.toml` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/docs/coding-standards.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/docs/commits-and-prs.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/docs/maintainability.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/docs/testing.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/__init__.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/adoption.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/apply.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/cli.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/config.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/deps.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/doctor.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/doctor_wiring.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/eval_config.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/engineering/graft.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/growth.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/inspection.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/installation.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/migrate/__init__.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/migrate/common.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/migrate/legacy.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/migrate/openspec.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/migrate/wiring.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/ownership.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/registry.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/settings.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/skill_install.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/source.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/transaction.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/engineering/updates.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/evals/README.md` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/001-policy.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/002-verification.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/003-boundaries.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/004-health.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/005-plan.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/101-small-change.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/102-wayfinder.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/cases/103-ship.yaml` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/evals/run_evals.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/graft/package-lock.json` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/graft/package.json` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/manifest.json` | Generate | Fingerprint the actual consumer distribution; do not copy a source-checkout manifest. |
| `.engineering/migrations/baselines/v2-manifest.json` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/migrations/openspec-migration-report.md` | Exclude | Repository-specific generated installation or migration state. |
| `.engineering/scripts/check_feature_docs.py` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/scripts/cmd_check.sh` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/scripts/generate_template_manifest.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/scripts/lib/change.sh` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/scripts/lib/run_quiet.sh` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/setup.sh` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.engineering/state/install.json` | Exclude | Repository-specific generated installation or migration state. |
| `.engineering/state/migrations/openspec.json` | Exclude | Repository-specific generated installation or migration state. |
| `.engineering/tests/__init__.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/fixtures/legacy-v2.json` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/integration/__init__.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/integration/test_checks.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/integration/test_graft.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/integration/test_growth.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/integration/test_ownership.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/test_dependencies.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/test_doctor.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/test_installation.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/test_legacy.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/test_migration.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.engineering/tests/unit/__init__.py` | Upstream only | Starter development, history, test/eval or release content. |
| `.env.template` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.github/pull_request_template.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `.github/workflows/evals.yml` | Upstream only | Starter development, history, test/eval or release content. |
| `.gitignore` | Consumer adaptation | Keep operational instructions/targets; remove maintainer coupling and expose project placeholders. |
| `AGENTS.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `CLAUDE.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `ENGINEERING.md` | Consumer adaptation | Keep operational instructions/targets; remove maintainer coupling and expose project placeholders. |
| `Makefile` | Consumer adaptation | Keep operational instructions/targets; remove maintainer coupling and expose project placeholders. |
| `README.md` | Consumer adaptation | Keep operational instructions/targets; remove maintainer coupling and expose project placeholders. |
| `REVIEW.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `docs/adr/index.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `docs/agents/domain.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `docs/agents/issue-tracker.md` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `docs/architecture.md` | Upstream only | Starter development, history, test/eval or release content. |
| `docs/context/legacy-openspec-candidates.md` | Upstream only | Starter development, history, test/eval or release content. |
| `docs/context/product.md` | Upstream only | Starter development, history, test/eval or release content. |
| `docs/decisions/.gitkeep` | Upstream only | Starter development, history, test/eval or release content. |
| `docs/migrations/engineering-v3.md` | Upstream only | Starter development, history, test/eval or release content. |
| `docs/migrations/openspec/factory-phase2.md` | Upstream only | Starter development, history, test/eval or release content. |
| `docs/migrations/openspec/software-factory.md` | Upstream only | Starter development, history, test/eval or release content. |
| `engineering` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `idea.md` | Upstream only | Starter development, history, test/eval or release content. |
| `pyproject.toml` | Consumer adaptation | Keep operational instructions/targets; remove maintainer coupling and expose project placeholders. |
| `tests/.gitkeep` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |
| `uv.lock` | Include | Operational runtime, portable policy, pinned dependency configuration or minimal project seed. |

## Dependency findings

- Setup currently installs dependencies but does not initialize missing ownership state.
- Doctor requires installation state and all managed manifest paths.
- The shared engineering-check recipe invokes upstream evals; consumer recipes must be decoupled before those files are omitted.
- The current manifest generator selects upstream evals and writes installation state. Consumer manifest generation must omit state and match the selected payload.
- Migration runtime and the legacy ownership baseline are operational command support, distinct from legacy fixture repositories and project-specific archives.
- The project-owned migration skill requires a narrow Git ignore exception; managed upstream skills remain ignored and pin-installed.
- Consumer fmt must tolerate absent application source and must not reference omitted starter tests.
- The consumer README is a dedicated project seed; source product documentation remains upstream.
- Runtime shell helper `change.sh` still contains unused OpenSpec listing and legacy branch-shape functions. Repository search found no callers. Remove these during payload cleanup while retaining base-branch resolution required by reviewers.
