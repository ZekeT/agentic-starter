#!/usr/bin/env python3
"""Compatibility entry point for the shared safe factory adopt engine.

Default and --dry invocations are read-only plans. Use --apply explicitly.
Conflicts and --force requests never authorize overwriting project content.
"""

import sys
from pathlib import Path

if sys.version_info < (3, 12):
    sys.exit("Python 3.12+ required; use uv run --no-project --isolated --python 3.12 python with this script.")

STARTER_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STARTER_DIR / ".harness"))
from factory.cli import legacy_main  # noqa: E402


if __name__ == "__main__":
    sys.exit(legacy_main(STARTER_DIR, "adopt"))
