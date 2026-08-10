---
name: graphify
description: >
  Query the codebase knowledge graph for broad architecture questions spanning
  many files. Prefer plain grep/read for anything scoped to one feature.
  Trigger on: /graphify, "build knowledge graph", "how does X connect to Y",
  "show me the architecture".
---

# Graphify Skill

Turn the project into a queryable knowledge graph for token-efficient
codebase navigation. 71x fewer tokens per query vs reading raw files.

**Opt-in:** if `graphify-out/GRAPH_REPORT.md` exists, it's worth checking for
broad architecture or cross-component questions. For anything scoped to one
feature or file, plain Grep/Read is simpler and just as fast.

Install: `pip install graphifyy && graphify .`
Trigger: `/graphify` or "build knowledge graph"

---

## When to use this skill

- Broad architecture or cross-component questions
- Tracing how components connect or data flows through the system
- After several Grep calls without finding what you need — the graph may
  surface the connection faster

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

- Token savings compound: first run costs tokens to build, every
  subsequent query reads the compact graph instead of raw files.
- Add `.graphifyignore` to exclude directories (same syntax as `.gitignore`).
- Update after new files land: `graphify . --update` (only re-processes changed files).
