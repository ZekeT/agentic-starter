"""Plan dependencies offline; fetch and apply only through explicit choices."""

import json
import re
import tempfile
from pathlib import Path
from typing import Any

from . import graft
from .ownership import digest, encoded, observe, read_bytes
from .registry import REGISTRY, STATE, installed_status, registry, state
from .skill_install import run, stage
from .transaction import write_files


def status(root: Path) -> int:
    """Report installed-versus-pinned state without querying upstream."""
    data, evidence = registry(root), state(root)["dependencies"]
    print(
        "Dependency             Desired                                   Installed                                 Status"
    )
    for row in data["dependency"]:
        installed, health = installed_status(root, row, evidence)
        print(f"{row['id']:<22} {row['version']:<41} {installed:<41} {health}")
    return 0


def replace_pin(raw: bytes, name: str, pin: str) -> bytes:
    """Edit only a selected registry entry, preserving comments and other pins."""
    parts = raw.decode().split("[[dependency]]")
    matches = 0
    for index, part in enumerate(parts):
        if re.search(rf'^id\s*=\s*"{re.escape(name)}"\s*$', part, re.MULTILINE):
            parts[index], count = re.subn(
                r'^version\s*=\s*"[^"\n]+"',
                f'version = "{pin}"',
                part,
                flags=re.MULTILINE,
            )
            matches += count
    if matches != 1:
        raise ValueError("deps.registry: cannot uniquely replace version")
    return "[[dependency]]".join(parts).encode()


def npm_stage(root: Path, directory: Path, row: dict[str, Any]) -> dict[str, bytes]:
    """Resolve an exact npm pin in isolation, then promote the complete installation."""
    directory.mkdir()
    original = json.loads(
        (read_bytes(root, f"{graft.PACKAGE}/package.json") or b"{}").decode()
    )
    if (
        not isinstance(original, dict)
        or any(
            original.get(key)
            for key in (
                "scripts",
                "devDependencies",
                "optionalDependencies",
                "peerDependencies",
            )
        )
        or not isinstance(original.get("dependencies", {}), dict)
        or set(original.get("dependencies", {})) - {row["source"]}
    ):
        raise ValueError(
            "deps.destination_modified: Graft package contains custom dependencies or scripts; reconcile before installation"
        )
    original.update(private=True, dependencies={row["source"]: row["version"]})
    (directory / "package.json").write_bytes(encoded(original))
    lock = read_bytes(root, f"{graft.PACKAGE}/package-lock.json")
    if (
        lock
        and json.loads(lock)
        .get("packages", {})
        .get("", {})
        .get("dependencies", {})
        .get(row["source"])
        == row["version"]
    ):
        (directory / "package-lock.json").write_bytes(lock)
        run(["npm", "ci", "--no-audit", "--no-fund"], directory)
    else:
        run(["npm", "install", "--no-audit", "--no-fund"], directory)
    return {
        f"{graft.PACKAGE}/{name}": (directory / name).read_bytes()
        for name in ("package.json", "package-lock.json")
    }


def operate(
    root: Path,
    operation: str,
    name: str | None,
    *,
    apply: bool,
    ref: str | None = None,
    check_remote: bool = False,
) -> int:
    """Stage all selected changes before replacing managed output scopes."""
    data, evidence = registry(root), state(root)
    rows = [
        dict(row)
        for row in data["dependency"]
        if row["id"] == name
        or name is None
        and (row["required"] or row["id"] in evidence["dependencies"])
    ]
    if not rows:
        raise ValueError(f"deps.id: unknown dependency {name}")
    if ref and (not name or operation != "update"):
        raise ValueError("deps.ref: use deps update NAME --ref IMMUTABLE_PIN")
    if check_remote and (apply or ref):
        raise ValueError(
            "deps.remote: discovery is plan-only; select a returned --ref explicitly"
        )
    registry_bytes = read_bytes(root, REGISTRY)
    assert registry_bytes is not None
    for row in rows:
        if ref:
            pattern = r"[0-9a-f]{40}" if row["kind"] == "skills" else r"\d+\.\d+\.\d+"
            if not re.fullmatch(pattern, ref):
                raise ValueError(
                    "deps.pin: require full commit SHA or exact npm version"
                )
            row["version"] = ref
            registry_bytes = replace_pin(registry_bytes, row["id"], ref)
        installed, health = installed_status(root, row, evidence["dependencies"])
        print(f"{row['id']}: {installed} → {row['version']} ({health})")
        if check_remote:
            command = (
                [
                    "git",
                    "ls-remote",
                    "https://github.com/" + row["source"] + ".git",
                    "HEAD",
                ]
                if row["kind"] == "skills"
                else ["npm", "view", row["source"], "version"]
            )
            print("Upstream candidate (network): " + run(command, root))
    print(
        "Apply installs from the network using pinned sources. Global installations are not managed."
    )
    print(
        "After apply: engineering doctor; make engineering-test; make engineering-evals."
    )
    if not apply:
        print("No files changed. Select --apply to install/update the displayed pins.")
        return 0
    selected = []
    for row in rows:
        _, health = installed_status(root, row, evidence["dependencies"])
        if health == "MODIFIED":
            raise ValueError(
                f"deps.destination_modified: {row['id']}; reconcile local edits first"
            )
        if health == "OK":
            continue
        if (
            operation == "install"
            and row["id"] in evidence["dependencies"]
            and health == "PIN DIFFERS"
        ):
            raise ValueError("deps.pin: installed version differs; use deps update")
        selected.append(row)
    if not selected:
        print("Already installed at desired pins.")
        return 0
    observed = {REGISTRY: observe(root, REGISTRY), STATE: observe(root, STATE)}
    for entry in evidence["dependencies"].values():
        for path in entry["outputs"]:
            observed[path] = observe(root, path)
    changes: dict[str, bytes | None] = {REGISTRY: registry_bytes}
    # Upstream package installation occurs in a disposable directory. Project writes
    # happen only after collision and concurrent-change checks have all passed.
    with tempfile.TemporaryDirectory(prefix="engineering-deps-") as temporary:
        temporary_path = Path(temporary)
        npm_pending = None
        for row in selected:
            directory = temporary_path / row["id"]
            directory.mkdir()
            if row["kind"] == "skills":
                outputs = stage(directory, row, data["skills_installer"])
            else:
                package_dir = directory / "package"
                outputs = npm_stage(root, package_dir, row)
                node = run(["node", "--version"], directory)
                if tuple(map(int, node.lstrip("v").split(".")[:2])) < (22, 12):
                    raise ValueError("deps.runtime: Node.js 22.12+ required")
                outputs[graft.SKILL] = graft.skill_text(
                    "node", package_dir / "node_modules/@nanonets/graft"
                ).encode()
                npm_pending = package_dir / "node_modules"
            old = evidence["dependencies"].get(row["id"], {}).get("outputs", {})
            for path, content in outputs.items():
                current = read_bytes(root, path)
                # npm metadata are shipped pins, and are validated independently.
                shipped = path in {
                    f"{graft.PACKAGE}/package.json",
                    f"{graft.PACKAGE}/package-lock.json",
                }
                if (
                    current is not None
                    and current != content
                    and path not in old
                    and not shipped
                ):
                    raise ValueError(
                        f"deps.destination_modified: {path}; no files changed"
                    )
                observed.setdefault(path, observe(root, path))
                changes[path] = content
            for path in old.keys() - outputs.keys():
                changes[path] = None
            evidence["dependencies"][row["id"]] = {
                "managed": True,
                "installed_version": row["version"],
                "installed_from": row["source"],
                "outputs": {path: digest(content) for path, content in outputs.items()},
            }
        if any(observe(root, path) != value for path, value in observed.items()):
            raise ValueError("deps.stale: inputs changed during installation; re-plan")
        changes[STATE] = encoded(evidence)
        if npm_pending:
            import shutil

            destination = root / graft.PACKAGE / "node_modules"
            backup = temporary_path / "previous-node-modules"
            if destination.is_symlink():
                raise ValueError(
                    "deps.symlink: node_modules must be a managed local directory"
                )
            # Move on the same filesystem where possible; shutil handles cross-device.
            if destination.exists():
                shutil.move(str(destination), backup)
            try:
                shutil.move(str(npm_pending), destination)
                write_files(root, changes)
            except (OSError, ValueError):
                if destination.exists():
                    shutil.rmtree(destination)
                if backup.exists():
                    shutil.move(str(backup), destination)
                raise
        else:
            write_files(root, changes)
    return 0
