# Integration evals

`make engineering-evals` runs static policy, dependency, installation and
non-mutating-plan checks. `make engineering-evals-full` additionally invokes
`claude -p` for small-work, uncertain-architecture and shipping-boundary prompts;
it requires authentication and costs tokens. Prompt cases are never an ordinary
product gate. The runner and its small YAML-subset parser are retained from the
previous system; cases test our boundaries, not upstream methodology internals.
