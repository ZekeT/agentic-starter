# Architecture

The stdlib Python core in `.engineering/engineering/` owns installation safety, dependency bookkeeping and deterministic checks. `.claude/` adapts shared policy to Claude Code. Upstream skills own workflows; Graft owns derived application structure. See ENGINEERING.md for usage and docs/adr/ for durable decisions.
