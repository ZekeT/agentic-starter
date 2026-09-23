# Python application template. Adoption preserves the target's own check recipe.
MAKEFLAGS += --no-print-directory
export MAKEFLAGS
export UV_OFFLINE = 1
export UV_PYTHON_DOWNLOADS = never
SRC ?= src
FORMAT_PATHS = $(wildcard $(SRC) tests)

.PHONY: install setup fmt lint test check
install:
	UV_OFFLINE=0 uv sync --all-extras
setup:
	UV_OFFLINE=0 bash .engineering/setup.sh
fmt:
	@if [ -n "$(FORMAT_PATHS)" ]; then uv run ruff check --fix --exit-zero $(FORMAT_PATHS); fi
	@if [ -n "$(FORMAT_PATHS)" ]; then uv run ruff format $(FORMAT_PATHS); fi
lint:
	@SRC="$(SRC)" bash .engineering/scripts/cmd_check.sh lint
test:
	uv run pytest || test $$? -eq 5
check:
	@SRC="$(SRC)" bash .engineering/scripts/cmd_check.sh
# engineering:integration:begin
.PHONY: engineering-check
engineering-check:
	./engineering doctor
	./engineering maintainability
# engineering:integration:end
