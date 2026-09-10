# Software factory implementation report

Completed on 2026-09-09 on `feat/software-factory-g1`. This is a final review
record, not a workflow-status database. The task checklist remains `tasks.md`.
The user-authored `instruct.md` was read and remains unchanged.

## 1. Files added (22)

- `.claude/skills/shape-change/SKILL.md`
- `.harness/evals/cases/012-factory-routing.yaml`
- `.harness/evals/cases/013-independent-gates.yaml`
- `.harness/evals/cases/014-progressive-skills.yaml`
- `.harness/evals/cases/103-route-fast.yaml`
- `.harness/evals/cases/104-route-standard.yaml`
- `.harness/evals/cases/105-route-deep.yaml`
- `.harness/evals/workflow-runs.md`
- `.harness/scripts/check_feature_docs.py`
- `.harness/scripts/cmd_check.sh`
- `.harness/scripts/lib/run_quiet.sh`
- `.harness/tests/integration/test_factory_checks.py`
- `FACTORY.md`
- `openspec/changes/software-factory/.openspec.yaml`
- `openspec/changes/software-factory/design.md`
- `openspec/changes/software-factory/implementation-report.md`
- `openspec/changes/software-factory/intent.md`
- `openspec/changes/software-factory/program-design.md`
- `openspec/changes/software-factory/proposal.md`
- `openspec/changes/software-factory/specs/factory-verification/spec.md`
- `openspec/changes/software-factory/specs/factory-workflow/spec.md`
- `openspec/changes/software-factory/tasks.md`

## 2. Files modified (37)

- `.claude/agents/verifier.md`
- `.claude/commands/commit-push-pr.md`
- `.claude/commands/dev-change.md`
- `.claude/commands/review.md`
- `.claude/commands/spike.md`
- `.claude/settings.json`
- `.claude/skills/crystallize/SKILL.md`
- `.claude/skills/domain-modeling/SKILL.md`
- `.claude/skills/explore/INTENT-FORMAT.md`
- `.claude/skills/explore/SKILL.md`
- `.claude/skills/gauntlet-loop/SKILL.md`
- `.claude/skills/grilling/SKILL.md`
- `.claude/skills/grilling/agents/openai.yaml`
- `.claude/skills/handoff/SKILL.md`
- `.claude/skills/handoff/agents/openai.yaml`
- `.claude/skills/karpathy-guidelines/SKILL.md`
- `.claude/skills/rescan-docs/SKILL.md`
- `.claude/skills/setup-update/SKILL.md`
- `.claude/skills/setup-update/scripts/setup_update.py`
- `.harness/docs/design.md`
- `.harness/docs/setup.md`
- `.harness/docs/testing.md`
- `.harness/evals/README.md`
- `.harness/evals/cases/102-stop-at-intent-gate.yaml`
- `.harness/scripts/cmd_commit_push_pr.sh`
- `.harness/scripts/cmd_dev_change.sh`
- `.harness/scripts/cmd_review.sh`
- `.harness/scripts/generate_template_manifest.py`
- `.harness/scripts/migrate_to_framework.py`
- `.harness/setup.sh`
- `.harness/template-manifest.json`
- `CLAUDE.md`
- `HARNESS.md`
- `Makefile`
- `README.md`
- `REVIEW.md`
- `openspec/config.yaml`

## 3. Files removed (1)

- `.claude/hooks/post_tool_feature_claude_reminder.py`

Its repeated per-edit warning is replaced by the stateless final feature-doc gate.

## 4. Old workflow vs new workflow

| Before | After |
|---|---|
| One heavy workflow for maintenance and product work | FAST maintenance, STANDARD behavior changes, DEEP architectural work |
| Crystallize always prepares tasks | STANDARD prepares tasks; DEEP stops at architecture/spec acceptance before shape-change |
| No separate program-design stage | DEEP program design records files, interfaces, flows, tests and uncertainty before vertical slicing |
| Implementer prints whole change artifacts | Claimed group and artifact paths; selectively read relevant sections |
| Full checks in implementer, verifier and shipping | Full checks in fresh verifier and shipping, with targeted implementation tests |
| Full check auto-fixes source | Explicit make fmt before verification; non-mutating make check |
| Shipping output truncated through tail | Complete failure output and failing exit status preserved |
| Feature reminder after edits | Missing feature documentation enforced once at final check |

The work is a coherent rollout on one task-group branch. It remains uncommitted:
human review precedes committing/PR creation. Archive remains a later human-gated
operation after the implementation PR merges.

## 5. Superpowers responsibilities removed and retained

Factory skills and commands own exploration, planning, architecture, program
design, decomposition, branch/worktree ownership, review and shipping. Broad
Superpowers planning, subagent-driven development and branch-finishing workflows
are excluded from this lifecycle. Selected TDD, systematic-debugging and
verification techniques remain optional. Existing installations are retained;
removal awaits measured technique value.

## 6. Context and token efficiency

- Root CLAUDE.md: 137 → 60 lines, 5,829 → 3,304 bytes (43.3% fewer bytes).
- HARNESS.md: 273 → 163 lines; lifecycle policy moved to FACTORY.md.
- Implementation loads the claimed group and relevant artifact sections only.
- Verifier receives slug + group, or only a FAST branch name; no implementation narrative.
- Successful commands emit compact status lines; complete failures remain visible.
- Additional utilities require explicit invocation; specialized techniques load conditionally.
- The prescribed successful group workflow drops from three to two full-suite
  runs. This is a workflow comparison, not measured token or elapsed-time savings.
- `.harness/evals/workflow-runs.md` provides the measurement format and tiny-bug,
  normal-feature and architectural-feature scenarios. Historical usage data was
  unavailable, so token savings are not claimed.

## 7. Backwards compatibility

Existing STANDARD tasks work without a tier marker, Context references, or
program-design.md; executable fixtures verify this. Canonical specs and retained
security/env/git hooks were not changed. New helpers and lifecycle skills are
included in template packaging, with migration/update guidance.

Developers must now run make fmt explicitly before verification; make check
fails instead of fixing formatting. Existing feature directories missing CLAUDE.md
must add stable feature documentation before the final gate succeeds. Update
Makefile, helpers and hook settings together and review customized retired hooks.

## 8. Eval and verification results

OpenSpec strict validation passed. Shape-change's skill validator passed. The
independent verifier's report is reproduced below; task 1.6 was marked complete
after this verdict was received.

Verification — software-factory, group 1

Ran:

- `make check` → exit 0; format, lint, types, tests, feature-docs passed.
- `make harness-test` → exit 0; 164 tests passed.
- `make evals-full` → exit 0; 20/20 passed, including all six prompt cases.
- `make evals` → exit 0; 14/14 static cases passed after the routing correction.
- Manifest hash, measurement-field and routing-case discovery assertions → exit 0.
- `git diff --check` → exit 0.

Initial sandbox runs could not access the uv cache or Claude authentication. Approved escalated reruns passed.

Checked against:

- Correct branch `feat/software-factory-g1` → HOLDS.
- Routing, STANDARD/DEEP artifact boundaries, shaping and human gates → HOLDS through artifact inspection and static/prompt evals.
- Legacy claims, DEEP readiness and branch mutex → HOLDS through executable integration tests.
- Independent verifier inputs and FAST diff discovery instructions → HOLDS.
- Non-mutating formatting checks, quiet/verbose output, failure propagation and stateless feature documentation → HOLDS through integration tests.
- Completed tasks 1.1–1.5, packaging and measurement format → HOLDS.
- Nearby regression paths—migration/update, existing hooks, empty source and pytest no-tests behavior—covered by harness tests.

Mismatches: The FAST bug-fix exception initially contradicted the behavior-change routing requirement. It was removed; the corrected artifacts and static eval passed. No outstanding mismatch.

Not covered: Complete end-to-end implementation sessions for all tiers, real shipping/archive operations, and measured token savings. Human gates were inspected without performing those mutations.

Verdict: PASS. Task 1.6’s verification evidence is now available; work remains uncommitted for human review.

## 9. Unresolved decisions

No implementation decision remains unresolved. Representative end-to-end runs
and historical token comparisons remain unmeasured; the provided observation
format supports that follow-up. Human review, commit/PR approval and archive
are intentionally still pending.
