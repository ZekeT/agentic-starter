#!/usr/bin/env python3
"""
PostToolUse hook — remind the agent to link new feature CLAUDE.md files.

Triggered by: Write, Edit, MultiEdit tool calls that touch a feature-level
              `src/<feature>/CLAUDE.md` (never the root CLAUDE.md).
Purpose: Agents add a feature CLAUDE.md and forget the one-line pointer in the
         root CLAUDE.md, leaving the new file undiscoverable. Nudge at write
         time, when the fix is one line, rather than at review time.

This is a nudge, not a gate: it does a loose substring check, not a strict
parse of the root CLAUDE.md's structure. PostToolUse can't undo a write anyway, so
`exit 1` here surfaces a message to the agent (same pattern as post_tool_lint.py's
"run `make fmt`" reminder) rather than reverting anything.

Claude Code hook spec:
  stdin  → JSON with keys: tool_name, tool_input, tool_response
  stdout → ignored
  exit 0 → proceed
  exit 1 → block + show stderr to agent
  exit 2 → block silently
"""

import json
import sys
from pathlib import Path


def main() -> None:
    """Remind the agent to add a root CLAUDE.md pointer for feature CLAUDE.md files."""
    payload = json.loads(sys.stdin.read())
    tool_name = payload.get("tool_name", "")

    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path")
    if not file_path:
        return

    parts = Path(file_path).parts
    if "src" not in parts:
        return

    rel = parts[parts.index("src") + 1 :]
    if len(rel) != 2 or rel[1] != "CLAUDE.md":
        return
    feature_name = rel[0]

    root_md = Path("CLAUDE.md")
    if not root_md.exists():
        return

    if feature_name not in root_md.read_text():
        print(
            f"REMINDER: '{feature_name}' has no pointer in the root CLAUDE.md.",
            file=sys.stderr,
        )
        print(
            "Add a one-line entry under Project Structure, e.g.:",
            file=sys.stderr,
        )
        print(f"  {feature_name}/  # <one-line purpose>", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
