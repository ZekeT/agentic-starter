"""Compare source growth against the existing factory merge-base contract."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Config, safe_path
from .source import count_python, discover_sources, git


@dataclass(frozen=True)
class GrowthFinding:
    """Reviewable code-line evidence and threshold disposition."""

    path: str
    current: int
    previous: int | None
    status: str
    reason: str

    @property
    def growth(self) -> int | None:
        """Return net growth only when a comparison baseline exists."""
        return None if self.previous is None else self.current - self.previous


def classify(
    current: int, previous: int | None, config: Config, *, new: bool = False
) -> str:
    """Apply the configured strict size and inclusive substantial-growth limits."""
    if current > config.max_file_lines and (
        new
        or previous is not None
        and current - previous >= config.substantial_growth_lines
    ):
        return "FAIL"
    return "WARN" if current > config.warn_file_lines else "PASS"


def merge_base(root: Path, base: str | None) -> str:
    """Reuse the shipped shell helper without interpolating user input into code."""
    helper = Path(__file__).resolve().parents[1] / "scripts/lib/change.sh"
    env = dict(os.environ)
    if base is not None:
        env["HARNESS_BASE_BRANCH"] = base
    proc = subprocess.run(
        ["bash", "-c", '. "$1"; merge_base_of HEAD', "factory", str(helper)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    if proc.returncode or not proc.stdout.strip():
        raise ValueError(
            "Cannot resolve merge base; set --base or harness.baseBranch, or use --all for size-only inspection. "
            + proc.stderr.strip()
        )
    return proc.stdout.strip()


def check_growth(
    root: Path, config: Config, base: str | None = None, *, all_files: bool = False
) -> tuple[list[GrowthFinding], list[str]]:
    """Check changed files, tracking Git-detected renames and untracked additions."""
    sources, unsupported = discover_sources(root)
    baseline = None if all_files else merge_base(root, base)
    old_paths: set[str] = set()
    changed: set[str] = set()
    renames: dict[str, str] = {}
    if baseline:
        old_paths = set(
            git(root, "ls-tree", "-r", "--name-only", "-z", baseline)
            .decode(errors="surrogateescape")
            .split("\0")
        )
        tokens = (
            git(root, "diff", "--name-status", "-z", "--find-renames", baseline, "--")
            .decode(errors="surrogateescape")
            .split("\0")
        )
        index = 0
        while index < len(tokens) and tokens[index]:
            status, name = tokens[index : index + 2]
            index += 2
            if status.startswith("R"):
                destination = tokens[index]
                index += 1
                renames[destination] = name
                name = destination
            changed.add(name)
    findings = []
    for name in sources:
        if baseline and name not in changed and name in old_paths:
            continue
        reason = config.exceptions.get(name)
        try:
            current = count_python(safe_path(root, name).read_bytes()).code
            old_name = renames.get(name, name)
            previous = (
                count_python(git(root, "show", f"{baseline}:{old_name}")).code
                if baseline and old_name in old_paths
                else (0 if baseline else None)
            )
        except (SyntaxError, UnicodeError, ValueError) as exc:
            raise ValueError(f"Cannot analyze {name}: {exc}") from exc
        if reason:
            findings.append(GrowthFinding(name, current, previous, "EXEMPT", reason))
            continue
        status = classify(
            current, previous, config, new=bool(baseline and old_name not in old_paths)
        )
        reason = (
            "Decompose cohesive responsibilities or request a reviewed exception."
            if status == "FAIL"
            else "Review cohesion before further growth."
        )
        findings.append(GrowthFinding(name, current, previous, status, reason))
    return findings, unsupported
