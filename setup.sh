#!/usr/bin/env bash
# setup.sh — bootstrap a new project from this template
# Run once after cloning: bash setup.sh
# Source: Agentic Engineering guide (Getting Started, slide 29)

set -e

echo "=== Agentic Base — Project Setup ==="
echo ""

# 1. Install uv if not present
if ! command -v uv &> /dev/null; then
  echo "[1/6] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source "$HOME/.cargo/env" 2>/dev/null || true
else
  echo "[1/6] uv already installed ($(uv --version))"
fi

# 2. Install Python deps
echo "[2/6] Installing Python dependencies..."
uv sync --all-extras

# 3. Install BMAD then immediately trim to the lean pipeline
echo "[3/6] Installing BMAD..."
if command -v npx &> /dev/null; then
  npx bmad-method install
  echo "  Trimming to lean pipeline (Agentic Engineering guide — 5 steps only)..."
  echo "yes" | uv run python scripts/trim_bmad_skills.py --apply
  echo "  BMAD trimmed. Run 'make bmad-audit' to verify."
else
  echo "  SKIP: npx not found. Install Node.js then run:"
  echo "    npx bmad-method install && make bmad-trim-apply"
fi

# 4. Install Superpowers (global — handles developer + code-review workflow)
echo "[4/6] Installing Superpowers..."
if command -v claude &> /dev/null; then
  # Superpowers installs globally to ~/.claude/ — not per-project
  # It provides: subagent-driven-development, code-reviewer, TDD workflow
  # Skills trigger automatically — no manual invocation needed
  claude --dangerously-skip-permissions -p "/plugin marketplace add obra/superpowers-marketplace && /plugin install superpowers@superpowers-marketplace" 2>/dev/null || true
  echo "  If the above failed, run manually inside Claude Code:"
  echo "    /plugin marketplace add obra/superpowers-marketplace"
  echo "    /plugin install superpowers@superpowers-marketplace"
else
  echo "  SKIP: claude CLI not found. Run inside Claude Code:"
  echo "    /plugin marketplace add obra/superpowers-marketplace"
  echo "    /plugin install superpowers@superpowers-marketplace"
fi

# 5. Install graphify (optional but recommended)
echo "[5/6] Setting up graphify..."
if command -v pip &> /dev/null; then
  pip install graphifyy --quiet
  graphify claude install
  echo "  graphify installed and wired to CLAUDE.md"
else
  echo "  SKIP: pip not found. Run manually: pip install graphifyy && graphify claude install"
fi

# 5. Verify make check works (no src yet, just confirm tooling)
echo "[6/6] Verifying toolchain..."
uv run black --version
uv run isort --version-number
uv run autoflake --version
uv run interrogate --version
uv run mypy --version
uv run pytest --version
echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit pyproject.toml — set [project] name, description"
echo "  2. Create src/<your_package>/__init__.py"
echo "  3. Run /plan in Claude Code to start the BMAD planning workflow"
echo "  4. Human gates: requirements → architecture → sprint planning → deploy"
echo ""
echo "Quick reference:"
echo "  make fmt    — format code"
echo "  make lint   — check code"
echo "  make test   — run tests"
echo "  make check  — all three (run before every commit)"
