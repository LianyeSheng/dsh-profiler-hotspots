#!/usr/bin/env python3
"""Convert every version 1 chain file the version 2 rules can map losslessly.

Dry-run by default: prints each target and a unified diff. `--write` replaces
the file atomically. A version 2 file is already current. Frozen folders are
migrated too: the chain file is bookkeeping and no frozen evidence prose
changes. A version 1 file the conversion cannot map stays version 1 and
remains valid under the version 1 rules. No network.
"""

from __future__ import annotations

import argparse
import difflib
import os
from pathlib import Path
import sys
import tempfile

from chain_data import ChainError, dump_chain, load_chain, to_v2
from document_sources import find_root
from document_validation import validate_chain


def chain_files(root: Path) -> list[Path]:
    return sorted((root / ".agents" / "notes").glob("*/*/*/chain.yaml"))


def write_atomic(path: Path, text: str) -> None:
    handle, temporary = tempfile.mkstemp(prefix=".chain-", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def convert_one(root: Path, path: Path, *, write: bool) -> str:
    folder = path.parent
    rel = path.relative_to(root).as_posix()
    try:
        chain = load_chain(folder)
    except ChainError as exc:
        print(f"refuse: {rel}: {exc}")
        return "refused"
    if chain.version == 2:
        print(f"current: {rel}: version 2")
        return "current"
    try:
        converted = to_v2(chain)
    except ChainError as exc:
        print(f"leave: {rel}: {exc}")
        return "left"
    paths = sorted(item for item in folder.iterdir() if item.is_file())
    issues, _ = validate_chain(root, root, folder, converted, paths)
    if issues:
        details = "; ".join(f"{issue.rule}: {issue.message}" for _, issue in issues)
        print(f"leave: {rel}: {details}")
        return "left"
    text = dump_chain(converted)
    old_text = path.read_text(encoding="utf-8")
    print(f"target: {rel}")
    diff = list(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            text.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
    )
    sys.stdout.writelines(diff)
    if write:
        write_atomic(path, text)
        print(f"wrote {rel}")
    return "converted"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert every losslessly mappable version 1 chain file to version 2."
    )
    parser.add_argument("--write", action="store_true", help="replace chain files atomically")
    args = parser.parse_args(argv)
    try:
        root = find_root()
    except (OSError, ValueError) as exc:
        print(f"migrate_chain: {exc}", file=sys.stderr)
        return 2
    counts = {"converted": 0, "current": 0, "left": 0, "refused": 0}
    for path in chain_files(root):
        counts[convert_one(root, path, write=args.write)] += 1
    print(
        "summary: "
        + ", ".join(f"{name}={count}" for name, count in counts.items())
        + ("" if args.write else " (dry run; pass --write)")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
