# Agentic Starter — Phase 2

## Maintainability, Code Comprehension, and Factory Lifecycle Tooling

## Objective

Phase 2 should make the software factory better at producing code that is:

* modular
* maintainable
* easier for humans to review
* easier for fresh agents to navigate
* less likely to accumulate oversized files and duplicated abstractions

It should also make the factory itself easier to:

* validate
* install into an existing repository
* update safely over time

This phase must build on the existing Phase 1 architecture rather than introduce a parallel framework.

The three major deliverables are:

```text
1. Maintainability guardrails
2. CODEMAP generation and visual code navigation
3. Factory lifecycle tooling: doctor / adopt / update
```

The factory should continue to prefer deterministic tooling over LLM reasoning whenever the requirement can be enforced mechanically.

---

# 1. Preserve the Phase 1 architecture

Before changing anything, inspect the repository and confirm the Phase 1 implementation.

Do not overwrite or revert Phase 1 decisions.

Specifically preserve:

```text
FAST / STANDARD / DEEP routing

OpenSpec as behavioral system truth

program-design.md for DEEP changes

one task group = one branch = one PR

fresh verifier context

human review gate

compact deterministic verification output

selective rather than orchestration-level Superpowers usage

context boundaries between major factory stages
```

If the current implementation differs slightly from the Phase 1 specification, adapt Phase 2 to the actual repository rather than blindly recreating files.

---

# 2. Add a maintainability contract

Create a short factory-level maintainability policy.

Do not turn this into a large style guide.

It should describe architectural expectations that are useful across languages.

Recommended rules:

```text
Prefer cohesive modules over large multi-responsibility files.

Before adding substantial code to an existing file:
- inspect whether the responsibility already has a natural module;
- search for existing shared abstractions;
- consider whether the new behavior forms a coherent module of its own.

Avoid:
- endlessly extending central service/controller files;
- generic utils dumping grounds;
- duplicated domain logic;
- unnecessary wrapper abstractions;
- circular dependencies;
- deeply nested control flow;
- functions with several unrelated responsibilities.

Prefer:
- clear domain or capability boundaries;
- explicit public interfaces;
- reuse of existing abstractions where appropriate;
- local/simple abstractions before global/framework abstractions;
- dependency direction toward stable domain modules.
```

Add soft file-size guidance:

```text
~300 LOC:
consider whether decomposition would improve cohesion

~500 LOC:
new substantial growth should receive explicit maintainability review

~800 LOC:
new or substantially enlarged handwritten source files require either:
- decomposition, or
- an explicit documented exception
```

These are not universal correctness limits.

Generated code, schemas, migrations, fixtures, protocol definitions, vendored sources, and similar files may be exempt.

The system must distinguish soft guidance from hard failure.

---

# 3. Introduce configurable maintainability thresholds

Add configuration to the factory manifest introduced in Phase 1, or extend the equivalent existing configuration.

Example:

```yaml
maintainability:
  enabled: true
  warn_file_lines: 500
  max_file_lines: 800
```

Do not make language-specific assumptions in the manifest.

Allow projects to override thresholds.

Provide reasonable defaults.

If Phase 1 uses a differently named manifest, extend that rather than creating a second configuration file.

---

# 4. Add deterministic file-growth checks

Implement a lightweight script that inspects handwritten source files.

Purpose:

Detect architectural drift before the codebase accumulates very large files.

The check should be able to report:

```text
file
current LOC
previous/base LOC when available
growth
threshold status
```

Prefer checking the diff against the merge base when running during change verification.

Example output:

```text
✓ maintainability: no pathological file growth
```

or:

```text
⚠ src/users/service.py
  462 → 731 LOC (+269)

  File now exceeds the configured warning threshold.
  Review whether the new responsibility should become a separate module.
```

For an extreme violation:

```text
✗ src/api.py
  611 → 1038 LOC (+427)

  Handwritten source exceeds max_file_lines=800.

  Decompose the new responsibilities or document an approved exception.
```

Do not fail merely because a grandfathered existing file is already large.

A pre-existing 1,100-line file should not make every unrelated PR fail.

Instead evaluate whether the current change materially increases it.

Recommended policy:

```text
existing oversized file + insignificant/no growth
→ warning or ignore

existing oversized file + substantial growth
→ fail or require explicit exception

new oversized file
→ fail or require explicit exception
```

Define "substantial growth" deterministically and document it.

Keep the implementation simple.

---

# 5. Support maintainability exceptions

Avoid forcing agents into artificial decomposition when a large cohesive file is appropriate.

Provide an explicit exception mechanism.

Prefer a checked-in configuration entry rather than inline magic comments spread throughout source files.

Example:

```yaml
maintainability:
  exceptions:
    - path: src/generated/schema.py
      reason: generated schema representation
```

or equivalent structure compatible with the existing manifest.

Every exception must require a short reason.

`factory doctor` should detect malformed or nonexistent exception paths.

Do not allow wildcard exceptions that effectively disable the check for an entire codebase unless explicitly configured by the project.

---

# 6. Extend Program Design with code-shape planning

Update the DEEP `program-design.md` structure.

Add a required section:

```markdown
## Code Shape

### Existing modules reused

- `path/to/module`
  - reason

### New modules

- `path/to/new_module`
  - responsibility
  - intended public surface

### Existing modules intentionally not extended

- `path/to/large_module`
  - why this responsibility should not be added there

### Expected implementation footprint

- expected files changed
- expected files created
- rough size/complexity expectations
```

Do not demand fake line-count precision.

The goal is to make the agent reason about module placement before implementation.

For STANDARD changes, this section may be optional or abbreviated inside `design.md`.

For DEEP changes it should be expected.

---

# 7. Add implementation-vs-design drift detection

During maintainability review, compare the implementation against the accepted program design where available.

Do not require exact compliance.

Flag significant structural divergence such as:

```text
Program design:
3 modules with separated responsibilities

Implementation:
all behavior added to one 900-line service file
```

or:

```text
Program design:
reuse existing parser abstraction

Implementation:
new parser implementation introduced elsewhere
```

This should be reported as a review concern, not automatically treated as behavioral failure.

The purpose is to surface architectural drift to the human reviewer.

---

# 8. Add a maintainability reviewer

Create a dedicated fresh-context reviewer.

Suggested name:

```text
maintainability-reviewer
```

It should be read-only.

It should inspect:

```text
the change diff
program-design.md or design.md when present
relevant immediate neighbouring modules
maintainability check output
```

It should not inspect the implementation session's chain of thought or narrative.

It should answer a narrower question than the behavioral verifier:

```text
Did this change leave the codebase reasonably maintainable?
```

Review for:

```text
oversized files
oversized or multi-responsibility functions
new duplication
missed existing abstractions
unnecessary abstractions
generic utils dumping
poor module boundaries
high coupling
circular dependency risks
unexpected architectural drift
misleading names
tests excessively coupled to implementation structure
```

Do not reward abstraction for its own sake.

The reviewer should explicitly avoid recommending:

```text
interfaces with only one plausible implementation
tiny one-function files without semantic value
generic repositories/services solely to fit a pattern
new frameworks for localized problems
abstractions based only on speculative future needs
```

---

# 9. Maintainability reviewer output format

Keep output concise and useful to the human.

PASS example:

```text
PASS

No maintainability concerns requiring review.
```

Concern example:

```text
CONCERNS

M1 — src/users/service.py grew 418 → 917 LOC

Password-reset orchestration, token management, and persistence were added
to the existing user lifecycle service.

Suggested boundary:
- auth/password_reset.py
- auth/reset_tokens.py

M2 — normalize_user_id() duplicates canonicalize_user_id()
in users/identity.py.

Prefer reuse unless the semantics intentionally differ.
```

Each concern should contain:

```text
identifier
location
problem
why it matters
specific suggested direction
```

Avoid generic commentary such as "consider refactoring for maintainability."

---

# 10. Integrate maintainability review into the lifecycle

Recommended STANDARD/DEEP implementation flow:

```text
implementation
    ↓
targeted tests
    ↓
CODEMAP refresh
    ↓
maintainability reviewer
    ↓
fresh behavioral verifier
    ↓
human review
    ↓
commit / PR
```

FAST may skip the maintainability reviewer when the change is truly small.

However, deterministic file-growth checks should still run as part of the normal full gate.

Do not automatically mutate/refactor code in the reviewer.

If maintainability review fails or raises concerns, return control to the implementation agent or human.

---

# 11. Create CODEMAP.md

Add a repository-level navigation artifact.

Preferred name:

```text
CODEMAP.md
```

Its contract:

```text
CODEMAP is a navigation aid.

It is NOT canonical behavioral truth.
It is NOT the architectural decision record.
It is NOT a replacement for source code.
```

Document the source-of-truth hierarchy:

```text
OpenSpec
→ what the system is expected to do

Design / ADR / program-design
→ why the system is shaped this way

Source code
→ implementation truth

CODEMAP
→ where implementation lives and how major pieces connect
```

---

# 12. CODEMAP goals

A fresh agent or human should be able to answer, within a few minutes:

```text
What are the major modules?

Where are the main entry points?

What does each major module own?

What are the important public functions/classes?

How does a common request flow through the system?

What modules call each other?

Where should I start if I need to change feature X?

What are the expected inputs and outputs at important boundaries?
```

The CODEMAP should optimize navigation, not completeness.

Do not attempt to document every private helper.

---

# 13. CODEMAP structure

Use approximately this structure:

```markdown
# Code Map

> Generated / refreshed from the current implementation.
> Navigation aid only.

## System at a Glance

<Mermaid component/module diagram>

## Entry Points

| Entry | Input | Output | Responsibility |
|---|---|---|---|

## Major Flows

### <Flow name>

<Mermaid flow or sequence diagram>

## Modules

### `path/to/module`

**Responsibility**

...

**Public surface**

- `function_name(input) -> output`
- `ClassName.method(...)`

**Calls**

- ...

**Called by**

- ...

## Important Data / Contracts

...

## Where Should I Look If...

| Goal | Start here | Then inspect |
|---|---|---|

## Generated Metrics

| File | LOC | Functions | Classes |
|---|---:|---:|---:|
```

Keep it compact.

For large repositories, document major modules/capabilities rather than every leaf file.

---

# 14. Generate CODEMAP mechanically where possible

Do not make an agent manually inspect and rewrite the whole map after every change.

Implement deterministic source inspection first.

For Python v1, use the standard library AST where practical.

Extract at least:

```text
module paths
imports
top-level classes
top-level functions
public method/function signatures where practical
line counts
known entry points
approximate static call relationships where reasonably reliable
```

Do not attempt perfect dynamic call-graph resolution.

Label inferred/approximate edges appropriately if necessary.

Avoid adding a heavyweight language server dependency solely for v1.

---

# 15. Separate machine data from rendered Markdown

Design CODEMAP generation around an intermediate graph representation.

For example:

```text
.codemap/
  graph.json
```

Possible shape:

```json
{
  "modules": [],
  "symbols": [],
  "imports": [],
  "calls": [],
  "entrypoints": []
}
```

The exact schema is up to the implementation.

The important architectural rule is:

```text
source analysis
    ↓
normalized graph model
    ↓
CODEMAP.md renderer
```

rather than directly coupling AST traversal to Markdown strings.

This enables future renderers without rewriting analysis.

---

# 16. Mermaid is the required first renderer

Generate Mermaid diagrams in CODEMAP.md.

At minimum support:

```text
module dependency graph
one or more main call/request flows where entry points are discoverable
```

Do not generate enormous unreadable graphs.

Apply limits such as:

```text
major modules only
collapse internal helpers
omit stdlib and third-party dependency nodes
limit graph depth
```

If necessary, generate multiple smaller diagrams by capability.

Prefer:

```text
auth
billing
factory lifecycle
verification
```

over one 120-node graph.

---

# 17. Human-readable annotations

Static analysis cannot infer architectural intent reliably.

Allow a small manually maintained annotation file.

Example:

```yaml
codemap:
  modules:
    src/auth/password_reset.py:
      responsibility: Owns password reset orchestration.
    src/users/repository.py:
      responsibility: Persistence boundary for user records.
```

Do not duplicate symbol lists manually.

Use annotations only for semantic information machines cannot reliably infer.

If Phase 1 already has feature-level CLAUDE.md files or capability metadata that can provide this information, consider reusing them rather than adding another file.

Avoid duplicate documentation stores.

---

# 18. Add "Where Should I Look If..." navigation

This is important for both humans and agents.

Allow CODEMAP to contain capability-oriented navigation:

```text
I want to change authentication
→ start at src/auth/

I want to change workflow routing
→ start at factory/routing.py

I want to change verification
→ start at .harness/verifier/ or equivalent
```

Prefer generating this from existing capability/spec/module metadata where possible.

Use manual annotations only when necessary.

---

# 19. Make CODEMAP a retrieval index for agents

Update root/factory instructions so agents use progressive disclosure:

```text
When entering an unfamiliar area:

1. Read the relevant OpenSpec capability if behavior matters.
2. Consult CODEMAP for implementation location and call flow.
3. Read only the modules identified by those artifacts.
4. Expand retrieval only when needed.
```

Do not instruct agents to load all of CODEMAP for trivial localized work if it becomes large.

Where possible, CODEMAP headings should make targeted retrieval easy.

---

# 20. Add a CODEMAP command

Add an explicit command such as:

```text
factory map
```

or the equivalent naming convention used in Phase 1.

Support:

```text
factory map
```

Refresh the full map.

Optional later:

```text
factory map --check
```

Verify whether the checked-in map is current without rewriting it.

For Phase 2, implement `--check` if it is straightforward and useful for CI.

Do not introduce nondeterministic timestamps into generated output unless necessary, because they make every run dirty.

Stable input should produce stable output.

---

# 21. Integrate CODEMAP refresh into implementation completion

After implementation and targeted tests:

```text
factory map
```

should refresh the map before maintainability review and behavioral verification.

Do not regenerate it after every file edit.

Do not turn CODEMAP generation into a noisy post-tool hook.

It is a lifecycle boundary artifact.

---

# 22. CODEMAP and PR review

Update the review process so the human reviewer is directed to:

```text
1. relevant OpenSpec delta
2. design/program design
3. CODEMAP changes
4. implementation diff
5. verifier results
```

CODEMAP changes should help explain architectural movement.

If a previously simple flow suddenly has many additional nodes or cross-module dependencies, this should be visible in review.

Do not treat the map as proof of correctness.

---

# 23. Add factory lifecycle tooling

Implement a minimal factory-management CLI or script entry point.

Prefer one consistent interface.

Recommended:

```text
factory doctor
factory map
factory adopt
factory update
```

If Phase 1 already introduced a CLI name, extend that instead.

Do not create separate unrelated scripts if a coherent CLI exists.

---

# 24. `factory doctor`

Purpose:

```text
Validate that the repository is a healthy installation of the software factory.
```

This must be deterministic and fast.

Check at least:

```text
factory manifest exists and parses
required factory directories exist
required commands exist
required hooks exist
OpenSpec structure is valid
required scripts are executable where relevant
gitignore contains required protections
environment/secrets protections are configured
factory-managed files are internally consistent
maintainability configuration is valid
maintainability exception paths are valid
CODEMAP configuration is valid
eval configuration exists
installed factory version is known
```

Example:

```text
Agent Factory Doctor

✓ manifest
✓ OpenSpec
✓ commands
✓ hooks
✓ git protections
✓ environment protection
✓ maintainability policy
✓ CODEMAP
✓ eval configuration

⚠ CODEMAP is stale
✗ verifier configuration does not match factory version

2 issues found
```

Provide actionable remediation.

---

# 25. Dogfood doctor against the starter

The `agentic-starter` repository itself should pass:

```text
factory doctor
```

Do not special-case the starter so heavily that the command only works there.

The starter should be a normal valid factory installation.

Add doctor to CI / `make check` / factory eval flow where appropriate.

Avoid recursive command loops.

For example, if:

```text
make check
```

calls `factory doctor`, then `factory doctor` must not call `make check`.

---

# 26. Add factory version metadata

The factory needs to know what template/version is installed.

Extend the manifest:

```yaml
factory:
  version: "2.x.x"
```

Use the repository's actual versioning convention if one exists.

Do not invent package-release infrastructure unless necessary.

A simple semantic version string is sufficient initially.

---

# 27. Track managed files

The factory needs to know which files belong to the factory versus the application.

Add an explicit managed-file model.

Examples:

```text
.harness/
selected .claude/commands/
selected .claude/hooks/
factory CLI scripts
factory eval configuration
```

Do NOT automatically claim ownership over:

```text
the entire CLAUDE.md
the project's Makefile
application source
CI
project documentation
```

unless those files are truly generated and owned by the factory.

Mixed-ownership files need special handling.

---

# 28. Store upstream fingerprints

For safely updating installed factory files, track the upstream version or content hash of managed files.

Possible manifest state:

```yaml
managed_files:
  .harness/scripts/verify.py:
    upstream_hash: "<hash>"
```

The implementation may use a separate machine-owned metadata file if keeping hashes out of the human-facing manifest is cleaner.

Example:

```text
.factory/
  state.json
```

This is acceptable because it represents installation metadata, not workflow/task status.

Do not confuse this with the forbidden redundant `00-status.md` workflow state.

---

# 29. Implement `factory adopt`

Purpose:

```text
Bring an existing repository into the software factory safely.
```

Do not blindly copy the starter over an existing repo.

Adoption must be inspection-first.

Detect where practical:

```text
languages
package/build tools
test commands
lint/typecheck commands
existing Makefile/task runner
existing CLAUDE.md / AGENTS.md
existing OpenSpec/spec documentation
existing hooks
existing CI
existing .gitignore
existing agent configuration
repository structure
```

The initial implementation does not need perfect language detection.

Support the repository types already reasonably supported by agentic-starter first.

---

# 30. Adoption must have plan and apply stages

Prefer:

```text
factory adopt
```

to generate/show a proposed plan.

Then either:

```text
factory adopt --apply
```

or another explicit apply mode.

Do not destructively modify repository configuration without clearly surfacing what will happen.

The adoption plan should classify actions:

```text
ADD
MERGE
PRESERVE
CONFLICT
SKIP
```

Example:

```text
ADD
.factory.yml
.harness/

MERGE
CLAUDE.md
Makefile

PRESERVE
.github/workflows/ci.yml
existing tests

CONFLICT
existing command named /review
```

---

# 31. Preserve project-specific instructions during adoption

Existing repos may already have:

```text
CLAUDE.md
AGENTS.md
custom scripts
CI
lint rules
release commands
deployment instructions
```

Do not replace them wholesale.

Where a file has mixed ownership, merge factory instructions into a clearly bounded section.

Example:

```markdown
<!-- agent-factory:start -->
...
<!-- agent-factory:end -->
```

Use marker blocks only for files where they make sense.

Do not add marker blocks to application source.

Project-specific instructions outside the managed region must remain untouched.

---

# 32. Adoption should infer commands conservatively

If test/lint/build commands are obvious from existing tooling, propose them.

Examples:

```text
pyproject.toml + pytest config
→ likely pytest

package.json scripts.test
→ npm/pnpm/yarn test depending on lockfile
```

Do not fabricate commands when uncertain.

If the existing repository already has a canonical `make check`, preserve it unless there is a strong reason not to.

The factory should adapt to the repo more often than the repo adapts to the factory.

---

# 33. Adoption output

After a successful adoption report:

```text
Factory installed

Detected:
- Python
- pytest
- Ruff
- mypy
- existing CLAUDE.md

Added:
- .factory.yml
- .harness/...
- OpenSpec structure
- factory commands

Merged:
- CLAUDE.md
- Makefile

Preserved:
- GitHub Actions
- project-specific instructions

Next:
factory doctor
```

Run `factory doctor` automatically after apply if that does not create undesirable side effects.

---

# 34. Implement `factory update`

Purpose:

```text
Update the factory infrastructure without destroying project customizations.
```

This is not the same as updating application dependencies.

Use managed-file metadata and upstream fingerprints.

Classify each managed file:

```text
unchanged locally / changed upstream
→ replace safely

unchanged locally / unchanged upstream
→ no action

changed locally / unchanged upstream
→ preserve local file

changed locally / changed upstream
→ conflict / merge required
```

Do not silently overwrite local modifications.

---

# 35. Prefer deterministic update handling

For files fully owned by the factory:

Use deterministic replacement when local contents still match the recorded upstream version.

For marker-managed sections:

Replace only the managed section.

For files changed both locally and upstream:

Prefer:

```text
three-way merge
```

when feasible.

If a clean deterministic merge is not possible:

```text
report conflict
do not overwrite
```

Do not invoke an LLM merely because a file differs.

Agent-assisted conflict resolution may be offered as a later workflow, but deterministic update behavior comes first.

---

# 36. Update safety

Before modifying files:

Create enough state to recover.

Prefer relying on Git when the repository is clean.

If the worktree has relevant uncommitted modifications:

```text
warn or refuse update
```

unless a safe path is implemented.

Do not hide changes in temporary backup directories without documenting them.

After update:

```text
factory doctor
factory map --check
factory eval
```

as appropriate.

---

# 37. Self-update / starter maintenance

When changing the `agentic-starter` factory source itself, provide a documented workflow such as:

```text
make check
factory doctor
factory map --check
factory eval
```

If template snapshots or managed-file manifests must be regenerated after modifying factory source, provide a deterministic command for that.

For example:

```text
factory template refresh
```

only if such a concept is actually required.

Avoid adding commands merely for symmetry.

---

# 38. Extend factory evals

Add static evals covering maintainability and lifecycle behavior.

At minimum verify:

```text
maintainability thresholds exist

new pathological handwritten files are detected

grandfathered oversized files do not automatically fail unrelated changes

exceptions require reasons

program-design supports code-shape planning

maintainability reviewer is read-only

CODEMAP declares itself non-canonical

CODEMAP generation is deterministic for stable input

CODEMAP excludes third-party dependencies from primary diagrams

factory doctor detects missing required structure

factory doctor detects invalid manifest configuration

factory adopt has a non-destructive planning stage

factory adopt preserves project-specific instructions

factory update does not overwrite locally modified managed files silently

factory update detects dual-change conflicts

agentic-starter passes factory doctor
```

Use static tests where possible.

Only add LLM behavioral evals for properties that cannot be expressed deterministically.

---

# 39. Add CODEMAP-specific tests

For a small test fixture repository, verify that source analysis identifies:

```text
modules
functions
classes
imports
entry points where supported
basic call edges
```

Verify generated Markdown contains:

```text
System at a Glance
Entry Points
Modules
Where Should I Look If...
```

Verify Mermaid output is syntactically stable enough for common renderers.

Do not test exact whitespace unless required.

Prefer semantic assertions.

---

# 40. Add maintainability fixture tests

Create fixtures such as:

```text
small cohesive module
new 900-line source file
existing 900-line grandfathered file
existing 700-line file growing to 950 lines
generated 1,500-line file with exception
duplicate exception path
missing exception path
```

Ensure the policy behaves predictably.

---

# 41. Documentation for humans

Update the factory documentation to explain the new mental model.

Keep it visual and concise.

Add diagrams similar to:

```text
DESIGN INTENT

OpenSpec
   ↓
design / program design
   ↓
implementation
```

and:

```text
IMPLEMENTATION UNDERSTANDING

source code
   ↓ static analysis
code graph
   ↓
CODEMAP.md
   ↓
human + agent navigation
```

and:

```text
FACTORY LIFECYCLE

new repo ─────→ init
existing repo → adopt
                    ↓
                 doctor
                    ↓
               development
                    ↓
                  update
                    ↓
                 doctor
```

Use Mermaid where practical.

---

# 42. Keep documentation roles distinct

Do not let the following collapse into one giant document:

```text
OpenSpec
behavioral requirements

design.md / ADR
architectural intent

program-design.md
implementation plan before coding

CODEMAP.md
implemented navigation map

CLAUDE.md
high-frequency agent instructions

FACTORY.md / equivalent
human explanation of factory lifecycle
```

Each artifact should have one primary job.

If two documents repeat the same paragraphs, consolidate.

---

# 43. Do not create per-feature documentation automatically

Avoid generating a new permanent Markdown file for every small implementation.

CODEMAP should describe the current codebase globally or by existing capability structure.

OpenSpec archives already preserve change history.

The factory should not accumulate:

```text
feature-a-implementation-summary.md
feature-b-implementation-summary.md
feature-c-implementation-summary.md
```

unless a project explicitly chooses that model.

---

# 44. Keep token efficiency in mind

Phase 2 must not solve maintainability by adding enormous agent prompts.

Prefer:

```text
static checks
small structured artifacts
generated navigation
conditional reviewers
targeted retrieval
```

over:

```text
larger CLAUDE.md
more always-loaded skills
repeating design rules in every command
```

The maintainability policy should be referenced from relevant stages rather than copied verbatim everywhere.

---

# 45. Recommended implementation order

Implement in small, reviewable units.

Suggested order:

```text
1. Inspect and document current Phase 1 state.

2. Add maintainability configuration and policy.

3. Implement deterministic file-size / growth checks.

4. Add maintainability fixtures and evals.

5. Extend program-design with code-shape planning.

6. Add maintainability reviewer and lifecycle integration.

7. Design internal CODEMAP graph schema.

8. Implement Python source analyzer.

9. Implement CODEMAP Markdown + Mermaid renderer.

10. Add factory map / map --check.

11. Integrate CODEMAP refresh before review.

12. Update agent retrieval guidance to use CODEMAP.

13. Implement factory doctor.

14. Add managed-file/version metadata.

15. Implement factory adopt plan mode.

16. Implement factory adopt apply mode.

17. Implement factory update classification.

18. Implement deterministic update/merge handling.

19. Dogfood doctor/adopt/update behavior against test fixtures and starter.

20. Update factory documentation and diagrams.

21. Run full static and behavioral evals.

22. Run repository verification suite.
```

Do not implement Wayfinder or advanced visualization before the basic graph model and Mermaid CODEMAP are stable.

---

# 46. Explicit non-goals for Phase 2

Do NOT attempt to build:

```text
a full language server

perfect whole-program call graph analysis

automatic AI refactoring of every large file

an IDE

a HumanLayer clone

a package manager

a general project scaffolding ecosystem

automatic semantic merge using an LLM

multi-language CODEMAP support for every language

Wayfinder UI integration
```

Design extension points so these may be added later.

But keep Phase 2 narrow enough to remain maintainable itself.

---

# 47. Acceptance criteria — maintainability

Phase 2 is successful when:

```text
Agents receive concrete module/cohesion guidance rather than generic
"write clean code" instructions.

Pathological new file growth is detected deterministically.

Large existing files are not blindly grandfathered into unlimited future
growth.

Exceptions are possible and documented.

DEEP program designs describe intended module boundaries before coding.

A fresh maintainability reviewer can identify architectural concerns
without modifying code.

The human reviewer can see when implementation shape diverges materially
from accepted program design.
```

---

# 48. Acceptance criteria — CODEMAP

Phase 2 is successful when:

```text
A CODEMAP.md can be generated deterministically from a supported repo.

The CODEMAP contains a concise Mermaid system/module view.

Major entry points and public surfaces are discoverable.

Important inputs/outputs are represented where they can be statically
determined or manually annotated.

A fresh agent can use CODEMAP as a retrieval index instead of broadly
reading the repository.

The CODEMAP clearly states that it is not canonical behavioral truth.

Stable source code produces stable CODEMAP output.

CODEMAP is refreshed at the implementation/review boundary rather than
after every edit.
```

---

# 49. Acceptance criteria — factory lifecycle

Phase 2 is successful when:

```text
factory doctor validates a normal installed factory.

agentic-starter itself passes factory doctor.

factory adopt can inspect an existing repository and show a non-destructive
adoption plan.

factory adopt preserves existing project-specific instructions and tooling.

factory update can distinguish untouched managed files from locally modified
ones.

factory update never silently overwrites a file changed both upstream and
locally.

managed factory ownership is explicit.

application source remains outside factory ownership.

factory structural behavior is covered by deterministic evals.
```

---

# 50. Final implementation report

When complete, return a concise implementation report containing:

```text
## Maintainability

Rules introduced
Static checks
Threshold behavior
Exception mechanism
Reviewer behavior

## CODEMAP

Analyzer architecture
Graph schema
Generated sections
Mermaid diagrams
Known analysis limitations

## Factory Lifecycle

doctor behavior
adopt behavior
update behavior
managed-file strategy

## Workflow Changes

Old:
implementation → verifier → review

New:
implementation
→ map refresh
→ maintainability review
→ verifier
→ human review

## Files

Added
Modified
Removed

## Testing

Static evals
Behavioral evals
Fixture tests
make check / equivalent
factory doctor result

## Deferred Work

Examples:
multi-language analyzers
Wayfinder visualization
richer call graph analysis
agent-assisted merge conflict resolution
```

Also explicitly report any point where the implementation deviated from this manual because the Phase 1 repository architecture made another approach materially simpler.

Prefer the simpler compatible design.

The goal of Phase 2 is not more factory machinery.

The goal is:

```text
better-shaped code
+
cheaper comprehension
+
safe factory distribution
```
