"""Safe Git source discovery and Python physical/code-line accounting."""

import ast
import io
import subprocess
import tokenize
from dataclasses import dataclass
from pathlib import Path

from .config import safe_path

EXCLUDED = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "vendor",
    "vendored",
    ".codemap",
}
OTHER_SOURCE = {
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".sh",
    ".rb",
}


@dataclass(frozen=True)
class LineCounts:
    """Physical lines and physical lines containing executable or data tokens."""

    physical: int
    code: int


def git(root: Path, *args: str) -> bytes:
    """Run Git read-only plumbing, retaining failures as diagnostics."""
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if proc.returncode:
        raise ValueError(
            proc.stderr.decode(errors="replace").strip() or "Git command failed"
        )
    return proc.stdout


def discover_sources(root: Path) -> tuple[list[str], list[str]]:
    """Include tracked and non-ignored untracked files, even in hidden harness dirs."""
    names = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    python: list[str] = []
    unsupported: list[str] = []
    for name in sorted(set(names.decode(errors="surrogateescape").split("\0")) - {""}):
        parts = Path(name).parts
        if EXCLUDED.intersection(parts) or any(
            p == ".env" or p.startswith(".env.") for p in parts
        ):
            continue
        suffix = Path(name).suffix
        if suffix != ".py" and suffix not in OTHER_SOURCE:
            continue
        if not safe_path(root, name).is_file():
            continue
        (python if suffix == ".py" else unsupported).append(name)
    return python, unsupported


def count_python(raw: bytes) -> LineCounts:
    """Exclude comments/docstring expressions while retaining same-line code."""
    encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
    text = raw.decode(encoding)
    tree = ast.parse(text)
    # AST columns are UTF-8 byte offsets; tokenizer columns are character offsets.
    lines = text.splitlines(keepends=True)

    def position(line: int, column: int) -> tuple[int, int]:
        return line, len(lines[line - 1].encode("utf-8")[:column].decode("utf-8"))

    spans = []
    for node in ast.walk(tree):
        if (
            isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            )
            and node.body
        ):
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                assert first.end_lineno is not None and first.end_col_offset is not None
                spans.append(
                    (
                        position(first.lineno, first.col_offset),
                        position(first.end_lineno, first.end_col_offset),
                    )
                )
    ignored = {
        tokenize.ENCODING,
        tokenize.ENDMARKER,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.NEWLINE,
        tokenize.NL,
        tokenize.COMMENT,
    }
    code_lines: set[int] = set()
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if (
            token.type in ignored
            or token.string == ";"
            or any(start <= token.start and token.end <= end for start, end in spans)
        ):
            continue
        code_lines.update(range(token.start[0], token.end[0] + 1))
    return LineCounts(len(text.splitlines()), len(code_lines))
