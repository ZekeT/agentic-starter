#!/usr/bin/env python3
"""
PostToolUse hook — auto-lint after every file write or edit.

Triggered by: Write, Edit, MultiEdit tool calls.
Purpose: Catch formatting issues immediately, not at commit time.
Source: Agentic Engineering guide (Layer 4: Deterministic Hooks)

Claude Code hook spec:
  stdin  → JSON with keys: tool_name, tool_input, tool_response
  stdout → ignored
  exit 0 → proceed
  exit 1 → block + show stderr to agent
  exit 2 → block silently
"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Run lint checks on the file that was just written or edited."""
    payload = json.loads(sys.stdin.read())
    tool_name = payload.get("tool_name", "")

    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return

    # Resolve the file path that was touched
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path")
    if not file_path:
        return

    path = Path(file_path)
    if not path.exists() or path.suffix != ".py":
        return

    # Run non-mutating checks so the agent sees failures immediately.
    # We do NOT auto-fix here — that's make fmt's job (mutating).
    # The agent should call `make fmt` if these fail.
    checks = [
        ["uv", "run", "black", "--check", str(path)],
        ["uv", "run", "isort", "--check-only", str(path)],
    ]

    failed = []
    for cmd in checks:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            failed.append(result.stdout + result.stderr)

    if failed:
        print("\n".join(failed), file=sys.stderr)
        print("Run `make fmt` to auto-fix.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
