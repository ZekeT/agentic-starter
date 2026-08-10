#!/usr/bin/env bash
# setup.sh — bootstrap a new project from this template
# Run once after cloning: bash setup.sh
# Source: Agentic Engineering guide (Getting Started, slide 29)

set -e

echo "=== Agentic Base — Project Setup ==="
echo ""

# 1. Install uv if not present
if ! command -v uv &> /dev/null; then
  echo "[1/7] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source "$HOME/.cargo/env" 2>/dev/null || true
else
  echo "[1/7] uv already installed ($(uv --version))"
fi

# 2. Install Python deps
echo "[2/7] Installing Python dependencies..."
uv sync --all-extras

# 3. Apply model config to .claude/agents/*.md frontmatter
echo "[3/7] Applying model configuration to agents..."
uv run python scripts/configure.py

# 4. Bootstrap .env from the committed template if missing
echo "[4/7] Bootstrapping .env from .env.template..."
if [ -f .env ]; then
  echo "  .env already exists — leaving it alone."
elif [ -f .env.template ]; then
  cp .env.template .env
  echo "  .env created from .env.template — fill in real values before running."
else
  echo "  SKIP: .env.template not found."
fi

# 5. Superpowers — must be installed manually inside Claude Code.
# /plugin is an interactive slash command, not a CLI argument.
# There is no way to automate this from a shell script.
echo "[5/7] Superpowers (manual step required)..."
echo ""
echo "  Open Claude Code in this project directory, then run:"
echo "    /plugin marketplace add obra/superpowers-marketplace"
echo "    /plugin install superpowers@superpowers-marketplace"
echo ""
echo "  Already installed on this machine? Update instead (v6.2+ required):"
echo "    /plugin update superpowers@superpowers-marketplace"
echo ""
echo "  This installs globally to ~/.claude/ — do it once,"
echo "  and it works for all your projects."
echo

# 6. Install graphify (optional but recommended).
# Use `uv pip` so it lands in the project venv rather than the system Python.
echo "[6/7] Setting up graphify..."
if uv pip install graphifyy --quiet 2>/dev/null; then
  uv run graphify claude install || true
  echo "  graphify installed. Building initial knowledge graph..."
  uv run graphify . --quiet 2>/dev/null && echo "  Knowledge graph built → graphify-out/GRAPH_REPORT.md" || \
    echo "  WARN: graphify build failed — run 'graphify .' manually after adding source files"
else
  echo "  SKIP: graphify install failed. Run manually:"
  echo "    uv pip install graphifyy && graphify ."
fi

# 7. Verify make check works (no src yet, just confirm tooling)
echo "[7/7] Verifying toolchain..."
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
echo "  3. Plan in Claude Code (Superpowers brainstorming → docs/prd.md,"
echo "     docs/architecture.md), then /sprint-planning"
echo "  4. Human gates: requirements → architecture → sprint planning → deploy"
echo ""
echo "Quick reference:"
echo "  make fmt    — format code"
echo "  make lint   — check code"
echo "  make test   — run tests"
echo "  make check  — all three (run before every commit)"
