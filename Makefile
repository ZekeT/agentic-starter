# ============================================================
# Makefile — single entry point for all dev commands
# Referenced in CLAUDE.md so agents always use these targets.
# ============================================================

.PHONY: install fmt lint test check clean configure configure-show configure-list evals evals-full manifest

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

# ---- Harness evals ----------------------------------------
# This repo IS agent configuration; tests/ only covers the Python scripts.
# `evals` is static-only (fast, free, CI default). `evals-full` also runs the
# prompt cases through `claude -p`, which costs tokens and needs auth.

evals:
	python3 evals/run_evals.py

evals-full:
	python3 evals/run_evals.py --full

# ---- Model configuration ----------------------------------
# Edit config/models.json then run one of these.
# PROFILE= optional: make configure PROFILE=anthropic-budget

configure:
	uv run python scripts/configure.py $(if $(PROFILE),--profile $(PROFILE),)

configure-show:
	uv run python scripts/configure.py --show

configure-list:
	uv run python scripts/configure.py --list

# ---- Clean ------------------------------------------------

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."

# ---- Template maintenance (starter repo only) --------------
# Regenerate after changing any template-owned file, before tagging a release.
# Powers the setup-update skill's staleness detection in downstream projects.

manifest:
	uv run python scripts/generate_template_manifest.py
