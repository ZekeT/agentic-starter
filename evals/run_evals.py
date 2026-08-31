#!/usr/bin/env python3
"""Run the harness evals.

This repo *is* agent configuration, so the things most likely to regress are
prose: CLAUDE.md's rules, a skill's frontmatter, a command's shell preamble.
`tests/` covers the Python scripts; this covers everything that steers a model.

Two kinds of case (see evals/README.md):

  static  — assert something about the repo. Fast, free, deterministic.
  prompt  — run `claude -p` and assert on the reply. Costs tokens, needs auth.

    python evals/run_evals.py            # static only (CI default)
    python evals/run_evals.py --full     # + prompt cases
    python evals/run_evals.py --only 003 # single case by id prefix

Stdlib-only on purpose: this must run in CI without installing the project.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).parent.parent
CASES_DIR = Path(__file__).parent / "cases"
PROMPT_TIMEOUT = 180

GREEN, RED, YELLOW, DIM, BOLD, RESET = (
    "\033[92m",
    "\033[91m",
    "\033[93m",
    "\033[2m",
    "\033[1m",
    "\033[0m",
)


@dataclass
class Case:
    """One eval case parsed from a YAML-ish file in cases/."""

    path: Path
    id: str
    kind: str
    why: str = ""
    shell: str = ""
    prompt: str = ""
    expect: list[str] = field(default_factory=list)
    reject: list[str] = field(default_factory=list)


def parse_case(path: Path) -> Case:
    """Parse a case file.

    Hand-rolled rather than using PyYAML so the runner stays stdlib-only and
    works in CI before `uv sync`. Supports exactly the subset the cases use:
    `key: value`, `key: >` folded scalars, and `key: |` literal blocks.

    Args:
        path: The case file to parse.

    Returns:
        The parsed Case.

    Raises:
        ValueError: If required keys are missing.
    """
    fields: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    mode = ""

    for raw in path.read_text().splitlines():
        header = re.match(r"^([a-z_]+):\s*(.*)$", raw)
        # A new key only starts at column 0; indented lines belong to the block.
        if header and not raw.startswith((" ", "\t")):
            if key:
                fields[key] = "\n".join(buf).rstrip()
            key, rest = header.group(1), header.group(2)
            buf, mode = [], rest.strip()
            if mode not in ("|", ">"):
                buf = [rest]
                fields[key] = rest
                key, buf = None, []
            continue
        if key is not None:
            buf.append(raw[2:] if raw.startswith("  ") else raw)
    if key:
        fields[key] = "\n".join(buf).rstrip()

    for required in ("id", "kind", "why"):
        if not fields.get(required):
            raise ValueError(f"{path.name}: missing required key '{required}'")

    return Case(
        path=path,
        id=fields["id"],
        kind=fields["kind"],
        why=" ".join(fields.get("why", "").split()),
        shell=fields.get("shell", ""),
        prompt=fields.get("prompt", ""),
        expect=[s for s in fields.get("expect", "").splitlines() if s.strip()],
        reject=[s for s in fields.get("reject", "").splitlines() if s.strip()],
    )


def run_static(case: Case) -> tuple[bool, str]:
    """Run a static case's shell script from the repo root."""
    proc = subprocess.run(
        ["bash", "-c", case.shell],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, out


def run_prompt(case: Case) -> tuple[bool, str]:
    """Run a prompt case through `claude -p` and check expect/reject strings."""
    try:
        proc = subprocess.run(
            ["claude", "-p", case.prompt],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=PROMPT_TIMEOUT,
        )
    except FileNotFoundError:
        return False, "`claude` not on PATH — cannot run prompt cases"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {PROMPT_TIMEOUT}s"

    reply = (proc.stdout or "").strip()
    if not reply:
        return False, f"empty reply (exit {proc.returncode}): {proc.stderr[:200]}"

    low = reply.lower()
    problems = [f"missing expected: {s!r}" for s in case.expect if s.lower() not in low]
    problems += [f"found rejected: {s!r}" for s in case.reject if s.lower() in low]
    if problems:
        return False, "\n".join(problems) + f"\n--- reply ---\n{reply[:600]}"
    return True, ""


def main() -> int:
    """Run the selected cases and report. Returns a process exit code."""
    ap = argparse.ArgumentParser(description="Run harness evals.")
    ap.add_argument("--full", action="store_true", help="include prompt cases")
    ap.add_argument("--only", help="run cases whose filename starts with this")
    args = ap.parse_args()

    files = sorted(CASES_DIR.glob("*.yaml"))
    if args.only:
        files = [f for f in files if f.name.startswith(args.only)]
    if not files:
        print("No cases found.")
        return 1

    passed: list[Case] = []
    failed: list[tuple[Case, str]] = []
    skipped: list[Case] = []

    for f in files:
        case = parse_case(f)
        if case.kind == "prompt" and not args.full:
            skipped.append(case)
            continue

        ok, detail = (
            run_static(case) if case.kind == "static" else run_prompt(case)
        )
        if ok:
            passed.append(case)
            print(f"  {GREEN}PASS{RESET}  {case.id}")
        else:
            failed.append((case, detail))
            print(f"  {RED}FAIL{RESET}  {case.id}")
            for line in detail.splitlines():
                print(f"        {DIM}{line}{RESET}")

    print()
    if failed:
        print(f"{BOLD}Failures — what each one guards against:{RESET}")
        for case, _ in failed:
            print(f"  {RED}{case.id}{RESET}\n      {DIM}{case.why}{RESET}")
        print()

    total = len(passed) + len(failed)
    summary = f"{len(passed)}/{total} passed"
    if skipped:
        summary += f", {len(skipped)} prompt case(s) skipped (use --full)"
    print(f"{BOLD}{summary}{RESET}")
    if skipped and not failed:
        print(f"{YELLOW}Static cases only — prompt cases test whether the "
              f"instructions actually steer the model.{RESET}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
