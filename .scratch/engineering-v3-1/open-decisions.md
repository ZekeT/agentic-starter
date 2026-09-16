# Payload requirement conflicts found during implementation

Status: both recommendations explicitly approved by the user

## Preserve tracker artifacts in Git

The v3.1 guide section 32 lists `.scratch/` among generated/cache paths to
exclude through `.gitignore`. The configured Matt local Markdown tracker stores
durable specs and tickets there. ENGINEERING.md explicitly says to keep those
artifacts tracked. Globally ignoring them risks losing multi-session work.

Recommendation: exclude upstream `.scratch/` from generated template packaging,
but leave downstream tracker artifacts trackable. Ignore actual migration
workspaces, caches and local installation state separately.

Alternative: ignore `.scratch/` globally and require explicit force-add for
durable tracker artifacts. This is error-prone and undermines the existing
tracker contract. Do not relocate or modify upstream Matt storage conventions.

## Distinguish migration recognition from legacy workflow installation

Guide section 41's suggested forbidden-term scan allows exceptions only in
user-facing migration documentation. Operational migration code necessarily
contains strings such as `openspec/`, `FACTORY.md`, `HARNESS.md` and legacy cache
names to recognize and safely retire them. The positive consumer payload needs
the migration commands and legacy ownership baseline to operate.

Recommendation: test absence of installed legacy workflows, fixtures, archives
and populated migration state; allow narrowly enumerated recognition strings in
the migration implementation/baseline and user-facing migration documentation.
Scan the rest of the payload strictly, with tests protecting the exception scope.

Alternative: ship migration tooling only as an external maintainer utility and
omit it from the consumer runtime. This changes the agreed self-contained command
surface and requires a separate distribution/bootstrap design.

Both recommendations were explicitly approved. Apply them to packaging, ignore rules and template integrity tests.
