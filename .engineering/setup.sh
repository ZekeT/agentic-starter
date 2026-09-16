#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "${1:-}" = "--check" ]; then
  exec ./engineering doctor
fi
if [ "$#" -ne 0 ]; then
  echo 'Usage: .engineering/setup.sh [--check]' >&2
  exit 2
fi
echo 'Setup will install Python development tools and required pinned Matt/Graft dependencies from the network.'
echo 'Optional dependencies and machine-wide settings are unchanged.'
uv sync --all-extras
./engineering deps install --apply
./engineering doctor
echo 'Next: read ENGINEERING.md, configure application roots, and use the local Markdown tracker.'
