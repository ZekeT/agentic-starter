#!/usr/bin/env bash
# Non-mutating source checks. Cache/test artifacts may still be generated.
set -e
. "$(cd "$(dirname "$0")" && pwd)/lib/run_quiet.sh"

CHECK_SRC=${SRC:-src}
CHECK_PATHS=()
[ ! -d "$CHECK_SRC" ] || CHECK_PATHS+=("$CHECK_SRC")
[ ! -d tests ] || CHECK_PATHS+=(tests)

format_check() {
  [ "${#CHECK_PATHS[@]}" -eq 0 ] || uv run ruff format --check "${CHECK_PATHS[@]}"
}
lint_check() {
  [ "${#CHECK_PATHS[@]}" -eq 0 ] || uv run ruff check "${CHECK_PATHS[@]}"
}
types_check() {
  if [ -d "$CHECK_SRC" ] && [ -n "$(find "$CHECK_SRC" -name '*.py' -print -quit)" ]; then
    uv run mypy "$CHECK_SRC"
  else
    printf '%s\n' 'No Python source files; type checking is not applicable.'
  fi
}
tests_check() {
  # Preserve the starter's existing no-tests-collected convention (pytest 5).
  local test_status=0
  uv run pytest || test_status=$?
  [ "$test_status" -eq 0 ] || [ "$test_status" -eq 5 ] || return "$test_status"
}

case "${1:-all}" in
  lint)
    run_quiet format format_check
    run_quiet lint lint_check
    run_quiet types types_check
    ;;
  all)
    run_quiet format format_check
    run_quiet lint lint_check
    run_quiet types types_check
    run_quiet tests tests_check
    run_quiet feature-docs python3 .harness/scripts/check_feature_docs.py "$CHECK_SRC"
    ;;
  *) printf 'Unknown check mode: %s\n' "$1" >&2; exit 2 ;;
esac
