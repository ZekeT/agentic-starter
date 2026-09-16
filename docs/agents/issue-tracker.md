# Issue tracker: local Markdown

Use Matt Pocock's installed local Markdown adapter:
[upstream tracker contract](../../.claude/skills/setup-matt-pocock-skills/issue-tracker-local.md).
It owns storage conventions and Wayfinding operations. Specs and tickets are
local repository files under `.scratch/`; keep durable work tracked in Git.

This is the default for new projects regardless of remote hosting provider.
No GitHub API or `gh` CLI is required. To select GitHub Issues or another tracker,
run `/setup-matt-pocock-skills` and update this project-owned configuration.
Do not publish issues remotely without explicit human instructions.
