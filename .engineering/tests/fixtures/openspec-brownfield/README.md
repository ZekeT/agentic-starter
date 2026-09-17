# Brownfield source fixtures

These six small repositories contain source prose, executable code and tests.
Copy a `repo/` directory to a temporary directory and initialize/commit Git before
running migration commands. No fixture includes Git internals or installed state.

A matches canonical behavior and retains only domain terminology. B conflicts on
the lock threshold and must block finalization. C has decided active delivery work.
D has partial export work; retain serialization and hand off only the remainder.
E has unresolved delivery architecture and routes to Wayfinder. F is an arbitrary
non-starter project, with no Engineering files or legacy infrastructure.

C/E explicitly describe the serializer as pre-existing behavior. D's proposal
and delta include serialization in the change itself, and its executable tests
demonstrate that slice is delivered. The partial classification must come from
those sources together, not from the checked task alone.

`expected.json` is an authored semantic example, not generated model output and
not proof of model judgment. It provides classification/routing expectations and
exact proposed document content for finalizer acceptance/refusal tests. A test
harness must bind these records to its actual inventory, reviewed commit, exact
plan hash, write before hashes and source deletion hashes; fixture constants must
never pretend to be approval. B/E need human decisions before finalization.
The fixture tests execute each application suite in an isolated copied project,
check evidence references, and run the public preparation CLI against committed
copies. They check authored classification/routing coverage against the resulting
inventory and ensure proposed destinations are not written. Distribution coverage
also verifies that the skill and contract are included as project-owned files.
Real semantic dogfood/independent model evaluation must be reported separately.
