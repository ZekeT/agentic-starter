"""Fetch pinned starter objects and attest consumer updates against their payload."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .adoption import template_manifest
from .distribution import payload_path
from .installation import MANIFEST_PATH, check_state
from .ownership import digest, json_object, read_bytes
from .source import git
from .verification_git import baseline_content
from .verification_inputs import files, source_path


# These objects cross the JSON plan/evidence boundary; manifest schemas are
# validated by the same distribution reader that installation uses.
def validate_source(value: Any) -> None:
    """Require a repository URL and immutable commit, with an optional tag guard."""
    if not isinstance(value, dict) or set(value) - {"tag"} != {"repository", "commit"}:
        raise ValueError("starter_source requires repository, commit and optional tag")
    repository, commit = value["repository"], value["commit"]
    if not isinstance(repository, str):
        raise ValueError("starter_source.repository must be a Git repository URL")
    url = urlsplit(repository)
    if (
        url.scheme not in {"https", "http", "ssh", "git"}
        or not url.hostname
        or not url.path
        or url.password is not None
        or (url.username is not None and url.scheme != "ssh")
        or url.query
        or url.fragment
        or any(char.isspace() or ord(char) < 32 for char in repository)
    ):
        raise ValueError(
            "starter_source.repository requires an https/http/ssh/git URL without "
            "password, query or fragment; local checkout paths are not sources"
        )
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(
            "starter_source.commit must be a full lowercase Git commit SHA"
        )
    if "tag" in value:
        tag = value["tag"]
        if not isinstance(tag, str) or not tag.startswith("refs/tags/"):
            raise ValueError("starter_source.tag must be a full refs/tags/ reference")
        # check-ref-format validates syntax only, without contacting a repository.
        git(Path.cwd(), "check-ref-format", tag)


def fetch_git(root: Path, *args: str) -> bytes:
    """Fetch without custom transports, credential prompts, hooks or Git aliases."""
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=yes",
    )
    options = ["-c", "protocol.allow=never", "-c", f"core.hooksPath={os.devnull}"]
    for protocol in ("https", "http", "ssh", "git"):
        options += ["-c", f"protocol.{protocol}.allow=always"]
    try:
        result = subprocess.run(
            ["git", *options, "-C", str(root), *args],
            env=environment,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        # Do not expose transport diagnostics that may contain credentials.
        raise ValueError(
            "Starter source could not be fetched or resolved; verification is INCOMPLETE"
        ) from error
    return result.stdout


def fetch_source(spec: dict[str, Any]) -> dict[str, Any]:
    """Read only fetched Git blobs; no checkout filters or source scripts run."""
    validate_source(spec)
    with tempfile.TemporaryDirectory(prefix="engineering-source-") as folder:
        root = Path(folder)
        fetch_git(root, "init", "--quiet", "--template=")
        fetch_git(
            root,
            "fetch",
            "--quiet",
            "--no-tags",
            "--no-recurse-submodules",
            "--",
            spec["repository"],
            spec.get("tag", spec["commit"]),
        )
        commit = fetch_git(root, "rev-parse", "FETCH_HEAD^{commit}").decode().strip()
        if commit != spec["commit"]:
            raise ValueError(
                "Starter source moved: fetched revision differs from pinned commit"
            )
        revision = fetch_git(root, "rev-parse", "FETCH_HEAD").decode().strip()
        for name, mode, raw in baseline_content(root, commit):
            target = source_path(root, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            target.chmod(0o755 if mode == "100755" else 0o644)
        manifest = template_manifest(root)
        for name, entry in manifest["files"].items():
            if entry["ownership"]["mode"] == "file" and bool(
                payload_path(root, name).stat().st_mode & 0o111
            ) != entry.get("executable", False):
                raise ValueError(
                    f"{name}: starter source executable mode disagrees with manifest"
                )
        return {
            **spec,
            "revision": revision,
            "manifest_sha256": digest(read_bytes(root, MANIFEST_PATH)),
            "manifest": manifest,
        }


def verify_update(checkout: Path, source: dict[str, Any], base: dict[str, Any]) -> None:
    """Compare the complete managed file distribution with fetched authority."""
    offered = source["manifest"]
    proposed = json_object(read_bytes(checkout, MANIFEST_PATH) or b"{}")
    # Updates retain the consumer's project metadata, outside starter ownership.
    if {k: v for k, v in proposed.items() if k != "project"} != {
        k: v for k, v in offered.items() if k != "project"
    }:
        raise ValueError(
            "Proposed manifest differs from pinned starter source manifest"
        )
    expected: dict[str, dict[str, Any] | None] = {
        name: {"sha256": entry["sha256"], "executable": entry.get("executable", False)}
        for name, entry in offered["files"].items()
        if entry["ownership"]["mode"] == "file"
    }
    for name, entry in base.items():
        if entry["ownership"]["mode"] == "file" and name not in offered["files"]:
            expected[name] = None
    observed = files(checkout, set(expected))
    if mismatched := [name for name in expected if observed[name] != expected[name]]:
        raise ValueError(
            f"Managed bytes, modes or removals differ from pinned starter source: {mismatched}"
        )
    check_state(checkout, offered)
