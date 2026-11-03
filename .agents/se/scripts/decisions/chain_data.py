"""Restricted chain.yaml reader and writer shared by the gate and the CLI.

The chain file uses a closed YAML subset: block mappings and inline scalar
mappings only. Lists, anchors, quotes, multi-line scalars and trailing comments
are rejected; a whole-line comment starting with # is allowed.

Version 2 stores one locale-neutral English coordinate per ref; the Chinese
path is derived by replacing the trailing .md with .zh.md at the same commit.
Version 1 stores the en/zh pair and stays readable permanently so frozen and
unconvertible files remain valid under their own rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

from document_sources import safe_path

SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
REQUEST_ID = rf"[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}-{SLUG}"
KINDS = ("discuss", "reply")
COORD_KEYS = ("commit", "path")
VERSIONS = (1, 2)
RULES = "chain.yaml"


class ChainError(ValueError):
    """A chain-file grammar or schema violation."""


@dataclass(frozen=True)
class Coord:
    commit: str
    path: str


@dataclass(frozen=True)
class Ref:
    """One cited revision: a v2 English anchor or a stored v1 en/zh pair."""

    en: Coord
    zh: Coord | None = None

    def locale_coord(self, locale: str) -> Coord:
        if locale == "en":
            return self.en
        if locale != "zh":
            raise ChainError(f"locale must be en or zh, not {locale!r}")
        if self.zh is not None:
            return self.zh
        return Coord(self.en.commit, derive_zh_path(self.en.path))


@dataclass(frozen=True)
class Thread:
    discuss: dict[str, Ref]
    reply: dict[str, Ref] | None = None


@dataclass(frozen=True)
class Chain:
    version: int
    threads: dict[str, Thread]

    def block(self, thread: str, kind: str) -> dict[str, Ref]:
        entry = self.threads.get(thread)
        if entry is None:
            raise ChainError(f"unknown thread {thread!r} in {RULES}")
        if kind not in KINDS:
            raise ChainError(f"kind must be one of {KINDS}")
        block = entry.discuss if kind == "discuss" else entry.reply
        if block is None:
            raise ChainError(f"thread {thread!r} has no {kind} block in {RULES}")
        return block

    def ref(self, thread: str, kind: str, name: str) -> Ref:
        block = self.block(thread, kind)
        if name not in block:
            raise ChainError(f"unknown ref {name!r} in {thread}/{kind} of {RULES}")
        return block[name]


def derive_zh_path(path: str) -> str:
    """Return the derived Chinese path for an English Markdown path."""
    if not path.endswith(".md") or path.endswith(".zh.md"):
        raise ChainError(f"{path!r} is not an English .md path")
    return path[:-3] + ".zh.md"


def normalize_lifecycle(path: str) -> str:
    # Historical addresses retain their language and topic through lifecycle moves.
    parts = list(PurePosixPath(path).parts)
    if len(parts) >= 4 and parts[:2] == [".agents", "notes"]:
        parts[2] = "<lifecycle>"
    return "/".join(parts)


def folder_identity(folder: str) -> str:
    return normalize_lifecycle(folder)


def proposal_identity(path: str | None) -> str | None:
    if not path:
        return None
    path = normalize_lifecycle(path)
    if not path.endswith("/proposal.md") and not path.endswith("/proposal.zh.md"):
        path = re.sub(r"(\.zh)?\.md$", lambda m: "/proposal" + (m[1] or "") + ".md", path)
    return path


def ref_dir(path: str, ref: str) -> str | None:
    if ref == "proposal":
        identity_path = proposal_identity(path)
        if identity_path is None:
            return None
        return normalize_lifecycle(identity_path).rsplit("/", 1)[0]
    return normalize_lifecycle(path).rsplit("/", 1)[0]


def ref_basename(path: str, ref: str) -> str | None:
    if ref == "proposal":
        identity_path = proposal_identity(path)
        return PurePosixPath(identity_path).name if identity_path else None
    return PurePosixPath(path).name


def ref_title(ref: str, locale: str) -> str:
    if ref == "proposal":
        return "# 决策：" if locale == "zh" else "# Decision: "
    if ref.startswith("discuss-"):
        return "# 讨论：" if locale == "zh" else "# Discussion: "
    if ref.startswith("reply-"):
        return "# 回复：" if locale == "zh" else "# Reply: "
    raise ChainError(f"ref {ref!r} is not a local document stem")


def ref_path_issues(folder_id: str, name: str, coord: Coord, locale: str) -> list[str]:
    """Return the path-shape problems of one ref coordinate, without Git."""
    path = coord.path
    if not safe_path(path):
        return [f"path {path!r} is not a safe repository-relative path"]
    if locale == "zh":
        if not path.endswith(".zh.md"):
            return [f"path must end with .zh.md, not {path!r}"]
    elif path.endswith(".zh.md") or not path.endswith(".md"):
        return [f"path must be an English .md file, not {path!r}"]
    basename = ref_basename(path, name)
    expected_name = name + (".zh.md" if locale == "zh" else ".md")
    if basename != expected_name:
        return [f"path basename must be {expected_name}, not {basename!r}"]
    if ref_dir(path, name) != folder_id:
        return [f"path is outside this request folder: {path!r}"]
    return []


def _tokens(text: str):
    result = []
    for number, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise ChainError(f"line {number}: tabs are not allowed")
        stripped = raw.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2 != 0:
            raise ChainError(f"line {number}: indentation must use pairs of spaces")
        result.append((indent, stripped, number))
    if not result:
        raise ChainError(f"{RULES} is empty")
    return result


def _scalar(value: str, number: int) -> str:
    if any(token in value for token in "{}[]'\""):
        raise ChainError(f"line {number}: unsupported scalar syntax")
    if value == "":
        raise ChainError(f"line {number}: empty value")
    return value


def _flow_map(value: str, number: int) -> dict[str, str]:
    if not value.endswith("}"):
        raise ChainError(f"line {number}: unterminated inline mapping")
    inner = value[1:-1]
    pieces, current = [], ""
    for char in inner:
        if char == ",":
            pieces.append(current)
            current = ""
        else:
            current += char
    pieces.append(current)
    result = {}
    for piece in pieces:
        if ":" not in piece:
            raise ChainError(f"line {number}: expected inline key: value")
        key, item = piece.split(":", 1)
        key, item = key.strip(), item.strip()
        if re.fullmatch(SLUG, key) is None or item == "":
            raise ChainError(f"line {number}: invalid inline entry {piece!r}")
        if key in result:
            raise ChainError(f"line {number}: duplicate key {key!r}")
        result[key] = _scalar(item, number)
    return result


def parse_text(text: str) -> dict:
    """Parse the restricted YAML subset into nested dicts of scalars."""
    tokens = _tokens(text)
    position = 0

    def parse_map(indent: int) -> dict:
        nonlocal position
        result = {}
        while position < len(tokens):
            level, content, number = tokens[position]
            if level < indent:
                return result
            if level > indent:
                raise ChainError(f"line {number}: unexpected indentation")
            if ":" not in content:
                raise ChainError(f"line {number}: expected key: value")
            key, rest = content.split(":", 1)
            key, rest = key.strip(), rest.strip()
            if re.fullmatch(SLUG, key) is None:
                raise ChainError(f"line {number}: invalid key {key!r}")
            if key in result:
                raise ChainError(f"line {number}: duplicate key {key!r}")
            position += 1
            if rest == "":
                if position < len(tokens) and tokens[position][0] > level:
                    result[key] = parse_map(tokens[position][0])
                else:
                    raise ChainError(f"line {number}: {key!r} needs a nested mapping")
            elif rest.startswith("{"):
                result[key] = _flow_map(rest, number)
            else:
                result[key] = _scalar(rest, number)
        return result

    if tokens[0][0] != 0:
        raise ChainError(f"line {tokens[0][2]}: root mapping must start at column 1")
    parsed = parse_map(0)
    if position != len(tokens):
        raise ChainError(f"line {tokens[position][2]}: trailing content")
    return parsed


def _mapping(value, where: str, required: tuple[str, ...], optional: tuple[str, ...] = ()) -> dict:
    if not isinstance(value, dict):
        raise ChainError(f"{where}: expected a mapping")
    unknown = set(value) - set(required) - set(optional)
    if unknown:
        raise ChainError(f"{where}: unexpected keys {sorted(unknown)}")
    missing = [key for key in required if key not in value]
    if missing:
        raise ChainError(f"{where}: missing keys {missing}")
    return value


def _coord(value, where: str) -> Coord:
    if isinstance(value, str):
        raise ChainError(f"{where}: expected commit and path")
    mapping = _mapping(value, where, COORD_KEYS)
    commit, path = mapping["commit"], mapping["path"]
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ChainError(f"{where}: commit must be a full lowercase SHA")
    if not isinstance(path, str) or path == "":
        raise ChainError(f"{where}: path must be a nonempty string")
    return Coord(commit, path)


def _refs(value, where: str, version: int) -> dict[str, Ref]:
    if not isinstance(value, dict) or not value:
        raise ChainError(f"{where}: at least one ref is required")
    result = {}
    for name, body in value.items():
        if re.fullmatch(SLUG, name) is None:
            raise ChainError(f"{where}: invalid ref name {name!r}")
        if version == 2:
            mapping = _mapping(body, f"{where}.{name}", COORD_KEYS)
            result[name] = Ref(_coord(mapping, f"{where}.{name}"))
        else:
            mapping = _mapping(body, f"{where}.{name}", ("en", "zh"))
            result[name] = Ref(
                _coord(mapping["en"], f"{where}.{name}.en"),
                _coord(mapping["zh"], f"{where}.{name}.zh"),
            )
    return result


def parse_chain(text: str) -> Chain:
    data = parse_text(text)
    root = _mapping(data, RULES, ("version", "threads"))
    if root["version"] not in ("1", "2"):
        raise ChainError(f"{RULES}: version must be 1 or 2")
    version = int(root["version"])
    threads = root["threads"]
    if not isinstance(threads, dict) or not threads:
        raise ChainError(f"{RULES}: threads must be a nonempty mapping")
    result = {}
    for slug, body in threads.items():
        if re.fullmatch(SLUG, slug) is None:
            raise ChainError(f"{RULES}: invalid thread slug {slug!r}")
        mapping = _mapping(body, f"{RULES}.threads.{slug}", ("discuss",), ("reply",))
        discuss = _refs(mapping["discuss"], f"{slug}.discuss", version)
        reply = _refs(mapping["reply"], f"{slug}.reply", version) if "reply" in mapping else None
        result[slug] = Thread(discuss, reply)
    return Chain(version, result)


def load_chain(folder: Path) -> Chain:
    path = folder / RULES
    try:
        return parse_chain(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ChainError(f"cannot read {path}: {exc}") from exc
    except UnicodeError as exc:
        raise ChainError(f"{path}: not UTF-8 text") from exc


def _dump_coord(lines: list[str], indent: int, coord: Coord) -> None:
    lines.append(" " * indent + f"commit: {coord.commit}")
    lines.append(" " * indent + f"path: {coord.path}")


def _dump_block(lines: list[str], version: int, kind: str, block: dict[str, Ref]) -> None:
    if not block:
        raise ChainError(f"{kind}: at least one ref is required")
    lines.append(f"    {kind}:")
    for name, ref in block.items():
        lines.append(f"      {name}:")
        if version == 2:
            if ref.zh is not None:
                raise ChainError(f"{kind}/{name}: a version 2 ref stores one English coordinate")
            _dump_coord(lines, 8, ref.en)
        else:
            if ref.zh is None:
                raise ChainError(f"{kind}/{name}: a version 1 ref stores en and zh")
            lines.append("        en:")
            _dump_coord(lines, 10, ref.en)
            lines.append("        zh:")
            _dump_coord(lines, 10, ref.zh)


def dump_chain(chain: Chain) -> str:
    """Serialize a chain in canonical block style, preserving entry order."""
    if chain.version not in VERSIONS:
        raise ChainError(f"{RULES}: version must be 1 or 2")
    if not chain.threads:
        raise ChainError(f"{RULES}: cannot write an empty chain")
    lines = [f"version: {chain.version}", "threads:"]
    for slug, thread in chain.threads.items():
        lines.append(f"  {slug}:")
        _dump_block(lines, chain.version, "discuss", thread.discuss)
        if thread.reply is not None:
            _dump_block(lines, chain.version, "reply", thread.reply)
    return "\n".join(lines) + "\n"


def _convert_ref(ref: Ref, where: str) -> Ref:
    if ref.zh is None:
        raise ChainError(f"{where}: missing the zh coordinate")
    if ref.en.commit != ref.zh.commit:
        raise ChainError(f"{where}: en and zh commits differ")
    expected = derive_zh_path(ref.en.path)
    if ref.zh.path != expected:
        raise ChainError(f"{where}: zh path is not the en path with .zh.md")
    return Ref(ref.en)


def to_v2(chain: Chain) -> Chain:
    """Convert a v1 chain losslessly; raise ChainError when it cannot be mapped."""
    if chain.version == 2:
        return chain
    if chain.version != 1:
        raise ChainError(f"{RULES}: version must be 1 or 2")
    threads = {}
    for slug, thread in chain.threads.items():
        discuss = {
            name: _convert_ref(ref, f"{slug}/discuss/{name}") for name, ref in thread.discuss.items()
        }
        reply = None
        if thread.reply is not None:
            reply = {
                name: _convert_ref(ref, f"{slug}/reply/{name}") for name, ref in thread.reply.items()
            }
        threads[slug] = Thread(discuss, reply)
    return Chain(2, threads)


def is_request_id(value: str) -> bool:
    return re.fullmatch(REQUEST_ID, value) is not None
