#!/usr/bin/env python3
"""
PreToolUse hook — remind Claude to check the graphify knowledge graph
before doing broad codebase searches.

Triggered by: Grep and Glob tool calls.
Purpose: Nudge agents toward the token-efficient graph query path instead
         of grepping raw files across the whole codebase.

Silent when:
  - graphify-out/GRAPH_REPORT.md does not exist (graph not built yet)
  - The Grep/Glob targets a specific file rather than a directory scan

Reminder only (exit 0 always) — never blocks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPORT = Path("graphify-out/GRAPH_REPORT.md")
_REMINDER = (
    "GRAPHIFY: graph is available. "
    'Try: graphify query "<question>" instead of grepping raw files '
    "(71x fewer tokens). Only grep if the graph doesn't answer your question."
)

# Grep/Glob paths that look like whole-codebase scans (not targeted file reads)
_BROAD_PATHS = {".", "", "/"}


def _is_broad_grep(tool_input: dict[str, object]) -> bool:
    path = str(tool_input.get("path", "") or "")
    return path in _BROAD_PATHS or path.rstrip("/") == "."


def _is_broad_glob(tool_input: dict[str, object]) -> bool:
    pattern = str(tool_input.get("pattern", "") or "")
    # Patterns starting with **/ or ./**/ are codebase-wide
    return (
        pattern.startswith("**")
        or pattern.startswith("./**")
        or pattern.startswith("./")
    )


def main() -> None:
    """Print graphify reminder for broad codebase searches."""
    if not _REPORT.exists():
        return

    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool == "Grep" and _is_broad_grep(tool_input):
        print(_REMINDER)
    elif tool == "Glob" and _is_broad_glob(tool_input):
        print(_REMINDER)


if __name__ == "__main__":
    main()
