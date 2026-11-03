#!/usr/bin/env python3
"""Resolve and edit evidence citations by full chain ID.

IDs are `<request>/<thread>/<discuss|reply>/<ref>` and resolve through the
unique request folder under `.agents/notes/*/*/<request>/chain.yaml`. Every
lookup uses the commit and path recorded in the chain file; version 2 derives
the Chinese path from the English anchor, while version 1 resolves its stored
pair. The read subcommands are read-only. `add`, `modify` and `delete` are the
only writers: they write version 2, convert a valid version 1 target in the
same write, refuse frozen folders, dry-run by default, and validate the result
before replacing the file atomically. No network.
"""

from __future__ import annotations

import argparse
import difflib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from chain_data import (
    Chain,
    ChainError,
    Coord,
    Ref,
    Thread,
    dump_chain,
    is_request_id,
    load_chain,
    to_v2,
)
from document_sources import find_root, git, safe_path
from document_validation import validate_chain

SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
RANGE = re.compile(r"L(\d+)(?:-L(\d+))?$")
EDITABLE_LIFECYCLES = ("proposed", "implemented")


def request_folder(root: Path, request: str) -> Path:
    matches = sorted(
        path for path in (root / ".agents" / "notes").glob(f"*/*/{request}") if path.is_dir()
    )
    if not matches:
        raise ChainError(f"no request folder {request!r} under .agents/notes/*/*/")
    if len(matches) > 1:
        raise ChainError(
            "request folder name is ambiguous; the gate requires unique names: "
            + ", ".join(str(path.relative_to(root)) for path in matches)
        )
    return matches[0]


def parse_id(value: str) -> tuple[str, str, str, str]:
    parts = value.split("/")
    if len(parts) != 4:
        raise ChainError("id must be <request>/<thread>/<discuss|reply>/<ref>")
    request, thread, kind, ref = parts
    if not is_request_id(request):
        raise ChainError(f"invalid request id {request!r}")
    if kind not in ("discuss", "reply"):
        raise ChainError("kind must be discuss or reply")
    for name, part in (("thread", thread), ("ref", ref)):
        if re.fullmatch(SLUG, part) is None:
            raise ChainError(f"invalid {name} {part!r}")
    return request, thread, kind, ref


def ancestor(root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
    )
    return result.returncode == 0


def resolve(root: Path, value: str):
    """Return (folder, chain, thread, kind, ref_name, Ref)."""
    request, thread, kind, ref = parse_id(value)
    folder = request_folder(root, request)
    chain = load_chain(folder)
    return folder, chain, thread, kind, ref, chain.ref(thread, kind, ref)


def blob_text(root: Path, commit: str, path: str) -> str:
    if not safe_path(path):
        raise ChainError(f"unsafe path {path!r}")
    if git(root, "cat-file", "-t", commit).strip() != b"commit":
        raise ChainError(f"{commit} is not a commit")
    if not ancestor(root, commit):
        raise ChainError(f"{commit} is not an ancestor of HEAD")
    if git(root, "cat-file", "-t", f"{commit}:{path}").strip() != b"blob":
        raise ChainError(f"{commit}:{path} is not a blob")
    return git(root, "show", f"{commit}:{path}").decode("utf-8")


def parse_range(value: str | None, line_count: int) -> tuple[int, int] | None:
    if value is None:
        return None
    match = RANGE.fullmatch(value)
    if match is None:
        raise ChainError(f"invalid line range {value!r}; use L14-L22 or L14")
    start = int(match[1])
    end = int(match[2]) if match[2] is not None else start
    if start < 1 or end < start or end > line_count:
        raise ChainError(f"line range {value!r} is outside the cited file ({line_count} lines)")
    return start, end


def command_show(root: Path, value: str, line_range: str | None, locale: str, raw: bool) -> int:
    folder, chain, thread, kind, ref_name, ref = resolve(root, value)
    del chain
    coord = ref.locale_coord(locale)
    text = blob_text(root, coord.commit, coord.path).splitlines()
    span = parse_range(line_range, len(text))
    body = text if span is None else text[span[0] - 1 : span[1]]
    if not raw:
        print(f"chain: {value}")
        print(f"locale: {locale}")
        print(f"request: {folder.relative_to(root)}")
        print(f"thread: {thread} ({kind}, ref {ref_name})")
        print(f"commit: {coord.commit}")
        print(f"path: {coord.path}")
        if span is not None:
            print(f"lines: L{span[0]}-L{span[1]}")
        hint = f"git show {coord.commit}:{coord.path}"
        if span is not None:
            hint += f" | sed -n '{span[0]},{span[1]}p'"
        print(f"hint: {hint}")
        print()
    sys.stdout.write("\n".join(body))
    if body:
        sys.stdout.write("\n")
    return 0


def command_refs(root: Path, value: str) -> int:
    parts = value.split("/")
    if len(parts) != 3:
        raise ChainError("refs id must be <request>/<thread>/<discuss|reply>")
    request, thread, kind = parts
    if not is_request_id(request) or re.fullmatch(SLUG, thread) is None or kind not in ("discuss", "reply"):
        raise ChainError("invalid refs id")
    folder = request_folder(root, request)
    chain: Chain = load_chain(folder)
    block = chain.block(thread, kind)
    print(f"{request}/{thread}/{kind} ({folder.relative_to(root)})")
    for name in sorted(block):
        ref = block[name]
        print(f"  {name}")
        print(f"    en {ref.en.commit} {ref.en.path}")
        if ref.zh is not None:
            print(f"    zh {ref.zh.commit} {ref.zh.path}")
    return 0


def command_diff(root: Path, value: str, locale: str) -> int:
    folder, chain, thread, kind, ref_name, ref = resolve(root, value)
    del chain
    coord = ref.locale_coord(locale)
    cited = blob_text(root, coord.commit, coord.path).splitlines(keepends=True)
    suffix = ".zh.md" if locale == "zh" else ".md"
    current_path = folder / f"{ref_name}{suffix}"
    if not current_path.is_file():
        raise ChainError(f"current file {current_path.relative_to(root)} does not exist")
    current = current_path.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = list(
        difflib.unified_diff(
            cited,
            current,
            fromfile=f"{coord.commit}:{coord.path}",
            tofile=str(current_path.relative_to(root)),
        )
    )
    if not diff:
        print("identical")
    else:
        sys.stdout.writelines(diff)
    return 0


def folder_lifecycle(root: Path, folder: Path) -> str:
    parts = folder.relative_to(root).parts
    if len(parts) != 5 or parts[:2] != (".agents", "notes"):
        raise ChainError(f"{folder.relative_to(root)} is not a request folder under .agents/notes")
    return parts[2]


def check_editable(root: Path, folder: Path) -> None:
    lifecycle = folder_lifecycle(root, folder)
    if lifecycle not in EDITABLE_LIFECYCLES:
        raise ChainError(
            f"{folder.relative_to(root)} is {lifecycle}; frozen evidence is never edited"
        )


def load_editable_chain(root: Path, folder: Path, *, allow_absent: bool) -> Chain | None:
    path = folder / "chain.yaml"
    if not path.exists():
        if allow_absent:
            return None
        raise ChainError(f"{path.relative_to(root)} does not exist")
    chain = load_chain(folder)
    try:
        return to_v2(chain)
    except ChainError as exc:
        raise ChainError(
            f"{path.relative_to(root)} is version {chain.version} and cannot be converted: {exc}"
        ) from exc


def make_coord(commit: str | None, path: str | None) -> Coord:
    if commit is None or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ChainError("--commit must be a full lowercase SHA")
    if not path:
        raise ChainError("--path must be a non-empty repository-relative path")
    return Coord(commit, path)


def evidence_stem(name: str) -> tuple[str, str] | None:
    if name.endswith(".zh.md"):
        name = name[: -len(".zh.md")]
    elif name.endswith(".md"):
        name = name[: -len(".md")]
    else:
        return None
    for kind in ("discuss", "reply"):
        if name.startswith(kind + "-"):
            return kind, name[len(kind) + 1 :]
    return None


def evidence_files(folder: Path) -> list[Path]:
    return [
        path
        for path in sorted(folder.iterdir())
        if path.is_file() and evidence_stem(path.name) is not None
    ]


def set_ref(chain: Chain, thread: str, kind: str, name: str, coord: Coord) -> Chain:
    threads = dict(chain.threads)
    entry = threads.get(thread)
    discuss = dict(entry.discuss) if entry is not None else {}
    reply = dict(entry.reply) if entry is not None and entry.reply is not None else None
    ref = Ref(coord)
    if kind == "discuss":
        discuss[name] = ref
    else:
        if entry is None:
            raise ChainError(
                f"thread {thread!r} has no discuss block; add its discuss ref first"
            )
        if reply is None:
            reply = {}
        reply[name] = ref
    threads[thread] = Thread(discuss, reply)
    return Chain(2, threads)


def remove_ref(chain: Chain, thread: str, kind: str, name: str) -> Chain:
    if thread not in chain.threads:
        raise ChainError(f"unknown thread {thread!r} in chain.yaml")
    entry = chain.threads[thread]
    block = entry.discuss if kind == "discuss" else entry.reply
    if block is None or name not in block:
        raise ChainError(f"unknown ref {name!r} in {thread}/{kind} of chain.yaml")
    discuss = dict(entry.discuss)
    reply = dict(entry.reply) if entry.reply is not None else None
    threads = dict(chain.threads)
    if kind == "discuss":
        del discuss[name]
        if not discuss:
            if reply:
                raise ChainError(
                    f"cannot remove the last discuss ref of {thread!r} while a reply block remains"
                )
            del threads[thread]
        else:
            threads[thread] = Thread(discuss, reply)
    else:
        assert reply is not None
        del reply[name]
        threads[thread] = Thread(discuss, reply if reply else None)
    return Chain(2, threads)


def validate_result(root: Path, folder: Path, chain: Chain) -> None:
    paths = sorted(path for path in folder.iterdir() if path.is_file())
    issues, _ = validate_chain(root, root, folder, chain, paths)
    if issues:
        details = "; ".join(f"{issue.rule}: {issue.message}" for _, issue in issues)
        raise ChainError(f"refusing an invalid chain edit: {details}")


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


def apply_edit(root: Path, folder: Path, text: str, *, write: bool) -> int:
    path = folder / "chain.yaml"
    old_text = path.read_text(encoding="utf-8") if path.exists() else None
    rel = path.relative_to(root).as_posix()
    print(f"target: {rel}")
    old_lines = old_text.splitlines(keepends=True) if old_text is not None else []
    fromfile = f"a/{rel}" if old_text is not None else "/dev/null"
    diff = list(
        difflib.unified_diff(old_lines, text.splitlines(keepends=True), fromfile=fromfile, tofile=f"b/{rel}")
    )
    if diff:
        sys.stdout.writelines(diff)
    else:
        print("identical")
    if write:
        write_atomic(path, text)
        print(f"wrote {rel}")
    return 0


def command_add(root: Path, value: str, commit: str, path: str, write: bool) -> int:
    request, thread, kind, name = parse_id(value)
    folder = request_folder(root, request)
    check_editable(root, folder)
    chain = load_editable_chain(root, folder, allow_absent=True)
    if chain is None:
        chain = Chain(2, {})
    updated = set_ref(chain, thread, kind, name, make_coord(commit, path))
    validate_result(root, folder, updated)
    return apply_edit(root, folder, dump_chain(updated), write=write)


def command_modify(root: Path, value: str, commit: str | None, path: str | None, write: bool) -> int:
    if commit is None and path is None:
        raise ChainError("modify requires --commit or --path")
    request, thread, kind, name = parse_id(value)
    folder = request_folder(root, request)
    check_editable(root, folder)
    chain = load_editable_chain(root, folder, allow_absent=False)
    assert chain is not None
    ref = chain.ref(thread, kind, name)
    updated_ref = make_coord(commit or ref.en.commit, path or ref.en.path)
    updated = set_ref(chain, thread, kind, name, updated_ref)
    validate_result(root, folder, updated)
    return apply_edit(root, folder, dump_chain(updated), write=write)


def command_delete(root: Path, value: str, write: bool) -> int:
    request, thread, kind, name = parse_id(value)
    folder = request_folder(root, request)
    check_editable(root, folder)
    chain = load_editable_chain(root, folder, allow_absent=False)
    assert chain is not None
    updated = remove_ref(chain, thread, kind, name)
    path = folder / "chain.yaml"
    rel = path.relative_to(root).as_posix()
    if not updated.threads:
        remaining = evidence_files(folder)
        if remaining:
            raise ChainError(
                "cannot remove the last thread while discuss/reply evidence remains: "
                + ", ".join(item.name for item in remaining)
            )
        print(f"target: {rel}")
        print(f"remove: {rel}")
        if write:
            path.unlink()
            print(f"removed {rel}")
        return 0
    validate_result(root, folder, updated)
    return apply_edit(root, folder, dump_chain(updated), write=write)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Resolve and edit full chain IDs against chain.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show", help="print the cited document or a line range")
    show.add_argument("id")
    show.add_argument("range", nargs="?", help="L14-L22 or L14")
    show.add_argument("--locale", choices=("en", "zh"), default="en")
    show.add_argument("--raw", action="store_true", help="print content without the hint header")
    refs = sub.add_parser("refs", help="list the refs of a discuss/reply block")
    refs.add_argument("id")
    diff = sub.add_parser("diff", help="compare the cited revision with the current file")
    diff.add_argument("id")
    diff.add_argument("--locale", choices=("en", "zh"), default="en")
    add = sub.add_parser("add", help="add a ref; dry-run unless --write")
    add.add_argument("id")
    add.add_argument("--commit", required=True)
    add.add_argument("--path", required=True)
    add.add_argument("--write", action="store_true", help="replace chain.yaml atomically")
    modify = sub.add_parser("modify", help="update a ref; dry-run unless --write")
    modify.add_argument("id")
    modify.add_argument("--commit")
    modify.add_argument("--path")
    modify.add_argument("--write", action="store_true", help="replace chain.yaml atomically")
    delete = sub.add_parser("delete", help="remove a ref; dry-run unless --write")
    delete.add_argument("id")
    delete.add_argument("--write", action="store_true", help="replace chain.yaml atomically")
    args = parser.parse_args(argv)
    try:
        root = find_root()
        if args.command == "show":
            return command_show(root, args.id, args.range, args.locale, args.raw)
        if args.command == "refs":
            return command_refs(root, args.id)
        if args.command == "diff":
            return command_diff(root, args.id, args.locale)
        if args.command == "add":
            return command_add(root, args.id, args.commit, args.path, args.write)
        if args.command == "modify":
            return command_modify(root, args.id, args.commit, args.path, args.write)
        return command_delete(root, args.id, args.write)
    except (ChainError, ValueError, OSError, UnicodeError) as exc:
        print(f"chain: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
