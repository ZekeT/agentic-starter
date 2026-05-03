#!/usr/bin/env bash
# setup.sh — bootstrap a new project from this template
# Run once after cloning: bash setup.sh
# Source: Agentic Engineering guide (Getting Started, slide 29)

set -e

echo "=== Agentic Base — Project Setup ==="
echo ""

# 1. Install uv if not present
if ! command -v uv &> /dev/null; then
  echo "[1/8] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source "$HOME/.cargo/env" 2>/dev/null || true
else
  echo "[1/8] uv already installed ($(uv --version))"
fi

# 2. Install Python deps
echo "[2/8] Installing Python dependencies..."
uv sync --all-extras

# 3. Install BMAD then immediately trim to the lean pipeline
echo "[3/8] Installing BMAD..."
if command -v npx &> /dev/null; then
  npx bmad-method install
  echo "  Trimming to lean pipeline (Agentic Engineering guide — 5 steps only)..."
  echo "yes" | uv run python scripts/trim_bmad_skills.py --apply
  echo "  BMAD trimmed. Run 'make bmad-audit' to verify."
else
  echo "  SKIP: npx not found. Install Node.js then run:"
  echo "    npx bmad-method install && make bmad-trim-apply"
fi

# 4. Apply model config to .claude/agents/*.md frontmatter
echo "[4/8] Applying model configuration to agents..."
uv run python scripts/configure.py

# 5. Bootstrap .env from the committed template if missing
echo "[5/8] Bootstrapping .env from .env.template..."
if [ -f .env ]; then
  echo "  .env already exists — leaving it alone."
elif [ -f .env.template ]; then
  cp .env.template .env
  echo "  .env created from .env.template — fill in real values before running."
else
  echo "  SKIP: .env.template not found."
fi

# 6. Superpowers — must be installed manually inside Claude Code.
# /plugin is an interactive slash command, not a CLI argument.
# There is no way to automate this from a shell script.
echo "[6/8] Superpowers (manual step required)..."
echo ""
echo "  Open Claude Code in this project directory, then run:"
echo "    /plugin marketplace add obra/superpowers-marketplace"
echo "    /plugin install superpowers@superpowers-marketplace"
echo ""
echo "  This installs globally to ~/.claude/ — do it once,"
echo "  and it works for all your projects."
echo

# 7. Install graphify (optional but recommended).
# Use `uv pip` so it lands in the project venv rather than the system Python.
echo "[7/8] Setting up graphify..."
if uv pip install graphifyy --quiet 2>/dev/null; then
  uv run graphify claude install || true
  echo "  graphify installed and wired to CLAUDE.md"
else
  echo "  SKIP: graphify install failed. Run manually:"
  echo "    uv pip install graphifyy && uv run graphify claude install"
fi

# 8. Verify make check works (no src yet, just confirm tooling)
echo "[8/8] Verifying toolchain..."
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
