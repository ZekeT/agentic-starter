#!/usr/bin/env python3
"""PostToolUse hook — remind the agent that a feature directory needs a CLAUDE.md.

Triggered by: Write, Edit, MultiEdit tool calls that touch code inside
              `src/<feature>/` when that directory has no `CLAUDE.md`.
Purpose: A feature's CLAUDE.md holds what the next session cannot get from the
         code cheaply — purpose, entry points, invariants, gotchas. Without a
         nudge at write time it never gets written, and every later session
         re-derives the module from its source.

This checks for the file's *existence*, not for an index entry in the root
CLAUDE.md. A list of feature directories is discoverable with `ls src/`, so
maintaining one by hand costs root-CLAUDE.md budget to restate what the file
tree already says.

This is a nudge, not a gate. PostToolUse cannot undo a write, so `exit 1`
surfaces a message to the agent (same pattern as post_tool_lint.py's
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

# Editing these does not tell you anything about a feature's purpose, so they
# should not trigger the reminder on their own.
IGNORED_NAMES = {"CLAUDE.md", "CONTEXT.md", "__init__.py"}


def main() -> None:
    """Remind the agent to write a feature CLAUDE.md when one is missing."""
    payload = json.loads(sys.stdin.read())
    if payload.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        return

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path")
    if not file_path:
        return

    path = Path(file_path)
    parts = path.parts
    if "src" not in parts:
        return

    # src/<feature>/... — a bare src/<file> has no feature directory to document.
    rel = parts[parts.index("src") + 1 :]
    if len(rel) < 2 or path.name in IGNORED_NAMES:
        return

    src_root = Path(*parts[: parts.index("src") + 1])
    feature_dir = src_root / rel[0]
    if (feature_dir / "CLAUDE.md").exists():
        return

    print(
        f"REMINDER: {feature_dir}/ has no CLAUDE.md.",
        file=sys.stderr,
    )
    print(
        "Write one before this group ships: purpose, entry points, invariants, "
        "gotchas; ~30 lines. Stable facts only — never implementation status.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
