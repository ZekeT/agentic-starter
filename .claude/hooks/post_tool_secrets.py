#!/usr/bin/env python3
"""
PostToolUse hook — block secrets from being written to any file.

Triggered by: Write, Edit, MultiEdit tool calls.
Purpose: Defense-in-depth first layer. The Security Reviewer agent
         catches indirect exposure during formal review — keep both.
Source: Agentic Engineering guide (Layer 4: Deterministic Hooks)

exit 1 → block the tool call and show the pattern that matched.
"""

import json
import re
import sys
from pathlib import Path

# Patterns that suggest a hardcoded secret.
# Tuned to avoid false positives on test fixtures and example values.
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][A-Za-z0-9_\-]{16,}["\']', "API key"),
    (r'(?i)(secret[_-]?key|secret)\s*=\s*["\'][A-Za-z0-9_\-]{16,}["\']', "Secret key"),
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{6,}["\']', "Password"),
    (r'(?i)(token)\s*=\s*["\'][A-Za-z0-9_\-\.]{20,}["\']', "Token"),
    (r'(?i)(aws_access_key_id)\s*=\s*["\'][A-Z0-9]{20}["\']', "AWS key"),
    (r'(?i)(aws_secret_access_key)\s*=\s*["\'][A-Za-z0-9/+=]{40}["\']', "AWS secret"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI/Anthropic key"),
]

# Files that are allowed to contain secret-like patterns (e.g., .env.example)
ALLOWED_PATHS = {".env.example", ".env.sample", ".env.template"}


def main() -> None:
    """Scan newly written file content for secret patterns."""
    payload = json.loads(sys.stdin.read())
    tool_name = payload.get("tool_name", "")

    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    if Path(file_path).name in ALLOWED_PATHS:
        return

    # Get the content being written
    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    if not content:
        return

    hits = []
    for pattern, label in SECRET_PATTERNS:
        if re.search(pattern, content):
            hits.append(label)

    if hits:
        print(
            f"BLOCKED: Possible secret(s) detected: {', '.join(hits)}", file=sys.stderr
        )
        print(
            "Use environment variables or a secrets manager instead.", file=sys.stderr
        )
        print(
            "If this is a false positive, add the pattern to ALLOWED_PATHS.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
