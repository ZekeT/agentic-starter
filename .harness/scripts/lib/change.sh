# Shared helpers for the /dev-change, /review, /commit-push-pr, /archive-change
# and /spike preambles.
#
# Sourced, never executed. Every function is POSIX sh and BSD/GNU portable:
# these run on macOS and in CI, and the two disagree silently on sed dialect.
# Use `sed -E`, never a GNU-only escape.

die() {
  echo "ERROR: $1" >&2
  shift
  for line in "$@"; do echo "$line" >&2; done
  exit 1
}

# Active (non-archived) change slugs, for error messages that tell you what you
# could have typed instead.
list_active_changes() {
  openspec list 2>/dev/null || ls -1 openspec/changes 2>/dev/null | grep -v '^archive$' || true
}

# feat/<slug>-g<N> → slug. Empty for any other branch shape, which callers
# treat as "not a change branch" rather than an error.
slug_from_branch() {
  echo "$1" | sed -nE 's|^feat/(.*)-g[0-9]+$|\1|p'
}

group_from_branch() {
  echo "$1" | sed -nE 's|^feat/.*-g([0-9]+)$|\1|p'
}

# The branch this work merges into. Not every team merges to main, so it is
# resolved rather than assumed, first hit winning:
#   1. HARNESS_BASE_BRANCH            — one invocation (what `--base` sets)
#   2. git config harness.baseBranch  — the project's (or the user's) default
#   3. origin/HEAD                    — whatever the remote calls its trunk
#   4. main
# Sets BASE_BRANCH and BASE_BRANCH_SOURCE; the source is worth printing, because
# a PR opened against the wrong trunk is expensive to notice late.
resolve_base_branch() {
  if [ -n "${HARNESS_BASE_BRANCH:-}" ]; then
    BASE_BRANCH="$HARNESS_BASE_BRANCH"
    BASE_BRANCH_SOURCE="--base"
  elif BASE_BRANCH=$(git config --get harness.baseBranch) && [ -n "$BASE_BRANCH" ]; then
    BASE_BRANCH_SOURCE="git config harness.baseBranch"
  elif BASE_BRANCH=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed -E 's|^origin/||') && [ -n "$BASE_BRANCH" ]; then
    BASE_BRANCH_SOURCE="origin/HEAD"
  else
    BASE_BRANCH="main"
    BASE_BRANCH_SOURCE="fallback"
  fi
}

base_branch() {
  resolve_base_branch
  echo "$BASE_BRANCH"
}

# The base as something git can resolve. `origin/<base>` is preferred over the
# local branch on purpose: the local one is often days stale (nobody pulls a
# trunk they never check out), and a stale base makes every diff show work that
# already merged. The remote ref is also the one the forge computes the PR's
# merge base against, so the diff you review matches the diff GitHub shows.
base_ref() {
  b=$(base_branch)
  if git rev-parse --verify --quiet "refs/remotes/origin/$b" >/dev/null; then
    echo "origin/$b"
  elif git rev-parse --verify --quiet "refs/heads/$b" >/dev/null; then
    echo "$b"
  else
    echo "$b"
  fi
}

# The commit a branch diverged from the base at. Diffing against this instead of
# the base tip is what stops a moved trunk showing up inverted as noise.
merge_base_of() {
  git merge-base "$(base_ref)" "$1"
}

# Every `## N.` heading in tasks.md with its checkbox counts.
task_group_summary() {
  awk '
    /^##[[:space:]]+[0-9]+\./ {
      if (n != "") printf "  group %-3s %-40s %d/%d done\n", n, title, done, total
      match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
      title = $0; sub(/^##[[:space:]]+[0-9]+\.[[:space:]]*/, "", title)
      done = 0; total = 0; next
    }
    /^[[:space:]]*-[[:space:]]*\[[ xX]\]/ { total++; if ($0 ~ /\[[xX]\]/) done++ }
    END { if (n != "") printf "  group %-3s %-40s %d/%d done\n", n, title, done, total }
  ' "$1"
}

# Lowest-numbered group that still has unchecked work. Empty when all are done.
first_unfinished_group() {
  awk '
    /^##[[:space:]]+[0-9]+\./ {
      if (n != "" && done < total) { print n; found = 1; exit }
      match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
      done = 0; total = 0; next
    }
    /^[[:space:]]*-[[:space:]]*\[[ xX]\]/ { total++; if ($0 ~ /\[[xX]\]/) done++ }
    END { if (!found && n != "" && done < total) print n }
  ' "$1"
}

# The body of one `## N.` group, headings and checkboxes included.
task_group_body() {
  awk -v g="$2" '
    /^##[[:space:]]+[0-9]+\./ {
      match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
      inblock = (n == g)
    }
    inblock
  ' "$1"
}

# Only the still-unchecked lines of one group.
unchecked_in_group() {
  awk -v g="$2" '
    /^##[[:space:]]+[0-9]+\./ {
      match($0, /^##[[:space:]]+[0-9]+/); n = substr($0, RSTART+2, RLENGTH-2); gsub(/[[:space:]]/, "", n)
      inblock = (n == g)
    }
    inblock && /^[[:space:]]*-[[:space:]]*\[[[:space:]]\]/
  ' "$1"
}
