# Source this file, then: run_quiet "label" command arg ...
# Each invocation owns a private temporary log and preserves command status.
run_quiet() (
  label=$1
  shift
  umask 077
  quiet_log=$(mktemp "${TMPDIR:-/tmp}/factory-check.XXXXXX") || return 1
  trap 'rm -f "$quiet_log"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  if "$@" >"$quiet_log" 2>&1; then
    printf '✓ %s\n' "$label"
    if [ "${VERBOSE:-0}" = 1 ]; then cat "$quiet_log"; fi
  else
    quiet_status=$?
    printf '✗ %s\n\n' "$label" >&2
    cat "$quiet_log" >&2
    exit "$quiet_status"
  fi
)
