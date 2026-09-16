"""Revalidate explicit lifecycle plans and report recoverable application failures."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import doctor
from .doctor_wiring import external_tool
from .ownership import observe


@dataclass(frozen=True)
class Action:
    """One visible disposition; proposed bytes exist only for actual mutations."""

    path: str
    kind: str
    reason: str
    content: bytes | None = None
    executable: bool = False


@dataclass
class Plan:
    """Observed inputs and immutable proposed actions, with no on-disk workflow state."""

    template: Path
    target: Path
    operation: str
    baseline: str | None
    actions: list[Action] = field(default_factory=list)
    detections: list[str] = field(default_factory=list)
    observed: dict[str, str | None] = field(default_factory=dict)
    directories: tuple[str, ...] = ()

    @property
    def conflicts(self) -> list[Action]:
        """Return every unresolved conflict before any mutation."""
        return [action for action in self.actions if action.kind == "CONFLICT"]


def git(root: Path, *args: str) -> str:
    """Use bounded Git plumbing without executing hooks or project commands."""
    result = subprocess.run(
        [
            external_tool(root, "git"),
            "-C",
            str(root),
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git repository unavailable")
    return result.stdout.strip()


def baseline(root: Path) -> str | None:
    """Read an optional recovery commit; planning supports uncommitted projects."""
    try:
        return git(root, "rev-parse", "--verify", "HEAD")
    except ValueError:
        return None


def show_plan(plan: Plan) -> None:
    """Print detections, all dispositions, and explicit follow-up requirements."""
    print(f"{plan.operation}: {plan.template} → {plan.target}")
    for finding in plan.detections:
        print(f"Inspection: {finding}")
    for action in plan.actions:
        print(f"{action.kind} {action.path}: {action.reason}")
    print("Apply is explicit (--apply); requires a clean committed target.")
    print(
        "Doctor runs offline after apply. Install managed dependencies separately; then run graft check and applicable evals."
    )


def apply_plan(plan: Plan) -> int:
    """Refuse stale/dirty/conflicted plans before writes; never claim partial success."""
    from .adoption import plan_installation

    if plan.conflicts:
        raise ValueError("Unresolved conflicts; no files written")
    if plan.baseline is None or git(plan.target, "rev-parse", "--show-toplevel") != str(
        plan.target
    ):
        raise ValueError("Apply requires the root of a clean committed Git target")
    if git(plan.target, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError(
            "Dirty target: commit or move changes before apply; no files written"
        )
    if baseline(plan.target) != plan.baseline:
        raise ValueError("Recovery commit changed; re-plan before apply")
    fresh = plan_installation(plan.template, plan.target, plan.operation)
    if fresh != plan:
        raise ValueError(
            "Observed inputs or proposed actions changed; re-plan; no files written"
        )
    for name, expected in plan.observed.items():
        if observe(plan.target, name) != expected:
            raise ValueError(f"Changed input {name}; no files written")
    from .transaction import write_files

    changes = {
        action.path: action.content
        for action in plan.actions
        if action.content is not None or action.kind == "REMOVE_SAFE"
    }
    executables = {action.path for action in plan.actions if action.executable}

    def validate() -> None:
        problems = [
            f
            for f in doctor.diagnose(plan.target)
            if f.severity == "ERROR" and f.code != "dependency"
        ]
        if problems:
            raise ValueError("Post-apply structural doctor failed: " + str(problems))

    try:
        write_files(plan.target, changes, executables=executables, validate=validate)
    except ValueError as exc:
        print(f"FAIL: {exc}\nRecovery commit: {plan.baseline}")
        print(
            "Inspect git status; restore affected tracked paths from that commit if rollback was incomplete."
        )
        return 1
    print(f"Applied; changes remain uncommitted. Recovery commit: {plan.baseline}")
    print(
        "Next: engineering deps install --apply; engineering doctor; project make check; human review."
    )
    return 0
