#!/usr/bin/env python3
"""
PreToolUse hook — block dangerous bash commands before execution.

Triggered by: Bash tool calls.
Purpose: Deterministic guardrail. No LLM judgment — pure pattern matching.
Source: Agentic Engineering guide (Layer 4: Deterministic Hooks)

exit 1 → block and show reason to agent so it can correct itself.
"""

import json
import re
import sys

# (pattern, human-readable reason)
DANGEROUS_PATTERNS = [
    (r"\brm\s+-rf\s+/", "rm -rf / is not allowed"),
    (r"\brm\s+--no-preserve-root", "rm --no-preserve-root is not allowed"),
    (
        r"\bgit\s+push\s+.*--force\b(?!-with-lease)",
        "force push without --force-with-lease is not allowed",
    ),
    (r"\bgit\s+push\s+-f\b", "force push (-f) is not allowed — use --force-with-lease"),
    (r"\bchmod\s+-R\s+777\b", "chmod -R 777 is not allowed"),
    (
        r"\bdd\s+if=.*of=/dev/(sd|hd|nvme)",
        "writing directly to block device is not allowed",
    ),
    (r"\bcurl\s+.*\|\s*(ba)?sh\b", "piping curl to shell is not allowed"),
    (r"\bwget\s+.*\|\s*(ba)?sh\b", "piping wget to shell is not allowed"),
    (r":\(\)\s*\{.*\};\s*:", "fork bomb pattern detected"),
    (
        r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE)\b",
        "destructive SQL statement — use a migration",
    ),
]


def main() -> None:
    """Check bash command against dangerous pattern list."""
    payload = json.loads(sys.stdin.read())

    if payload.get("tool_name") != "Bash":
        return

    command = payload.get("tool_input", {}).get("command", "")
    if not command:
        return

    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            print(f"BLOCKED: {reason}", file=sys.stderr)
            print(f"Command was: {command[:200]}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
