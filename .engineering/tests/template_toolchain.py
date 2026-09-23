"""Offline external installers for public generated-project command tests."""

import os
import shutil
import sys
from pathlib import Path


def toolchain(directory: Path) -> dict[str, str]:
    """Fake network tools while running real Engineering, Git and Python checks."""
    directory.mkdir()
    git = shutil.which("git")
    assert git
    script = directory / "fixture-tool"
    script.write_text(
        f"#!{sys.executable}\n"
        + f"PYTHON = {sys.executable!r}\nGIT = {git!r}\n"
        + """import json
import os
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
args = sys.argv[1:]
if "TEMPLATE_CALLS" in os.environ:
    with Path(os.environ["TEMPLATE_CALLS"]).open("a") as stream:
        stream.write(json.dumps([name, *args]) + "\\n")
if name == "uv":
    if args[0] == "sync":
        sys.exit(int(os.environ.get("SYNC_STATUS", "0")))
    if "python" in args:
        os.execv(PYTHON, [PYTHON, *args[args.index("python") + 1:]])
    executable = str(Path(PYTHON).parent / args[1])
    os.execv(executable, [executable, *args[2:]])
elif name == "git":
    if args[0] == "clone":
        Path(args[-1]).mkdir()
        sys.exit(0)
    if "checkout" in args and Path.cwd().name == "source":
        Path("fixture-pin").write_text(args[-1])
        sys.exit(0)
    if args == ["rev-parse", "HEAD"] and Path("fixture-pin").exists():
        print(Path("fixture-pin").read_text())
        sys.exit(0)
    os.execv(GIT, [GIT, *args])
elif name == "npx":
    for skill in args[args.index("--skill") + 1:args.index("--agent")]:
        path = Path(".claude/skills") / skill / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("Fixture installed skill: " + skill)
elif name == "npm":
    version = json.loads(Path("package.json").read_text())["dependencies"]["@nanonets/graft"]
    path = Path("node_modules/@nanonets/graft/package.json")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"version": version}))
elif name == "node":
    print("v22.12.0" if args == ["--version"] else "Fixture Graft skill")
else:
    sys.exit(99)
"""
    )
    script.chmod(0o755)
    for name in ("uv", "git", "npx", "npm", "node"):
        (directory / name).symlink_to(script)
    return {
        **os.environ,
        "PATH": f"{directory}:{os.environ['PATH']}",
        "TEMPLATE_CALLS": str(directory / "calls.jsonl"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
