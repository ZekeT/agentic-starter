# ============================================================
# Makefile — single entry point for all dev commands
# Referenced in CLAUDE.md so agents always use these targets.
# ============================================================

.PHONY: install fmt lint test check clean setup-hooks configure configure-show configure-list

# Source directory — override with: make fmt SRC=mypackage
SRC ?= src

# ---- Setup ------------------------------------------------

install:
	uv sync --all-extras

# ---- Format (mutating — fixes code in place) --------------

fmt:
	uv run autoflake --remove-all-unused-imports --remove-unused-variables \
		--in-place --recursive $(SRC) tests
	uv run isort $(SRC) tests
	uv run black $(SRC) tests

# ---- Lint (non-mutating — fails if issues found) ----------

lint:
	uv run black --check $(SRC) tests
	uv run isort --check-only $(SRC) tests
	uv run interrogate $(SRC)
	uv run mypy $(SRC)

# ---- Test -------------------------------------------------

test:
	uv run pytest

# ---- Combined gate (run before every commit) --------------
# Mirrors the pre-commit hook logic so CI never surprises you.
# Order matters: fmt first so lint sees clean code.

check: fmt lint test

# ---- Model configuration ----------------------------------
# Edit config/models.json then run one of these.
# PROFILE= optional: make configure PROFILE=ollama-qwen

configure:
	uv run python scripts/configure.py $(if $(PROFILE),--profile $(PROFILE),)

configure-show:
	uv run python scripts/configure.py --show

configure-list:
	uv run python scripts/configure.py --list

# ---- Hooks ------------------------------------------------
# Install deterministic Claude Code hooks (from .claude/hooks/).
# Run once after cloning.

setup-hooks:
	@echo "Hooks live in .claude/hooks/ — Claude Code loads them automatically."
	@echo "To also set up graphify: pip install graphifyy && graphify claude install"

# ---- Clean ------------------------------------------------

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."
