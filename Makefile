# Python application template. Adoption preserves the target's own check recipe.
MAKEFLAGS += --no-print-directory
export MAKEFLAGS
export UV_OFFLINE = 1
export UV_PYTHON_DOWNLOADS = never
SRC ?= src
FORMAT_PATHS = $(wildcard $(SRC) tests .engineering/engineering .engineering/tests)

.PHONY: install setup fmt lint test check engineering-test manifest
install:
	UV_OFFLINE=0 uv sync --all-extras
setup:
	UV_OFFLINE=0 bash .engineering/setup.sh
fmt:
	uv run ruff check --fix --exit-zero $(FORMAT_PATHS)
	uv run ruff format $(FORMAT_PATHS)
lint:
	@SRC="$(SRC)" bash .engineering/scripts/cmd_check.sh lint
test:
	uv run pytest || test $$? -eq 5
check:
	@SRC="$(SRC)" bash .engineering/scripts/cmd_check.sh
engineering-test:
	uv run ruff check .engineering/engineering .engineering/tests
	uv run ruff format --check .engineering/engineering .engineering/tests
	uv run mypy .engineering/engineering
	uv run pytest .engineering/tests -o addopts="" -q
manifest:
	uv run --no-project --isolated --python 3.12 python .engineering/scripts/generate_template_manifest.py

# engineering:integration:begin
.PHONY: engineering-check engineering-evals engineering-evals-full
engineering-check:
	./engineering doctor
	./engineering maintainability
	uv run --no-project --isolated --python 3.12 python .engineering/evals/run_evals.py
engineering-evals:
	uv run --no-project --isolated --python 3.12 python .engineering/evals/run_evals.py
engineering-evals-full:
	uv run --no-project --isolated --python 3.12 python .engineering/evals/run_evals.py --full
# engineering:integration:end
