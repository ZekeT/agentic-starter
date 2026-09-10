# Agentic Starter

A portable software-factory starter for taking an idea through accepted specs,
implementation, independent verification, human review, and shipping.

Choose FAST for small maintenance, STANDARD for ordinary behavior changes, and
DEEP for architectural work. OpenSpec preserves canonical system truth; durable
artifacts let each stage start in a fresh session.

- [FACTORY.md](FACTORY.md): workflow tiers, artifacts, lifecycle and human gates.
- [HARNESS.md](HARNESS.md): the shipped Claude Code commands, agents and checks.
- [Setup](.harness/docs/setup.md): bootstrap with `make setup`.

The workflow is runtime-independent; the included adapter targets Claude Code.
Other runtimes can use the artifacts and scripts with their own tool integration.
