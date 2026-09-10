# Workflow run measurements

Use one JSON object per completed representative run, saved with the review/eval
results (outside active change artifacts). This is an observation log, not a
workflow-status database; no factory command consumes it or needs it synchronized.
Do not record private prompts, environment values, or transcripts.

```json
{
  "revision": "commit SHA or working-tree identifier",
  "scenario": "tiny-bug | normal-feature | architectural-feature",
  "workflow_tier": "FAST | STANDARD | DEEP",
  "agent_sessions": 0,
  "subagent_sessions": 0,
  "full_check_runs": 0,
  "skill_invocations": 0,
  "skills_used": [],
  "approx_context_tokens": null,
  "input_tokens": null,
  "output_tokens": null,
  "tool_calls": null,
  "result": "success | failure",
  "notes": "measurement source, coverage gaps, retries, optional technique value"
}
```

Count every session and retry, including verifier sessions, and every invocation
of the full gate, including failed checks. Count specialized skills separately
from sessions. Use runtime usage reports for tokens/tool calls when available;
use `null` when unavailable, never an invented zero. Label estimates as estimates
in notes. Record input/output/cached tokens separately if the runtime exposes
those categories; do not compare incompatible totals.

## Representative scenarios

| Scenario | Request | Expected route and evidence |
|---|---|---|
| tiny-bug | Correct a typo in a non-contractual error message without changing meaning | FAST, no new OpenSpec change, branch verification and human review |
| normal-feature | Add password reset behavior to an existing account flow | STANDARD, accepted intent then proposal/spec/design/tasks, completed task group |
| architectural-feature | Replace persistence architecture while maintaining compatibility | DEEP, accepted architecture, program design, vertical slices and migration tests |

Run the same scenario on baseline and candidate revisions with comparable model,
runtime, repository fixture, cache conditions and check suite. A routing-only
prompt eval is not an implementation run: label it as routing-only and do not
infer full workflow costs from it. Compare result quality and regression coverage
alongside counts. Keep failed runs; excluding retries understates cost.

No historical token/session measurements are supplied with this refactor. The
old prescribed workflow ran a full gate in implementer, verifier and shipping;
the new prescribed workflow runs it in verifier and shipping. That is a reduction
from three to two full-suite invocations for an unchanged successful task group,
not a measured token or elapsed-time saving. Formatting is performed explicitly
before verification and may need repeating after edits.

Record actual Superpowers techniques used and whether they resolved a problem
or supplied a useful test. Compare runs with and without those optional techniques
before deciding whether the remaining dependency earns its cost. The refactor
retains existing installations; it does not claim unmeasured benefits.
