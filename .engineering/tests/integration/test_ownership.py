"""Exercise byte boundaries and the complete update decision table."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[3] / ".engineering"))
from engineering.ownership import (  # noqa: E402
    digest,
    merge_owned,
    owned_content,
    read_bytes,
    validate_ownership,
)
from engineering.updates import classify, legacy_baseline  # noqa: E402

SPEC = {"mode": "section", "marker": "rules"}
REGION = b"<!-- engineering:rules:begin -->\nold\n<!-- engineering:rules:end -->\n"


@pytest.mark.parametrize(
    "local,incoming,base,expected",
    [
        (b"a", b"a", b"a", "PRESERVE"),
        (b"a", b"b", b"a", "MERGE"),
        (b"b", b"a", b"a", "PRESERVE"),
        (b"b", b"c", b"a", "CONFLICT"),
        (b"b", b"b", b"a", "PRESERVE"),
        (None, b"a", b"a", "PRESERVE"),
        (None, b"b", b"a", "CONFLICT"),
        (None, b"a", None, "ADD"),
        (b"custom", b"a", None, "CONFLICT"),
        (b"", b"a", b"", "MERGE"),
    ],
)
def test_update_table(local, incoming, base, expected):
    assert classify(local, incoming, digest(base))[0] == expected


def test_section_surrounding_bytes_and_crlf():
    prefix, suffix = b"custom\r\n\xff\n", b"tail\r\n\x00"
    original = prefix + REGION + suffix
    incoming = REGION.replace(b"old", b"new")
    assert owned_content(original, "CLAUDE.md", SPEC) == REGION
    assert (
        merge_owned(original, incoming, "CLAUDE.md", SPEC) == prefix + incoming + suffix
    )


@pytest.mark.parametrize(
    "bad",
    [
        REGION + REGION,
        REGION.split(b"old")[0],
        REGION.replace(
            b"<!-- engineering:rules:begin -->\n",
            b"<!-- engineering:rules:begin -->text",
        ),
        REGION.replace(b":end -->", b":end -->extra"),
        REGION.replace(b":begin", b":wrong"),
        b"<!-- engineering:unknown:begin -->",
    ],
)
def test_malformed_regions_refuse(bad):
    with pytest.raises(ValueError, match="marker|region"):
        owned_content(bad, "CLAUDE.md", SPEC)


@pytest.mark.parametrize(
    "name", ["../outside", ".git/config", ".env", ".env.local", "/tmp/outside"]
)
def test_unsafe_reads_refuse(tmp_path, name):
    with pytest.raises(ValueError):
        read_bytes(tmp_path, name)


@pytest.mark.parametrize("kind", ["fifo", "directory", "symlink"])
def test_nonregular_input_refuses(tmp_path, kind):
    import os

    path = tmp_path / "input"
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError):
        read_bytes(tmp_path, "input")


@pytest.mark.parametrize(
    "name",
    [
        ".engineering/state/install.json",
        ".engineering/manifest.json",
        "src/main.py",
        "docs/product.md",
        ".github/workflows/ci.yml",
    ],
)
def test_metadata_and_project_ownership_refuse(name):
    with pytest.raises(ValueError):
        validate_ownership(name, {"mode": "file"})


def test_historical_fingerprint_requires_evidence():
    assert legacy_baseline(
        b"old", {"sha256": digest(b"new"), "previous": [digest(b"old")]}
    ) == digest(b"old")
    assert legacy_baseline(b"unknown", {"sha256": digest(b"new")}) is None


@pytest.mark.parametrize(
    "bad",
    [
        b"# engineering:rules:begin\nlocal# engineering:rules:end\n",
        b"# engineering:rules:begin\rjunk\nlocal\n# engineering:rules:end\n",
        b"# engineering:rules:begin\nlocal\n# engineering:rules:end\rjunk\n",
    ],
)
def test_markers_must_occupy_complete_lines(bad):
    with pytest.raises(ValueError, match="marker|region"):
        owned_content(bad, "Makefile", SPEC)


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_complete_lf_and_crlf_marker_lines(newline):
    region = newline.join(
        [b"# engineering:rules:begin", b"owned", b"# engineering:rules:end", b""]
    )
    content = b"project prefix\n" + region + b"project suffix\n"
    assert owned_content(content, "Makefile", SPEC) == region
