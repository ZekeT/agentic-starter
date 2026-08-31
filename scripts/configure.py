#!/usr/bin/env python3
"""
scripts/configure.py — apply model config to agent definitions and CLAUDE.md.

Usage:
    python scripts/configure.py                        # apply active config
    python scripts/configure.py --profile anthropic-budget  # switch profile
    python scripts/configure.py --show                 # print current config
    python scripts/configure.py --list                 # list available profiles

What this does:
    1. Reads config/models.json (active section or named profile).
    2. Patches .claude/agents/*.md frontmatter with resolved model strings.
    3. Updates the "Active Model Config" section in CLAUDE.md.

Why a script instead of manual edits:
    Agent files reference model tiers (planning/implement/fast), not hardcoded
    model strings. This keeps agent definitions stable across config changes —
    you only edit models.json, not every agent file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
MODELS_FILE = ROOT / "config" / "models.json"
AGENTS_DIR = ROOT / ".claude" / "agents"
CLAUDE_MD = ROOT / "CLAUDE.md"

# Maps agent filename → model tier
AGENT_TIER: dict[str, str] = {
    "developer.md": "implement",
    "code-reviewer.md": "review",
    "security-reviewer.md": "review",
    "scrum-master.md": "planning",
    "analyst.md": "planning",
    "pm.md": "planning",
    "architect.md": "planning",
    "qa-engineer.md": "fast",
    "devops.md": "fast",
}


def load_config(profile: str | None = None) -> dict:
    """Load and resolve the active model configuration."""
    raw = json.loads(MODELS_FILE.read_text())

    if profile:
        profiles = raw.get("profiles", {})
        if profile not in profiles:
            available = ", ".join(k for k in profiles if k != "_comment")
            print(f"Error: profile '{profile}' not found. Available: {available}")
            sys.exit(1)
        # Merge profile over base config
        cfg = {k: v for k, v in raw.items() if k not in ("profiles", "_comment")}
        cfg.update({k: v for k, v in profiles[profile].items() if k != "_comment"})
        return cfg

    return {k: v for k, v in raw.items() if k not in ("profiles", "_comment")}


def resolve_model(cfg: dict, tier: str) -> str:
    """Return the model string for a given tier."""
    return cfg["models"].get(tier, cfg["models"]["implement"])


def patch_agent_frontmatter(path: Path, model: str) -> None:
    """Replace the model: field in YAML frontmatter."""
    content = path.read_text()
    pattern = re.compile(r"^(model:\s*).*$", re.MULTILINE)
    if not pattern.search(content):
        print(f"  {path.name}: no frontmatter model field found, skipping")
        return
    patched = pattern.sub(f"model: {model}", content)
    if patched != content:
        path.write_text(patched)
        print(f"  {path.name}: model → {model}")
    else:
        print(f"  {path.name}: model already {model}")


def update_claude_md(cfg: dict) -> None:
    """Update the Active Model Config section in CLAUDE.md."""
    if not CLAUDE_MD.exists():
        return

    block_lines = [
        "## Active Model Config",
        "",
        "<!-- This section is auto-updated by scripts/configure.py — do not edit manually. -->",
        "<!-- Run `make configure-show` to see current assignments. -->",
        "",
        f"Provider: `{cfg['provider']}`",
        "",
        "| Tier | Model |",
        "|------|-------|",
    ]
    block_lines += [f"| {tier} | `{model}` |" for tier, model in cfg["models"].items()]

    new_block = "\n".join(block_lines)

    content = CLAUDE_MD.read_text()
    # Replace existing section if present, preserving the trailing `---` separator.
    pattern = re.compile(r"## Active Model Config.*?(?=\n## |\Z)", re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(new_block + "\n\n---\n", content)
    else:
        content = content.rstrip() + "\n\n---\n\n" + new_block + "\n"

    CLAUDE_MD.write_text(content)
    print("  CLAUDE.md: Active Model Config section updated")


def show_config(cfg: dict) -> None:
    """Pretty-print the active config."""
    print("\n=== Active Model Configuration ===")
    print(f"Provider : {cfg['provider']}")
    print("\nModel tiers:")
    for tier, model in cfg["models"].items():
        print(f"  {tier:<12} {model}")
    print()


def list_profiles() -> None:
    """List available profiles from models.json."""
    raw = json.loads(MODELS_FILE.read_text())
    profiles = raw.get("profiles", {})
    print("\nAvailable profiles:")
    for name, data in profiles.items():
        if name == "_comment":
            continue
        print(f"  {name:<25} {data.get('_comment', '')}")
    print()


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Configure model assignments for agents."
    )
    parser.add_argument(
        "--profile", "-p", help="Apply a named profile from models.json"
    )
    parser.add_argument(
        "--show", action="store_true", help="Show current config and exit"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available profiles and exit"
    )
    args = parser.parse_args()

    if args.list:
        list_profiles()
        return

    cfg = load_config(args.profile)

    if args.show:
        show_config(cfg)
        return

    if args.profile:
        # Persist the profile choice back to models.json active section
        raw = json.loads(MODELS_FILE.read_text())
        profile_data = raw["profiles"][args.profile]
        for key in ("provider", "models"):
            if key in profile_data:
                raw[key] = profile_data[key]
        MODELS_FILE.write_text(json.dumps(raw, indent=2) + "\n")
        print(f"\nProfile '{args.profile}' applied to config/models.json")

    print("\n=== Patching agent files ===")
    for agent_file in sorted(AGENTS_DIR.glob("*.md")):
        tier = AGENT_TIER.get(agent_file.name, "implement")
        patch_agent_frontmatter(agent_file, resolve_model(cfg, tier))

    print("\n=== Updating CLAUDE.md ===")
    update_claude_md(cfg)

    show_config(cfg)


if __name__ == "__main__":
    main()
