# ============================================================
# Makefile — single entry point for all dev commands
# Referenced in CLAUDE.md so agents always use these targets.
# ============================================================

.PHONY: install fmt lint test check clean setup-hooks configure configure-show configure-list

# Source directory — override with: make fmt SRC=mypackage
SRC ?= src

# True once $(SRC) contains at least one .py file. Empty/missing $(SRC) is the
# template's pre-setup state (see pyproject.toml) — interrogate and mypy both
# error out on an empty directory, so skip them until there's real code.
HAS_SRC_FILES := $(shell test -d $(SRC) && find $(SRC) -name '*.py' -print -quit)

# ---- Setup ------------------------------------------------

install:
	uv sync --all-extras

# ---- Format (mutating — fixes code in place) --------------

fmt:
	@mkdir -p $(SRC)
	uv run autoflake --remove-all-unused-imports --remove-unused-variables \
		--in-place --recursive $(SRC) tests
	uv run isort $(SRC) tests
	uv run black $(SRC) tests

# ---- Lint (non-mutating — fails if issues found) ----------

lint:
	@mkdir -p $(SRC)
	uv run black --check $(SRC) tests
	uv run isort --check-only $(SRC) tests
ifneq ($(strip $(HAS_SRC_FILES)),)
	uv run interrogate $(SRC)
	uv run mypy $(SRC)
else
	@echo "  (skipping interrogate/mypy — no .py files in $(SRC) yet)"
endif

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

# ---- BMAD skill management --------------------------------
# After `npx bmad-method install`, trim to the lean pipeline.
# Dry-run first (bmad-trim), then apply (bmad-trim-apply).

bmad-audit:
	uv run python scripts/trim_bmad_skills.py --audit

bmad-trim:
	uv run python scripts/trim_bmad_skills.py

bmad-trim-apply:
	uv run python scripts/trim_bmad_skills.py --apply
