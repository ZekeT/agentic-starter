# Brownfield source fixtures

These six small repositories contain source prose, executable code and tests.
Copy a `repo/` directory to a temporary directory and initialize/commit Git before
running migration commands. No fixture includes Git internals or installed state.

A matches canonical behavior and retains only domain terminology. B conflicts on
the lock threshold and must block finalization. C has decided active delivery work.
D has partial export work; retain serialization and hand off only the remainder.
E has unresolved delivery architecture and routes to Wayfinder. F is an arbitrary
non-starter project, with no Engineering files or legacy infrastructure.

`expected.json` is an authored semantic example, not generated model output and
not proof of model judgment. It provides classification/routing expectations and
exact proposed document content for finalizer acceptance/refusal tests. A test
harness must bind these records to its actual inventory, reviewed commit, exact
plan hash, write before hashes and source deletion hashes; fixture constants must
never pretend to be approval. B/E need human decisions before finalization.
The fixture unit test executes application tests and checks evidence paths only.
Real semantic dogfood/independent model evaluation must be reported separately.
