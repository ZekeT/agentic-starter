# Application manifest v1

This is temporary review evidence, not workflow state. The deterministic finalizer
implements this contract; reconciliation never applies these records itself.
Paths below are relative to the target repository, except `plan.path`, which is
relative to the migration workspace `.engineering/migration-work/openspec/`.

`reconciliation/application.json` is a JSON object with exactly these fields:

| Field | Value |
| --- | --- |
| `schema_version` | integer `1` |
| `inventory_sha256` | SHA-256 of exact `inventory.json` bytes |
| `reviewed_head` | full current Git commit ID used to inspect code/tests |
| `plan` | `{ "path": "reconciliation/plan.md", "sha256": "<exact bytes digest>" }` |
| `writes` | array of `{ "path": "docs/context/example.md", "before_sha256": null, "content": "exact UTF-8 bytes as JSON text" }` |
| `deletes` | array of `{ "path": "openspec/specs/example/spec.md", "before_sha256": "<digest>" }` |
| `canonical` | array of `{ "source": "openspec/specs/example/spec.md", "classification": "KEEP_AS_CONTEXT", "evidence": ["src/example.py", "tests/test_example.py"], "reason": "Explains a domain rule absent from executable behavior." }` |
| `active` | array of `{ "source": "example-change", "state": "DECIDED_NOT_IMPLEMENTED", "route": "to-spec", "evidence": ["openspec/changes/example-change/proposal.md"], "implemented": [], "remaining": ["Decided feature"], "missing_tests": ["Acceptance tests"], "decisions": [] }` |
| `unresolved_decisions` | array of nonempty human-readable questions; must be empty to finalize |

All arrays are required, even when empty. Unknown fields are refused to catch
misspellings and unreviewed extensions. Hashes are lowercase 64-character hex.
`before_sha256: null` means the destination must not exist. For replacements,
`before_sha256` is the exact existing file hash; empty string is not absence.
Content has no implicit newline normalization. Each write/delete path is unique
and the two sets cannot overlap. No wildcard, directory, absolute, traversal,
symlink or `.git` path is permitted. Writes are restricted to durable docs under
`docs/context/`, `docs/adr/`, `docs/features/`, accepted Markdown handoffs under the
configured tracker (`.scratch/` by default), or inventoried integration files being
edited to remove OpenSpec wiring. The plan must explain why each output is needed.
Deletes may only name inventoried OpenSpec tree files or dedicated generated
OpenSpec integration files. Every OpenSpec tree file and detected runtime
integration must have an explicit reviewed delete or integration replacement;
omission means incomplete removal, not implicit consent. Shared files such as
CLAUDE.md, settings, Makefile and package manifests require reviewed replacements,
never wholesale deletion. Inventory existing_docs are evidence, not removal
targets: preserve them unless an exact approved durable-document update is listed. Unknown metadata requires examination;
uncertain removal adds a human decision and blocks finalization.

`canonical.source` must cover every inventory canonical `path`; multiple records
may split meaning within a capability. Classification values are exactly the seven
values in SKILL.md. Each record has a nonempty reason and evidence. `active.source`
is an inventory active-change `name`; every active change has exactly one record.
State values are exactly the six values in SKILL.md. Allowed routes are `wayfinder`,
`to-spec`, `to-tickets`, `none`, `human`. Planning routes to `wayfinder`; decided
work to `to-spec`; partial work to `wayfinder`, `to-spec` or `to-tickets` according
to the remaining decisions/context; implemented and obsolete work to `none`;
unknown work to `human`. If implemented work has gaps, classify the remaining work
as partial. All evidence references name regular repository files present at
`reviewed_head`; cite precise claims/lines in the readable plan. Evidence must
include actual code/tests when available; record their absence honestly otherwise.
The string arrays describe evidence-backed statements, not boolean assertions.
Active `decisions` describes remaining design questions for the handoff. Questions
explicitly accepted by the human for deferral to `wayfinder` may remain there;
other unresolved questions must also appear in `unresolved_decisions` and block
finalization. Accepted deferral belongs in the readable plan, not a fake approval
boolean.
Conflicting/uncertain canonical records, unknown active states and route `human`
block finalization even if `unresolved_decisions` was mistakenly left empty.
Planning with genuinely unresolved decisions remains blocked until human answers
or explicit human acceptance of deferring those questions into the Wayfinder handoff
is recorded in the plan; do not silently erase outstanding migration decisions.

Freshness binds two separate commits: inventory `source_head` preserves original
source history; `reviewed_head` binds semantic review to current application code
and tests. Check current HEAD equals `reviewed_head`, every inventory source hash
still matches, every evidence file matches that commit, and every destination
matches its before hash. Reject dirty Git, unsafe paths and unresolved decisions
before writes. Git-only removal must verify exact source bytes exist at the
inventory preservation commit. Snapshot retention is an explicitly selected
inventory policy, never a default inferred by the skill.

Approval is human authorization of the exact displayed plan, diff and manifest
SHA-256. There is deliberately no `approved: true` field that an agent can assert.
The agent obtains that approval before invoking `--finalize --apply`; this explicit
command is the apply boundary. Any edits after review require renewed review.
The finalizer checks integrity and scope, not whether prose is semantically true.
