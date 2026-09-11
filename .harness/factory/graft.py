"""Bound the pinned upstream CLI to application navigation and read-only queries."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from .config import object_value, safe_path

PACKAGE = ".harness/graft"
SKILL = ".claude/skills/graft/SKILL.md"
IGNORES = (
    "/graft/",
    "/.graft/",
    "/.harness/graft/node_modules/",
    "/.claude/skills/graft/",
)
QUERIES = {"ask", "grep", "skeleton", "callers", "map", "blast"}


def validate_query(command: str, extra: list[str]) -> None:
    """Allow retrieval options but never an alternate repository or model call."""
    parser = argparse.ArgumentParser(prog=f"graft {command}", allow_abbrev=False)
    if command in {"ask", "grep", "skeleton", "callers"}:
        parser.add_argument("query")
    flags = {
        "ask": ["--source", "--full"],
        "grep": ["--fixed", "-i", "--ignore-case", "--json"],
        "skeleton": ["--json"],
        "callers": ["--json"],
        "map": ["--json"],
        "blast": [],
    }
    values = {
        "ask": ["--in", "-n", "--limit"],
        "grep": ["--in"],
        "skeleton": [],
        "callers": ["--in", "--direction", "--depth", "-d"],
        "map": ["--max-dirs"],
        "blast": ["--base", "--depth", "-d", "--format"],
    }
    for flag in ["--no-refresh", *flags[command]]:
        parser.add_argument(flag, action="store_true")
    for flag in values[command]:
        parser.add_argument(flag)
    parser.parse_args(extra)


def application_roots(root: Path) -> list[str]:
    """Read explicit application inputs; never infer scope from all repository code."""
    manifest = object_value(
        json.loads(safe_path(root, ".harness/template-manifest.json").read_text()),
        "manifest",
    )
    if (
        type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
    ):
        raise ValueError("Unsupported manifest schema_version")
    project = object_value(manifest.get("project", {}), "project")
    navigation = object_value(project.get("navigation", {}), "project.navigation")
    if set(navigation) - {"application_roots"}:
        raise ValueError("Unknown navigation setting; use application_roots")
    roots = navigation.get("application_roots", [])
    if not isinstance(roots, list) or any(not isinstance(p, str) for p in roots):
        raise ValueError("navigation.application_roots must be a list of directories")
    for name in roots:
        path = safe_path(root, name)
        if name == "." or any(
            part.startswith(".")
            or part in {"factory", "harness", "node_modules", "graft"}
            for part in Path(name).parts
        ):
            raise ValueError(f"Select application directories, not tooling: {name}")
        if not path.is_dir():
            raise ValueError(f"Application directory missing: {name}")
        for current, directories, _ in os.walk(path, followlinks=False):
            for directory in directories:
                if directory in {"factory", "harness"}:
                    relative = (Path(current) / directory).relative_to(root)
                    raise ValueError(
                        f"Application root {name} contains tooling directory {relative}; "
                        "select narrower project.navigation.application_roots"
                    )
            directories[:] = [
                d
                for d in directories
                if not d.startswith(".")
                and d != "node_modules"
                and not (Path(current) / d).is_symlink()
            ]
    return sorted(set(roots))


def runtime(root: Path) -> tuple[str, Path]:
    """Reject a missing runtime or incompatible installation before execution."""
    node = shutil.which("node")
    if not node:
        raise ValueError(
            "Node.js 22.12+ required; install Node and run make graft-install"
        )
    version = subprocess.run(
        [node, "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if tuple(int(n) for n in version.lstrip("v").split(".")[:2]) < (22, 12):
        raise ValueError(f"Node.js 22.12+ required; found {version}")
    package = safe_path(root, PACKAGE)
    expected = json.loads((package / "package.json").read_text())["dependencies"][
        "@nanonets/graft"
    ]
    installed = package / "node_modules/@nanonets/graft"
    if not (installed / "package.json").is_file():
        raise ValueError("Graft missing; run make graft-install")
    actual = json.loads((installed / "package.json").read_text())["version"]
    if actual != expected:
        raise ValueError(
            f"Graft {expected} required; found {actual}; run make graft-install"
        )
    return node, installed


def environment(*, deep: bool = False) -> dict[str, str]:
    """Keep graph processing structural and reviewer queries non-refreshing."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GRAFT_")}
    if deep:
        for key in ("GRAFT_API_KEY", "GRAFT_PROVIDER", "GRAFT_BASE_URL", "GRAFT_MODEL"):
            if key in os.environ:
                env[key] = os.environ[key]
    env.update(
        DOTENV_CONFIG_PATH=os.devnull,
        DO_NOT_TRACK="1",
        GRAFT_NO_REFRESH="1",
        GRAFT_REFRESH="hash",
        GRAFT_NO_GITIGNORE="1",
        GRAFT_NO_IGNORE="1",
    )
    env.pop("DOTENV_KEY", None)
    return env


def skill_text(node: str, package: Path) -> str:
    """Read the release's unchanged generated skill without running graft init."""
    module = (package / "dist/claude/skill-template.js").as_uri()
    script = f"import {{skillTemplate}} from {json.dumps(module)}; process.stdout.write(skillTemplate());"
    return subprocess.run(
        [node, "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
        env=environment(),
    ).stdout


def install_skill(root: Path, *, apply: bool) -> int:
    """Preview or install only upstream skill bytes; preserve customized files."""
    node, package = runtime(root)
    content = skill_text(node, package)
    path = safe_path(root, SKILL)
    if path.exists() and path.read_text() != content:
        raise ValueError(f"Customized {SKILL}; reconcile before installing")
    action = "KEEP" if path.exists() else "ADD"
    print(f"{action} {SKILL} (unchanged upstream skill)")
    ignore = safe_path(root, ".gitignore")
    prior = ignore.read_text() if ignore.exists() else ""
    missing = [line for line in IGNORES if line not in prior.splitlines()]
    if missing:
        print(f"APPEND .gitignore: {', '.join(missing)}")
    print(
        "No hooks, statusline, MCP, instruction files or global agent configuration changes."
    )
    if apply and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    if apply and missing:
        gap = "" if not prior or prior.endswith("\n") else "\n"
        ignore.write_text(prior + gap + "\n".join(missing) + "\n")
    return 0


def check_structure(root: Path, node: str, package: Path) -> int:
    """Apply the structural gate to upstream JSON without discarding enrichment."""
    result = subprocess.run(
        [node, str(package / "dist/cli.js"), "check", "--json"],
        cwd=root,
        env=environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise ValueError(f"Graft check failed ({result.returncode}): {result.stderr}")
    try:
        report = object_value(json.loads(result.stdout), "Graft check report")
    except ValueError as exc:
        raise ValueError(f"Invalid Graft check report: {result.stderr or exc}") from exc
    graph = object_value(report.get("graph"), "Graft wiring check")
    context = object_value(report.get("context"), "Graft deep check")
    for layer in (graph, context):
        if any(type(layer.get(key)) is not bool for key in ("ok", "missing")):
            raise ValueError("Invalid Graft check status")
    for key in ("added", "removed", "changed", "stale"):
        values = graph.get(key)
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError(f"Invalid Graft wiring check: {key}")
    drift = any(graph[key] for key in ("added", "removed", "changed"))
    if graph["missing"] or graph["ok"] != (not drift and not graph["stale"]):
        raise ValueError("Missing or inconsistent Graft wiring check")
    upstream_failed = not graph["ok"] or (not context["missing"] and not context["ok"])
    if result.returncode != int(upstream_failed):
        raise ValueError(f"Graft check exit disagrees with its report: {result.stderr}")
    print(f"graph check: {'STALE' if drift else 'OK'} (structural)")
    for key in ("added", "removed", "changed"):
        for identifier in graph[key]:
            print(f"  {key}: {identifier}")
    if drift:
        print("Implementer must run graft build.")
    if graph["stale"]:
        print(
            f"Optional enrichment: {len(graph['stale'])} stale summaries (non-blocking)."
        )
    if not context["missing"] and not context["ok"]:
        print("Optional deep content is stale (non-blocking).")
    if graph["stale"] or (not context["missing"] and not context["ok"]):
        print("Use source for current behavior; graft build --deep is optional.")
    return int(drift)


def run(root: Path, args: list[str]) -> int:
    """Expose bounded upstream commands; structural preparation is implementer-owned."""
    if any(arg.startswith("dotenv_config_") for arg in args):
        raise ValueError("dotenv CLI overrides are disabled for factory navigation")
    if args in (["install-skill"], ["install-skill", "--apply"]):
        return install_skill(root, apply="--apply" in args)
    if not args or args[0] not in QUERIES | {"build", "check", "version"}:
        raise ValueError(
            "Use graft build, check, ask, grep, skeleton, callers, map, blast, version or install-skill"
        )
    command, *extra = args
    if command in QUERIES:
        validate_query(command, extra)
    node, package = runtime(root)
    if command == "version":
        print(json.loads((package / "package.json").read_text())["version"])
        return 0
    roots = application_roots(root)
    if not roots:
        print("not applicable: no application sources configured")
        return 0 if command in {"build", "check"} else 1
    # Scope/output overrides would bypass the factory's application boundary.
    forbidden = {
        "--dir",
        "--only-dir",
        "--include-dir",
        "--follow-submodules",
        "--follow-nested-repos",
    }
    if any(arg.split("=", 1)[0] in forbidden for arg in extra):
        raise ValueError(
            "Configure project.navigation.application_roots; scope overrides are unsupported"
        )
    if (
        command in {"build", "check"}
        and extra
        and not (command == "build" and extra == ["--deep"])
    ):
        raise ValueError(
            f"graft {command} takes no extra arguments in the factory gate"
        )
    if command != "build":
        path = safe_path(root, "graft/.graph/wiring.json")
        if not path.is_file():
            raise ValueError(
                "Application graph missing; implementer must run graft build"
            )
    if command == "check":
        return check_structure(root, node, package)
    if command == "build":
        for name in roots:
            extra.extend(["--only-dir", name])
        extra.extend(["--no-follow-submodules", "--no-follow-nested-repos"])
    return subprocess.run(
        [node, str(package / "dist/cli.js"), command, *extra],
        cwd=root,
        env=environment(deep=command == "build" and "--deep" in extra),
        check=False,
    ).returncode
