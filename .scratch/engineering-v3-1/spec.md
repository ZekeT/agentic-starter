# Brownfield migration and clean consumer template

Status: ready-for-agent — architecture, testing boundaries and ticket breakdown approved

## Problem Statement

OpenSpec migration currently preserves evidence and removes integration before
semantic reconciliation. Legacy starter upgrades invoke this same extraction.
Users cannot migrate arbitrary OpenSpec projects into the native Matt workflow
with an enforceable human checkpoint. Fresh projects also inherit starter
development history, evals and populated installation state.

## Solution

Separate deterministic inventory, semantic reconciliation and approved
finalization. Upgrade legacy infrastructure without prematurely removing
OpenSpec. Generate a clean consumer template from one positive inclusion
manifest, preserving the existing Engineering System architecture and pinned
dependency strategy.

## User Stories

1. As a project owner, I can preview migration without writes.
2. As an OpenSpec user, I can inventory a project that never used this starter.
3. As a maintainer, I can upgrade legacy infrastructure without deciding application semantics.
4. As a reviewer, I can see canonical, active, archived and integration source references.
5. As a reviewer, I can identify the source commit and detect stale evidence.
6. As a developer, I can reconcile prose with actual code and tests.
7. As a domain owner, I must resolve conflicts and uncertain requirements explicitly.
8. As a developer, I retain durable domain context, architectural reasons and feature constraints.
9. As a developer, I can discard redundant and obsolete prose without mechanically creating replacement files.
10. As an owner of active work, I retain implemented behavior and route only remaining work into Matt skills.
11. As an owner of unresolved design, I receive a Wayfinder handoff preserving prior decisions and constraints.
12. As an owner of decided work, I receive input for upstream to-spec rather than an invented approved Matt spec.
13. As a reviewer, I can inspect exact document changes and removals before finalization.
14. As a project owner, finalization refuses dirty repositories, unresolved decisions and stale inputs.
15. As a project owner, retries do not duplicate outputs or overwrite customized documents.
16. As a project owner, committed Git history preserves removed sources by default.
17. As a project owner, I can explicitly request retained snapshots or temporary artifacts.
18. As a developer, completed migration leaves no permanent translation dependency.
19. As a new user, I receive an application-oriented README and useful operational files.
20. As a new user, setup initializes local state and installs pinned dependencies.
21. As a downstream developer, I do not inherit maintainer tests, release scripts, historical docs or populated caches.
22. As a maintainer, I can build reproducible template output and verify its inclusion list.
23. As an existing ordinary-project owner, adoption preserves my application tooling and points out detected OpenSpec.
24. As a maintainer, I can verify all four onboarding paths and representative migration scenarios.

## Implementation Decisions

Accepted by the user in this conversation:

- Default migration and --plan are non-mutating previews. --apply prepares the
  temporary inventory workspace only. --finalize --apply applies reviewed
  documents and removes approved integration. Each mutation requires clean Git.
- A readable semantic plan is paired with a small structured application
  manifest describing exact outputs, removals, source fingerprints and unresolved
  decisions. It is temporary migration evidence, not application workflow state.
- The finalizer validates approval scope and freshness; it does not determine
  semantic truth or accept unresolved decisions.
- Legacy-starter upgrades infrastructure and preserves OpenSpec pending semantic
  reconciliation. The old openspec command becomes a deprecated alias to the new
  safe entrypoint, not a second destructive path.
- New project migration defaults to git-only preservation, verifying removed
  source bytes against committed history. Snapshots require explicit selection.
- One authoritative positive inclusion manifest drives template generation.
  Existing source locations remain where useful; distinct README and Makefile
  inputs express consumer-specific content without duplicating runtime code.
- Initial distribution is a generated directory. Remote template branch or
  repository publication is deferred.
- Setup initializes missing installation state from the distribution manifest;
  existing installation state and customization safeguards remain authoritative.
- Temporary review artifacts can be removed following successful validation and
  human acceptance. Normal development does not depend on migration evidence.
- The semantic skill inspects prose, code and tests, explains classifications,
  escalates conflicts, and routes active work to upstream Matt skills. It does not
  implement unfinished application work or reproduce Matt's workflow logic.
- Maintainer-only evals and tests remain upstream. Consumer gates must not refer
  to omitted files. Managed upstream skills continue to be installed from pins.
- Application migration completion requires doctor and the project's check,
  plus applicable Graft checks; failures cannot produce a completion claim.

- Exclude upstream tracker artifacts from packaging, but keep downstream local Markdown tracker artifacts trackable in Git.
- Permit narrowly scoped legacy-recognition strings in migration runtime, ownership baselines and migration documentation; reject installed legacy workflows and artifacts.

## Testing Decisions

Approved testing boundaries:

- Prefer externally observable command behavior against temporary committed Git
  repositories. Extend the existing migration and installation test patterns.
  Check exit status, repository changes, preserved bytes and actionable reports.
- Cover preview immutability, dirty-tree refusal, stale source/output rejection,
  unresolved semantic decisions, path/symlink safety, rollback and repeat runs.
- Use all six requested fixture scenarios: matching canonical behavior, conflict,
  decided active work, partial implementation, unresolved architecture and an
  arbitrary non-starter OpenSpec project.
- Static skill evals verify the migration boundary and routing instructions, not
  Matt internals. Authored reconciliation examples test finalizer acceptance and
  refusal; they are not evidence of real model judgment.
- Exercise the public template build, compare repeated output, verify positive
  inclusion and forbidden content, initialize a fresh Git checkout, run setup,
  doctor and checks, and confirm that no maintainer-only dependencies remain.
- Perform a semantic dogfood run on a sacrificial realistic repository in addition
  to deterministic/static tests. Human semantic decisions remain human-owned.
- Run formatting before independent maintainability review and behavioral
  verification. Verification includes check, engineering-test, engineering-evals,
  template and migration tests; destructive migration/dependency execution also
  requires independent security review.

## Out of Scope

General migration frameworks; mechanical OpenSpec-to-Matt conversion; new ticket
trackers or graph systems; upstream workflow modifications; permanent compatibility
layers; remote publication; commits, pushes, PRs or merges without user request.

## Further Notes

The source requirements are the root v3.1 Brownfield Migration & Starter Hygiene
guide, including its classifications, six fixtures, acceptance criteria and
implementation order. The user accepted the architecture recommendations after
the read-only audit. Implementation is in progress. Implementation uses a fresh
session per approved ticket and an intended branch selected before implement.
