---
name: graphify
description: Use when answering architecture questions, understanding cross-component relationships, or when grepping for context requires many tool calls on an unfamiliar codebase.
---

# Graphify Skill

Turn the project into a queryable knowledge graph for token-efficient
codebase navigation. 71x fewer tokens per query vs reading raw files.

Install: `pip install graphifyy && graphify claude install`
Trigger: `/graphify` or "build knowledge graph"

---

## When to use this skill

- Before answering architecture questions on an unfamiliar codebase
- When a task requires understanding how multiple components relate
- When grepping for context is taking many tool calls

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

- The PreToolUse hook (installed by `graphify claude install`) reminds
  Claude to consult the graph before grepping raw files.
- Token savings compound: first run costs tokens to build, every
  subsequent query reads the compact graph instead of raw files.
- Add `.graphifyignore` to exclude directories (same syntax as `.gitignore`).
