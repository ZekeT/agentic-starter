# CLAUDE.md

@AGENTS.md

---

## Active Model Config

<!-- This section is auto-updated by scripts/configure.py — do not edit manually. -->
<!-- Run `make configure-show` to see current assignments. -->

Provider: `anthropic`

| Tier | Model |
|------|-------|
| planning | `claude-opus-4-8` |
| review | `claude-opus-4-8` |
| implement | `claude-sonnet-5` |
| fast | `claude-haiku-4-5-20251001` |

Advisor strategy: **enabled** — `claude-opus-4-8` advises executor agents (max 3 uses per request).
Source: https://claude.com/blog/the-advisor-strategy

---

## Advisor Strategy

Sonnet/Haiku **drives the full task** and escalates to Opus only when stuck.
This is the inverse of the usual orchestrator pattern — no decomposition,
no worker pool. Frontier reasoning applies only when the executor needs it.

When to invoke the advisor (executor agents should follow this):
- Architectural ambiguity that the story file doesn't resolve
- Conflicting requirements between PRD and architecture
- A blocking bug that's been attempted twice without success
- A security decision with non-obvious tradeoffs

Do **not** invoke for routine decisions. `max_uses: 3` enforces this.

The `advisor_20260301` tool is **Anthropic-only** — it won't be present in
agent definitions when using local models (`make configure PROFILE=ollama-*`).

---

## Claude Code specifics

- Hooks are wired in `.claude/settings.json` (env guard, dangerous-bash, secrets,
  lint, story lifecycle). Never bypass them.
- Superpowers v6+ is installed globally and triggers automatically — see the
  skill listing at session start for what's available.
- Feature folders may carry their own `CLAUDE.md` — see AGENTS.md project
  structure.
