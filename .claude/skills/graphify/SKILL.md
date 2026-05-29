---
name: graphify
description: >
  Check graphify-out/GRAPH_REPORT.md BEFORE grepping or reading multiple files
  for codebase context. Use for architecture questions, tracing connections between
  components, or any broad code navigation. 71x fewer tokens than raw file reads.
  Trigger on: /graphify, "build knowledge graph", "how does X connect to Y",
  "show me the architecture", or when about to run multiple Grep/Read calls.
---

# Graphify Skill

Turn the project into a queryable knowledge graph for token-efficient
codebase navigation. 71x fewer tokens per query vs reading raw files.

**Default behaviour:** If `graphify-out/GRAPH_REPORT.md` exists, always check
it BEFORE reaching for Grep or Read for codebase exploration. Only fall back
to grepping raw files if the graph doesn't answer your question.

Install: `pip install graphifyy && graphify .`
Trigger: `/graphify` or "build knowledge graph"

---

## When to use this skill

- **Always first:** before any broad codebase search (Grep across `.`, multi-file reads)
- Before answering architecture or cross-component questions
- When tracing how components connect or data flows through the system
- When you've run more than 2 Grep calls without finding what you need — build the graph

## Commands

```bash
# Build / update the graph
graphify .                    # full build
graphify . --update           # re-process only changed files

# Query without reading raw files
graphify query "what connects auth to the database?"
graphify query "show the request lifecycle"
graphify path "UserModel" "APIHandler"
graphify explain "PaymentService"

# Start MCP server for direct graph access
python -m graphify.serve graphify-out/graph.json
```

## How to use the output

1. Read `graphify-out/GRAPH_REPORT.md` for the high-level map
   (god nodes, community structure, surprising connections).
2. Use `graphify query` for specific questions — outputs a focused
   subgraph you can reason over without loading raw files.
3. Use `graph.json` via MCP for repeated structural queries.

## Output files

```
graphify-out/
  GRAPH_REPORT.md   # one-page summary — read this first
  graph.json        # full queryable graph
  graph.html        # interactive visual (open in browser)
  cache/            # SHA256 cache — re-runs only process changed files
```

## Notes

- A PreToolUse hook fires on broad Grep/Glob calls and reminds you to check
  the graph first. It is wired into `.claude/settings.json` — no separate install.
- Token savings compound: first run costs tokens to build, every
  subsequent query reads the compact graph instead of raw files.
- Add `.graphifyignore` to exclude directories (same syntax as `.gitignore`).
- Update after new files land: `graphify . --update` (only re-processes changed files).
