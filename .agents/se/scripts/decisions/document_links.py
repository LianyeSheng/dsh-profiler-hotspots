"""Repository-wide link and anchor checks.

Rules: .agents/se/contracts/anchor-convention.md (L group)
"""

from __future__ import annotations

from pathlib import Path
import re

from document_report import Finding
from document_sources import exists, read_text
from document_syntax import parse_code_references, parse_markdown_links

LINK_CONTRACT = ".agents/se/contracts/anchor-convention.md"

SCAN_SUFFIXES = {
    ".md",
    ".markdown",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".rb",
    ".sh",
    ".bash",
    ".toml",
    ".yml",
    ".yaml",
    ".sql",
    ".lua",
}

SKIP_DIRS = {
    ".git",
    ".tmp",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    "out",
    ".pnpm-store",
    ".next",
    "target",
    "test",
    "tests",
    "__tests__",
    "fixtures",
}

# Test references are synthetic paths, not links to actual repository records.
TEST_FILE = re.compile(r"\.(?:test|spec)\.[a-z]+$")

EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.\-]*:|#|//)")


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if TEST_FILE.search(path.name):
            continue
        yield path


def in_scope(root: Path, path: Path) -> bool:
    """Trees this contract governs. Legacy content elsewhere is warned, not failed."""
    rel = path.relative_to(root).as_posix()
    return rel.startswith((".agents/se/", ".agents/notes/", ".agents/skills/"))


def validate_links(root: Path, changed: set[str]) -> tuple[list[Finding], int]:
    """Check every in-repository reference; return findings and the number of scanned files."""
    findings = []
    scanned = 0
    for path in iter_files(root):
        scanned += 1
        if path.name == "chain.yaml":
            # Citation addresses are validated by the C rules; they are historical.
            continue
        rel = path.relative_to(root).as_posix()
        governed = in_scope(root, path)
        text = read_text(path, errors="replace")
        markdown = path.suffix in (".md", ".markdown")
        references = parse_markdown_links(text) if markdown else parse_code_references(text)
        for line, target in references:
            if markdown and EXTERNAL.match(target):
                continue
            if markdown and not target.startswith("/"):
                findings.append(
                    Finding(
                        "L2",
                        path,
                        line,
                        repr(target),
                        "Repository links must start with /",
                        "Use a repository-root-relative link",
                        "error" if governed else "warning",
                        LINK_CONTRACT,
                    )
                )
            # A malformed relative link is diagnosed above; repository links have one base.
            resolved = root / target.split("#", 1)[0].lstrip("/")
            if not exists(resolved):
                findings.append(
                    Finding(
                        "L3",
                        path,
                        line,
                        f"Target does not exist: {target}",
                        "Existing reference target",
                        "Correct the path or remove the reference",
                        contract=LINK_CONTRACT,
                    )
                )
            elif resolved.relative_to(root).as_posix() in changed:
                findings.append(
                    Finding(
                        "L4",
                        path,
                        line,
                        f"Referenced file changed: {target}",
                        "Confirm the reference still describes the target",
                        "Update the text if its meaning changed",
                        "warning",
                        LINK_CONTRACT,
                    )
                )
    return findings, scanned
