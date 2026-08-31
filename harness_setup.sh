#!/usr/bin/env bash
# harness_setup.sh — bootstrap a new project from this template
# Run once after cloning: bash harness_setup.sh
# Verify an existing project without changing it: bash harness_setup.sh --check

set -e

# ── --check: verify an existing project, mutate nothing ──────────────────────
# The structural half of what the retired setup-base skill did. Assertions only:
# no file is created, copied, or edited on this path.
if [ "${1:-}" = "--check" ]; then
  fail=0
  warn=0
  ok()   { echo "  PASS  $1"; }
  bad()  { echo "  FAIL  $1"; fail=1; }
  soft() { echo "  WARN  $1"; warn=$((warn + 1)); }

  echo "=== Harness check — $(pwd) ==="
  echo ""

  echo "Structure"
  for d in openspec/specs openspec/changes/archive docs/decisions \
           .claude/hooks .claude/agents .claude/commands .claude/skills; do
    [ -d "$d" ] && ok "$d/" || bad "$d/ missing"
  done

  echo ""
  echo "Required files"
  for f in CLAUDE.md HARNESS.md REVIEW.md Makefile pyproject.toml \
           .env.template config/models.json .claude/settings.json; do
    [ -f "$f" ] && ok "$f" || bad "$f missing"
  done

  echo ""
  echo "Hooks"
  if [ -f .claude/settings.json ]; then
    python3 - <<'EOF' || fail=1
import json, pathlib, re, sys

cfg = json.loads(pathlib.Path(".claude/settings.json").read_text())
wired = set()
for events in cfg.get("hooks", {}).values():
    for matcher in events:
        for hook in matcher.get("hooks", []):
            m = re.search(r"\.claude/hooks/(\S+\.py)", hook.get("command", ""))
            if m:
                wired.add(m.group(1))
on_disk = {p.name for p in pathlib.Path(".claude/hooks").glob("*.py")}
bad = False
for name in sorted(wired - on_disk):
    print(f"  FAIL  {name} wired in settings.json but missing from disk")
    bad = True
for name in sorted(on_disk - wired):
    print(f"  FAIL  {name} on disk but never wired — dead code that looks alive")
    bad = True
for name in sorted(wired & on_disk):
    print(f"  PASS  {name}")
sys.exit(1 if bad else 0)
EOF
  else
    bad ".claude/settings.json missing — no hooks are wired"
  fi

  echo ""
  echo "Template manifest"
  if [ -f template-manifest.json ]; then
    if python3 -c "import json,sys; d=json.load(open('template-manifest.json')); sys.exit(0 if d.get('files') else 1)" 2>/dev/null; then
      ok "template-manifest.json valid ($(python3 -c "import json;print(len(json.load(open('template-manifest.json'))['files']))") files)"
    else
      bad "template-manifest.json is not valid JSON, or lists no files"
    fi
  else
    soft "template-manifest.json absent — setup-update has nothing to diff against"
  fi

  echo ""
  echo "Change loop"
  if [ -d .git ]; then ok "git repo"; else soft "no .git — worktree isolation needs git"; fi
  if command -v openspec >/dev/null 2>&1; then
    if openspec validate --all >/dev/null 2>&1; then
      ok "openspec validate --all"
    else
      bad "openspec validate --all fails — run it for the detail"
    fi
  else
    soft "openspec CLI not on PATH — the change loop needs it"
  fi

  echo ""
  if [ "$fail" -ne 0 ]; then
    echo "FAILED — fix the FAILs above. WARNs are safe to defer."
    exit 1
  fi
  echo "OK — structure, hooks, and manifest intact ($warn warning(s))."
  exit 0
fi

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
echo "  Already installed on this machine? Update instead (v6+ required):"
echo "    /plugin update superpowers@superpowers-marketplace"
echo ""
echo "  This installs globally to ~/.claude/ — do it once,"
echo "  and it works for all your projects."
echo

# 6. Verify make check works (no src yet, just confirm tooling)
echo "[6/7] Verifying toolchain..."
uv run black --version
uv run isort --version-number
uv run autoflake --version
uv run interrogate --version
uv run mypy --version
uv run pytest --version
# 7. OpenSpec — the change loop's document lifecycle.
# Warn only: every other part of the harness works without it.
echo "[7/7] Checking OpenSpec (Node CLI)..."
NODE_MIN="20.19.0"
if ! command -v node &> /dev/null; then
  echo "  WARN: node not found. OpenSpec needs Node >= $NODE_MIN."
  echo "        Install Node, then: npm install -g @fission-ai/openspec@latest"
elif [ "$(printf '%s\n' "$NODE_MIN" "$(node --version | tr -d v)" | sort -V | head -1)" != "$NODE_MIN" ]; then
  echo "  WARN: node $(node --version) is older than v$NODE_MIN — OpenSpec needs >= v$NODE_MIN."
elif ! command -v openspec &> /dev/null; then
  echo "  node $(node --version) OK, but the openspec CLI is missing. Install it:"
  echo "    npm install -g @fission-ai/openspec@latest"
  echo "    openspec init --tools claude"
else
  echo "  openspec $(openspec --version) on node $(node --version)"
  if [ ! -d openspec ]; then
    echo "  No openspec/ directory yet — initialise it: openspec init --tools claude"
  fi
fi
echo

# The archive ships one worked example so the artifact chain is readable before
# you write your own. Offer to drop it — a setup script that silently deletes
# things erodes exactly the trust the human gates exist to build.
if [ -t 0 ] && ls -d openspec/changes/archive/2026-* >/dev/null 2>&1; then
  echo ""
  echo "The archive ships one example change (the starter's own history):"
  for d in openspec/changes/archive/2026-*; do echo "  $d"; done
  printf "Remove it? [y/N] "
  read -r REPLY
  case "$REPLY" in
    [yY]*)
      if git rm -r -q openspec/changes/archive/2026-* 2>/dev/null; then
        echo "  Removed — commit the deletion when you make your first commit."
      else
        rm -rf openspec/changes/archive/2026-*
        echo "  Removed."
      fi
      # git rm drops the directory once it is empty; the loop still needs it.
      mkdir -p openspec/changes/archive && touch openspec/changes/archive/.gitkeep
      ;;
    *) echo "  Kept. Delete it whenever: git rm -r openspec/changes/archive/2026-*" ;;
  esac
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit pyproject.toml — set [project] name, description"
echo "  2. Create src/<your_package>/__init__.py"
echo "  3. Write docs/product.md — what this is, who it is for, non-goals"
echo "  4. In Claude Code, crystallize your first idea into a change:"
echo "       /crystallize \"<your idea>\""
echo "     then review the intent, review the proposal + specs + tasks,"
echo "     and run /dev-change <slug> <group>"
echo ""
echo "  Human gates: intent → spec+tasks → PR merge → archived spec diff"
echo ""
echo "Quick reference:"
echo "  make fmt    — format code"
echo "  make lint   — check code"
echo "  make test   — run tests"
echo "  make check  — all three (run before every commit)"
