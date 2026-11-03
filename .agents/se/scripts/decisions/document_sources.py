"""Filesystem and Git history shared by the RFC gates."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import os
import re
import subprocess
import tempfile


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip() or "Git command failed")
    return result.stdout


def safe_path(path):
    return bool(
        path
        and not path.startswith("/")
        and "\\" not in path
        and all(p not in ("..", ".") for p in path.split("/"))
        and str(PurePosixPath(path)) == path
    )


def blob(root, sha, path):
    if not re.fullmatch(r"[0-9a-f]{40}", sha or "") or not safe_path(path):
        raise ValueError("Expected a full SHA and repository-relative path without traversal")
    if git(root, "cat-file", "-t", sha).strip() != b"commit":
        raise ValueError("Reviewed-Commit is not a commit")
    if git(root, "cat-file", "-t", f"{sha}:{path}").strip() != b"blob":
        raise ValueError("Reviewed-Path is not a blob")
    return git(root, "show", f"{sha}:{path}").decode("utf-8")


def find_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def read_text(path: Path, *, errors="strict") -> str:
    return path.read_text(encoding="utf-8", errors=errors)


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


@dataclass(frozen=True)
class DocumentSources:
    root: Path
    git_root: Path
    changed: frozenset[str]


@contextmanager
def document_sources(root: Path, *, base=None, staged=False, fix=False):
    """Use one baseline and one tree for every check."""
    if base is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", base) or base == "0" * 40:
            raise ValueError("--base must be an explicit nonzero 40-hex commit SHA")
        if git(root, "cat-file", "-t", base).strip() != b"commit":
            raise ValueError("--base must resolve to a commit")
    elif os.environ.get("CI"):
        raise ValueError(
            "CI requires explicit --base (or RFC_COMPARE_BASE through package scripts)"
        )
    if staged and fix:
        raise ValueError("--fix cannot edit the staged snapshot")
    args = ["diff"] + (["--cached"] if staged else [])
    args += ["--name-only", "--diff-filter=ACMR", base or "HEAD", "--"]
    changed = set(git(root, *args).decode().splitlines())
    if staged:
        with tempfile.TemporaryDirectory(prefix="rfc-index-") as temp:
            git(root, "checkout-index", "--all", f"--prefix={temp}/")
            yield DocumentSources(Path(temp), root, frozenset(changed))
    else:
        changed.update(
            git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines()
        )
        yield DocumentSources(root, root, frozenset(changed))


def iter_notes(notes_dir):
    return sorted(notes_dir.rglob("*"))


def is_file(path):
    return path.is_file()


def is_dir(path):
    return path.is_dir()


def exists(path):
    return path.exists()