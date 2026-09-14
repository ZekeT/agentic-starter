"""Inspect installed hook, command, eval and Git wiring without executing it."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .config import object_value, read_text, safe_path
from .eval_config import parse_fields

COMMANDS = ("dev-change", "review", "commit-push-pr", "archive-change", "spike")
HOOKS = {
    "pre_tool_dangerous.py": ("PreToolUse", {"Bash"}),
    "pre_tool_env_guard.py": ("PreToolUse", {"Bash", "Read", "Glob", "LS", "Grep"}),
    "post_tool_secrets.py": ("PostToolUse", {"Write", "Edit", "MultiEdit"}),
    "post_tool_lint.py": ("PostToolUse", {"Write", "Edit", "MultiEdit"}),
}


def external_tool(root: Path, name: str) -> str:
    """Resolve machine tooling while refusing executables inside the inspected project."""
    executable = shutil.which(name)
    if not executable or Path(executable).resolve().is_relative_to(root.resolve()):
        raise ValueError(
            f"Install {name} outside the inspected project and add it to PATH"
        )
    return executable


def check_hooks(root: Path) -> None:
    """Require active protection hooks for every supported tool matcher."""
    settings = object_value(
        json.loads(read_text(root, ".claude/settings.json")), "settings"
    )
    if settings.get("disableAllHooks", False) is not False:
        raise ValueError("disableAllHooks must be false or absent")
    events = object_value(settings.get("hooks"), "hooks")
    covered: dict[str, set[str]] = {name: set() for name in HOOKS}
    for event, groups in events.items():
        if not isinstance(groups, list):
            raise ValueError(f"{event} hook groups must be a list")
        for group in groups:
            group = object_value(group, "hook matcher")
            matcher, hooks = group.get("matcher", ""), group.get("hooks")
            if not isinstance(matcher, str) or not isinstance(hooks, list):
                raise ValueError("Hook matcher must be text and hooks must be a list")
            for hook in hooks:
                hook = object_value(hook, "hook")
                command = hook.get("command", "")
                if not isinstance(command, str):
                    raise ValueError("Hook command must be text")
                for name, (required_event, tools) in HOOKS.items():
                    # Preserve shell quoting: single quotes or an escaped dollar
                    # leave a literal variable name instead of the project path.
                    suffix = re.escape(f"/.claude/hooks/{name}")
                    expected = (
                        r'[ \t]*python3[ \t]+"\$CLAUDE_PROJECT_DIR'
                        rf'(?:"{suffix}|{suffix}")[ \t]*'
                    )
                    if (
                        hook.get("type") == "command"
                        and re.fullmatch(expected, command)
                        and event == required_event
                        and hook.get("async", False) is False
                    ):
                        covered[name].update(
                            tools
                            if matcher in {"", "*"}
                            else tools & set(matcher.split("|"))
                        )
    for name, (_, tools) in HOOKS.items():
        read_text(root, f".claude/hooks/{name}")
        if missing := tools - covered[name]:
            raise ValueError(
                f"{name}: missing active protection for {', '.join(sorted(missing))}"
            )


def has_preamble(content: str, script: str) -> bool:
    """Recognize a standalone shipped invocation, not arbitrary Markdown or shell.

    Accept bash/sh fences and standalone !`...` directives, with an optional
    $ARGUMENTS placeholder and trailing shell comment. Never execute the body.
    """
    content = re.sub(r"<!--.*?(?:-->|\Z)", "\n", content, flags=re.DOTALL)
    path = re.escape(script)
    invocation = (
        rf"bash[ \t]+(?:{path}|\"{path}\"|'{path}')"
        r"(?:[ \t]+\$ARGUMENTS)?[ \t]*(?:[ \t]#[^\n]*)?"
    )
    fence = re.compile(
        r"^(`{3,}|~{3,})([^\n]*)\n(.*?)^\1[ \t]*(?:\n|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for block in fence.finditer(content):
        if block[2].strip() in {"bash", "sh"} and re.fullmatch(
            invocation, block[3].strip()
        ):
            return True
    prose = fence.sub("\n", content)
    return any(
        re.fullmatch(invocation, directive)
        for directive in re.findall(r"^!`([^`\n]+)`[ \t]*$", prose, re.MULTILINE)
    )


def check_commands(root: Path) -> None:
    """Check shipped command preamble paths without running shell content."""
    makefile = read_text(root, "Makefile")
    for target in ("check", "evals"):
        if not re.search(rf"^{target}[ \t]*:", makefile, re.MULTILINE):
            raise ValueError(f"Makefile missing required {target} target")
    for command in COMMANDS:
        script = f".harness/scripts/cmd_{command.replace('-', '_')}.sh"
        content = read_text(root, f".claude/commands/{command}.md")
        read_text(root, script)
        if not has_preamble(content, script):
            raise ValueError(
                f"{command}: missing supported preamble: bash {script}; "
                "use a bash/sh fenced block or standalone !`...` directive"
            )
    status = object_value(
        json.loads(read_text(root, ".claude/settings.json")), "settings"
    ).get("statusLine")
    if (
        isinstance(status, dict)
        and status.get("command") == '"$CLAUDE_PROJECT_DIR"/.claude/statusline.sh'
    ):
        path = safe_path(root, ".claude/statusline.sh")
        if not path.is_file() or not path.stat().st_mode & 0o111:
            raise ValueError(".claude/statusline.sh must exist and be executable")


def check_git(root: Path) -> None:
    """Ask Git about ignore behavior using synthetic names, never secret bytes."""
    probes = [
        ".env",
        ".env.local",
        ".env.production",
        ".env.claude",
        "private.pem",
        "private.key",
    ]
    result = subprocess.run(
        [
            external_tool(root, "git"),
            "-C",
            str(root),
            "-c",
            "core.excludesFile=/dev/null",
            "check-ignore",
            "--no-index",
            "-z",
            "--stdin",
        ],
        input="\0".join([*probes, ".env.template"]) + "\0",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        env={
            "PATH": os.environ.get("PATH", os.defpath),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        },
    )
    if result.returncode not in {0, 1}:
        raise ValueError(
            "Git installation/repository unavailable; initialize or repair the repository"
        )
    ignored = set(result.stdout.split("\0"))
    if missing := set(probes) - ignored:
        raise ValueError(
            f"Missing Git ignore protections: {', '.join(sorted(missing))}"
        )
    if ".env.template" in ignored:
        raise ValueError(
            ".env.template must remain trackable; add !.env.template after broad ignore rules"
        )


def check_evals(root: Path) -> None:
    """Validate the runner's documented YAML subset without running case bodies."""
    read_text(root, ".harness/evals/run_evals.py")
    cases = sorted(safe_path(root, ".harness/evals/cases").glob("*.yaml"))
    if not cases:
        raise ValueError("No eval cases installed")
    identifiers: set[str] = set()
    for path in cases:
        content = read_text(root, path.relative_to(root).as_posix())
        fields = parse_fields(content, path.name)
        identifier = fields["id"]
        if identifier in identifiers:
            raise ValueError(f"{path.name}: require unique id")
        identifiers.add(identifier)
