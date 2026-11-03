#!/usr/bin/env python3
"""Install, upgrade or remove kit components in a target repository.

Standard library only and offline. The kit sources live under components/ in the
kit checkout; every component declares its source-to-installed mapping in
components/<id>/registry.json. This script renders the selected components into
.agents/se/ and .agents/skills of the target, composes one marked block per
component into the target AGENTS.md, and records every installed path, digest
and block digest in .agents/se/install-manifest.json.

Every subcommand is a dry run unless --apply is given. Installation writes a
file only when it is absent or byte-identical; a different existing file or
block is a conflict that exits non-zero and writes nothing. Removal is
all-or-nothing per selected component: a missing file, a missing or duplicated
block, or a digest mismatch stops the command before anything is deleted.

--self is reserved for se-tools itself: an uninstall or upgrade that would
delete the source repository's generated installed tree additionally requires
--confirm-self.

The rendered payload is self-contained. Rendering rewrites Markdown link
targets under components/ to their installed paths (the language switcher of a
bilingual pair) and drops code anchor lines that cite this repository's decision
tree, which the installed payload does not carry. Bilingual consistency records
name no pair path, so they render unchanged beside a source pair and its
installed copy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

BEGIN_RE = re.compile(r"^<!-- se-tools:begin component=([a-z][a-z0-9-]*) -->$")
END_RE = re.compile(r"^<!-- se-tools:end component=([a-z][a-z0-9-]*) -->$")
ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
ANCHOR_RE = re.compile(r"^(?:Decision|Rules):[ \t]+\S*\.agents/notes/\S*\.md[ \t]*$")
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
MD_COMPONENT_TARGET_RE = re.compile(r"(\]\(\s*)(/components/[^)\s]+)")
CODE_ANCHOR_RE = re.compile(r"(?<![\w/])(\.agents/notes/[\w./-]+\.md)")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
TICK = chr(96)

MANIFEST_REL = ".agents/se/install-manifest.json"
AGENTS_REL = "AGENTS.md"
INSTALL_ROOTS = (".agents/se", ".agents/skills")
SKIP_DIRECTORY_NAMES = {"__pycache__", "node_modules", ".git", "dist"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".DS_Store"}
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".mjs", ".cjs"}
MANIFEST_KEYS = ("kit_revision", "components", "mode", "agents_md_created", "files", "blocks")


class KitError(Exception):
    """A configuration, selection or target problem that stops the command."""


@dataclass(frozen=True)
class InstallEntry:
    source: str
    target: str


@dataclass(frozen=True)
class Component:
    id: str
    consequence: str
    prerequisites: tuple
    directory: Path
    fragments: tuple
    install: tuple


@dataclass
class Registry:
    revision: str
    components: dict
    order: list


@dataclass(frozen=True)
class SourceFile:
    path: Path
    component: str
    repo_relative: str
    target: str


@dataclass
class Block:
    start: int
    end: int
    text: str


@dataclass
class Manifest:
    kit_revision: str
    components: list
    mode: str
    agents_md_created: bool
    files: list
    blocks: dict

    def files_of(self, component_ids):
        wanted = set(component_ids)
        return [record for record in self.files if record["component"] in wanted]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_text(text: str) -> str:
    return sha_bytes(text.encode("utf-8"))


def safe_relative(value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value or "\x00" in value:
        return False
    parts = value.split("/")
    return all(part not in ("", ".", "..") for part in parts)


def installed_root_of(rel: str):
    for root in INSTALL_ROOTS:
        if rel == root or rel.startswith(root + "/"):
            return root
    return None


def find_source_root(script_path: Path):
    for parent in script_path.resolve().parents:
        if (parent / "components" / "kit" / "install.py").is_file():
            return parent
    return None


def mask_inline_code(line: str) -> str:
    characters = list(line)
    index = 0
    while index < len(characters):
        if characters[index] != TICK:
            index += 1
            continue
        run = 0
        while index + run < len(characters) and characters[index + run] == TICK:
            run += 1
        cursor = index + run
        closed = False
        while cursor < len(characters):
            if characters[cursor] != TICK:
                cursor += 1
                continue
            closing = 0
            while cursor + closing < len(characters) and characters[cursor + closing] == TICK:
                closing += 1
            if closing == run:
                for position in range(index, cursor + closing):
                    characters[position] = " "
                index = cursor + closing
                closed = True
                break
            cursor += closing
        if not closed:
            index += run
    return "".join(characters)

def load_registry(source_root: Path) -> Registry:
    root = source_root / "components"
    if (root / "registry.json").exists():
        raise KitError("central components/registry.json is no longer supported; use components/<id>/registry.json")
    components = {}
    targets = {}
    revision = None
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or directory.name in SKIP_DIRECTORY_NAMES or directory.name.startswith("__"):
            continue
        path = directory / "registry.json"
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise KitError("cannot read component registry " + str(path) + ": " + str(exc)) from exc
        if not isinstance(entry, dict):
            raise KitError(str(path) + " must hold a JSON object")
        allowed = {"id", "consequence", "prerequisites", "fragments", "install"}
        if directory.name == "kit":
            allowed.add("revision")
            revision = entry.get("revision")
            if not isinstance(revision, str) or not revision.strip():
                raise KitError(str(path) + " needs a non-empty string 'revision'")
        unknown = sorted(set(entry) - allowed)
        if unknown:
            raise KitError(str(path) + " has unsupported fields: " + ", ".join(unknown))
        component_id = entry.get("id")
        if not isinstance(component_id, str) or not ID_RE.fullmatch(component_id):
            raise KitError(str(path) + " needs a lower-kebab-case 'id'")
        if component_id in components:
            raise KitError("duplicate component id " + component_id)
        if component_id != directory.name:
            raise KitError(str(path) + ": component id " + repr(component_id) + " does not match directory " + repr(directory.name))
        consequence = entry.get("consequence")
        if not isinstance(consequence, str) or not consequence.strip():
            raise KitError("component " + component_id + " needs a non-empty 'consequence'")
        prerequisites = entry.get("prerequisites")
        if not isinstance(prerequisites, list) or not all(isinstance(item, str) for item in prerequisites):
            raise KitError("component " + component_id + " needs a string array 'prerequisites'")
        fragments = entry.get("fragments")
        if not isinstance(fragments, list) or not all(isinstance(item, str) for item in fragments):
            raise KitError("component " + component_id + " needs a string array 'fragments'")
        install = entry.get("install")
        if not isinstance(install, list) or not install:
            raise KitError("component " + component_id + " needs a non-empty 'install' array")
        for fragment in fragments:
            if not safe_relative(fragment) or not (directory / fragment).is_file():
                raise KitError("component " + component_id + " fragment " + repr(fragment) + " does not resolve")
        parsed_entries = []
        for issue in install:
            if not isinstance(issue, dict) or set(issue) != {"source", "target"}:
                raise KitError("component " + component_id + " install entries need exactly 'source' and 'target'")
            source, target = issue["source"], issue["target"]
            if not isinstance(source, str) or not safe_relative(source):
                raise KitError("component " + component_id + " has an unsafe install source " + repr(source))
            if not isinstance(target, str) or not safe_relative(target):
                raise KitError("component " + component_id + " has an unsafe install target " + repr(target))
            if installed_root_of(target) is None:
                raise KitError("component " + component_id + " target " + repr(target) + " is outside the installed roots")
            if not (directory / source).exists():
                raise KitError("component " + component_id + " install source " + repr(source) + " does not resolve")
            for claimed, owner in targets.items():
                if target == claimed:
                    raise KitError("install target " + repr(target) + " overlaps " + repr(claimed) + " claimed by " + owner)
            targets[target] = component_id
            parsed_entries.append(InstallEntry(source=source, target=target))
        components[component_id] = Component(
            id=component_id, consequence=consequence, prerequisites=tuple(prerequisites),
            directory=directory, fragments=tuple(fragments), install=tuple(parsed_entries),
        )
    if revision is None:
        raise KitError("components/kit/registry.json must declare the kit revision")
    for component in components.values():
        for prerequisite in component.prerequisites:
            if prerequisite not in components:
                raise KitError("component " + component.id + " declares unknown prerequisite " + repr(prerequisite))
    order = []
    pending = set(components)
    while pending:
        ready = sorted(component_id for component_id in pending
                       if set(components[component_id].prerequisites).issubset(order))
        if not ready:
            raise KitError("component dependency cycle: " + ", ".join(sorted(pending)))
        component_id = ready[0]
        order.append(component_id)
        pending.remove(component_id)
    registry = Registry(revision=revision, components=components, order=order)
    expand_files(registry, order)
    return registry


def prerequisite_closure(registry: Registry, selected) -> list:
    required = set()
    stack = list(selected)
    while stack:
        component_id = stack.pop()
        if component_id in required:
            continue
        required.add(component_id)
        stack.extend(registry.components[component_id].prerequisites)
    return [component_id for component_id in registry.order if component_id in required]


def select_components(registry: Registry, requested) -> list:
    if requested is None:
        return list(registry.order)
    wanted = [item.strip() for item in requested.split(",") if item.strip()]
    if not wanted:
        raise KitError("--components needs at least one component id")
    unknown = [item for item in wanted if item not in registry.components]
    if unknown:
        raise KitError("unknown component(s): " + ", ".join(unknown) + "; known: " + ", ".join(registry.order))
    if len(set(wanted)) != len(wanted):
        raise KitError("duplicate component in --components")
    return [component_id for component_id in registry.order if component_id in set(wanted)]


def unmet_prerequisites(registry: Registry, selected) -> list:
    missing = []
    for component_id in selected:
        for prerequisite in registry.components[component_id].prerequisites:
            if prerequisite not in selected:
                missing.append(component_id + " requires " + prerequisite)
    return missing


def component_source_root(registry: Registry) -> Path:
    first = registry.components[registry.order[0]]
    return first.directory.parent.parent


def expand_files(registry: Registry, selected) -> dict:
    repo_root = component_source_root(registry)
    files = {}
    for component_id in selected:
        component = registry.components[component_id]
        for entry in component.install:
            source = component.directory / entry.source
            if source.is_file():
                candidates = [(source, entry.target)]
            elif source.is_dir():
                candidates = []
                for root, directories, names in os.walk(source):
                    directories[:] = sorted(name for name in directories if name not in SKIP_DIRECTORY_NAMES)
                    for name in sorted(names):
                        if name in SKIP_SUFFIXES or name.endswith(".pyc"):
                            continue
                        candidate = Path(root) / name
                        relative = candidate.relative_to(source).as_posix()
                        candidates.append((candidate, entry.target.rstrip("/") + "/" + relative))
            else:
                raise KitError("install source " + str(source) + " is neither a file nor a directory")
            for candidate, target in candidates:
                if candidate.is_symlink():
                    raise KitError("refusing symbolic link in the kit sources: " + str(candidate))
                for claimed in files:
                    if target == claimed or target.startswith(claimed + "/") or claimed.startswith(target + "/"):
                        raise KitError("install target " + repr(target) + " overlaps produced path " + repr(claimed))
                files[target] = SourceFile(
                    path=candidate,
                    component=component_id,
                    repo_relative=candidate.relative_to(repo_root).as_posix(),
                    target=target,
                )
    return files


def source_target_map(registry: Registry) -> dict:
    return {source.repo_relative: source.target for source in expand_files(registry, registry.order).values()}


def render_bytes(registry: Registry, file: SourceFile, remap: dict) -> bytes:
    data = file.path.read_bytes()
    if file.path.suffix == ".md":
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return data

        def replace(match):
            target = match.group(2)
            mapped = remap.get(target.lstrip("/"))
            return match.group(1) + ("/" + mapped if mapped is not None else target)

        return MD_COMPONENT_TARGET_RE.sub(replace, text).encode("utf-8")
    if file.path.suffix in CODE_SUFFIXES:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return data
        lines = text.splitlines(keepends=True)
        kept = [line for line in lines if not ANCHOR_RE.match(line.rstrip("\r\n").strip())]
        if len(kept) != len(lines):
            return "".join(kept).encode("utf-8")
    return data


def read_fragment(component: Component, fragment: str) -> str:
    text = (component.directory / fragment).read_text(encoding="utf-8").replace("\r\n", "\n")
    if "<!-- se-tools:" in text:
        raise KitError("component " + component.id + " fragment " + fragment + " contains a kit marker")
    return text.rstrip("\n")


def render_block(component: Component, fragment: str) -> str:
    body = read_fragment(component, fragment)
    return "\n".join(
        [
            "<!-- se-tools:begin component=" + component.id + " -->",
            *body.split("\n"),
            "<!-- se-tools:end component=" + component.id + " -->",
        ]
    )


def markdown_links(text: str) -> list:
    """Markdown link targets outside fenced code blocks and inline code."""
    links = []
    fence = None
    for number, line in enumerate(text.split("\n"), 1):
        fence_match = re.match(r"^ {0,3}([\x60~]{3,})(.*)$", line)
        if fence_match:
            token, tail = fence_match.group(1), fence_match.group(2)
            if fence is None:
                fence = token
                continue
            if token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
                continue
        if fence is not None:
            continue
        masked = mask_inline_code(line)
        for target in MD_LINK_RE.findall(masked):
            links.append((number, target))
    return links


def links_resolve_inside(path: str, allowed: set) -> bool:
    if path in allowed:
        return True
    prefix = path.rstrip("/") + "/"
    return any(item.startswith(prefix) for item in allowed)


def validate_links_for(allowed: set, label: str, text: str, allow_external: bool) -> list:
    problems = []
    for number, target in markdown_links(text):
        if target.startswith("#"):
            continue
        if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", target):
            if not allow_external:
                problems.append(label + ":" + str(number) + ": external link " + repr(target))
            continue
        if not target.startswith("/"):
            problems.append(label + ":" + str(number) + ": link " + repr(target) + " is not repository-root relative")
            continue
        path = target.split("#", 1)[0].split("?", 1)[0].lstrip("/")
        if path == ".agents" or path.startswith(".agents/notes/"):
            problems.append(label + ":" + str(number) + ": link " + repr(target) + " points into .agents/notes/")
            continue
        if path.startswith("components/") or installed_root_of(path) is None:
            problems.append(label + ":" + str(number) + ": link " + repr(target) + " is outside the installed roots")
            continue
        if not links_resolve_inside(path, allowed):
            problems.append(label + ":" + str(number) + ": link " + repr(target) + " is not installed by this component or its prerequisites")
    return problems


def allowed_targets(registry: Registry, component_id: str, component_targets: dict) -> set:
    allowed = set()
    for member in prerequisite_closure(registry, [component_id]):
        allowed.update(component_targets.get(member, set()))
    return allowed


def validate_fragments(registry: Registry, selected, component_targets: dict) -> list:
    problems = []
    for component_id in selected:
        component = registry.components[component_id]
        allowed = allowed_targets(registry, component_id, component_targets)
        for fragment in component.fragments:
            problems.extend(validate_links_for(allowed, component_id + "/" + fragment, read_fragment(component, fragment), False))
    return problems


def validate_payload(registry: Registry, selected, files: dict, remap: dict, component_targets: dict) -> list:
    problems = []
    for target, source in sorted(files.items()):
        if not target.endswith(".md"):
            continue
        allowed = allowed_targets(registry, source.component, component_targets)
        text = render_bytes(registry, source, remap).decode("utf-8", errors="replace")
        problems.extend(validate_links_for(allowed, target, text, True))
    for target, source in sorted(files.items()):
        if source.path.suffix not in CODE_SUFFIXES:
            continue
        text = render_bytes(registry, source, remap).decode("utf-8", errors="replace")
        for number, line in enumerate(text.split("\n"), 1):
            for match in CODE_ANCHOR_RE.finditer(line):
                problems.append(target + ":" + str(number) + ": code anchor " + repr(match.group(1)) + " points into .agents/notes/")
    return problems


def parse_agents(text: str):
    lines = text.split("\n")
    blocks = {}
    problems = []
    index = 0
    while index < len(lines):
        begin = BEGIN_RE.match(lines[index])
        if begin:
            component_id = begin.group(1)
            end = index + 1
            broken = False
            while end < len(lines) and not END_RE.match(lines[end]):
                if BEGIN_RE.match(lines[end]):
                    problems.append("AGENTS.md:" + str(index + 1) + ": block " + component_id + " opens before the previous block ends")
                    broken = True
                    break
                end += 1
            if broken:
                break
            if end >= len(lines):
                problems.append("AGENTS.md:" + str(index + 1) + ": block " + component_id + " has no end marker")
                break
            closing = END_RE.match(lines[end])
            if closing.group(1) != component_id:
                problems.append("AGENTS.md:" + str(end + 1) + ": block " + component_id + " ends with marker " + closing.group(1))
                break
            if component_id in blocks:
                problems.append("AGENTS.md:" + str(index + 1) + ": duplicate block for " + component_id)
            else:
                blocks[component_id] = Block(start=index, end=end, text="\n".join(lines[index : end + 1]))
            index = end + 1
            continue
        if END_RE.match(lines[index]):
            problems.append("AGENTS.md:" + str(index + 1) + ": end marker without a begin marker")
        index += 1
    return lines, blocks, problems


def read_agents(target: Path):
    path = target / AGENTS_REL
    if not path.exists():
        return None, [], {}, []
    if path.is_symlink() or not path.is_file():
        raise KitError(AGENTS_REL + " exists but is not a regular file")
    text = path.read_text(encoding="utf-8")
    lines, blocks, problems = parse_agents(text)
    return text, lines, blocks, problems


def compose_agents(existing_text, blocks, expected, order):
    """Rewrite the managed block region in registry order, leaving other text alone.

    The region is contiguous except for blank lines; content between two marked
    blocks is a conflict because reordering it would move text the installer does
    not own. The composed text is canonical, so an unchanged install rewrites
    nothing and the second run is byte-identical.
    """
    merged = {component_id: block.text for component_id, block in blocks.items()}
    merged.update(expected)
    ordered = [merged[component_id] for component_id in order if component_id in merged]
    if existing_text is None:
        text = "\n\n".join(ordered)
        return (text + "\n" if text else ""), len(expected)
    lines = existing_text.split("\n")
    if existing_text.endswith("\n") and lines and lines[-1] == "":
        lines = lines[:-1]
    if not blocks:
        head = lines
        tail = []
        first = len(head)
        last_end = len(head) - 1
    else:
        first = min(block.start for block in blocks.values())
        last_end = max(block.end for block in blocks.values())
        covered = set()
        for block in blocks.values():
            covered.update(range(block.start, block.end + 1))
        for index in range(first, last_end + 1):
            if index not in covered and lines[index].strip() != "":
                raise KitError("AGENTS.md has content between marked kit blocks")
        head = lines[:first]
        tail = lines[last_end + 1 :]
    while head and head[-1].strip() == "":
        head.pop()
    while tail and tail[0].strip() == "":
        tail.pop(0)
    body = list(head)
    for position, block_text in enumerate(ordered):
        if body:
            body.append("")
        elif position > 0:
            body.append("")
        body.extend(block_text.split("\n"))
    if tail:
        if body:
            body.append("")
        body.extend(tail)
    text = "\n".join(body)
    return (text + "\n" if text else ""), len([component_id for component_id in expected if component_id not in blocks])


def read_manifest(target: Path):
    path = target / MANIFEST_REL
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise KitError("cannot read " + MANIFEST_REL + ": " + str(exc)) from exc
    if not isinstance(value, dict):
        raise KitError(MANIFEST_REL + " must hold a JSON object")
    missing = [key for key in MANIFEST_KEYS if key not in value]
    if missing:
        raise KitError(MANIFEST_REL + " is missing " + ", ".join(missing))
    unknown = [key for key in value if key not in MANIFEST_KEYS]
    if unknown:
        raise KitError(MANIFEST_REL + " has unsupported fields: " + ", ".join(unknown))
    revision = value["kit_revision"]
    components = value["components"]
    mode = value["mode"]
    created = value["agents_md_created"]
    files = value["files"]
    blocks = value["blocks"]
    if not isinstance(revision, str) or not revision:
        raise KitError(MANIFEST_REL + ": kit_revision must be a non-empty string")
    if not isinstance(components, list) or not all(isinstance(item, str) for item in components):
        raise KitError(MANIFEST_REL + ": components must be a string array")
    if mode not in ("tracked", "untracked"):
        raise KitError(MANIFEST_REL + ": mode must be tracked or untracked")
    if not isinstance(created, bool):
        raise KitError(MANIFEST_REL + ": agents_md_created must be a boolean")
    if not isinstance(files, list):
        raise KitError(MANIFEST_REL + ": files must be an array")
    parsed_files = []
    for record in files:
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "component"}:
            raise KitError(MANIFEST_REL + ": each file record needs path, sha256 and component")
        if not safe_relative(record["path"]) or installed_root_of(record["path"]) is None:
            raise KitError(MANIFEST_REL + ": unsafe file path " + repr(record["path"]))
        if not isinstance(record["sha256"], str) or not SHA_RE.match(record["sha256"]):
            raise KitError(MANIFEST_REL + ": bad digest for " + repr(record["path"]))
        if not isinstance(record["component"], str):
            raise KitError(MANIFEST_REL + ": bad component for " + repr(record["path"]))
        parsed_files.append({"path": record["path"], "sha256": record["sha256"], "component": record["component"]})
    if not isinstance(blocks, dict) or not all(
        isinstance(key, str) and isinstance(item, str) and SHA_RE.match(item) for key, item in blocks.items()
    ):
        raise KitError(MANIFEST_REL + ": blocks must map component ids to sha256 digests")
    return Manifest(
        kit_revision=revision,
        components=components,
        mode=mode,
        agents_md_created=created,
        files=parsed_files,
        blocks=blocks,
    )


def manifest_text(manifest: Manifest, registry) -> str:
    order = list(registry.order) if registry is not None else []
    order.extend(component_id for component_id in manifest.components if component_id not in order)
    rank = {component_id: index for index, component_id in enumerate(order)}
    selected = set(manifest.components)
    files = sorted(manifest.files, key=lambda record: (rank.get(record["component"], len(order)), record["path"]))
    value = {
        "kit_revision": manifest.kit_revision,
        "components": [component_id for component_id in order if component_id in selected],
        "mode": manifest.mode,
        "agents_md_created": manifest.agents_md_created,
        "files": files,
        "blocks": {component_id: manifest.blocks[component_id] for component_id in order if component_id in manifest.blocks},
    }
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write_file(target: Path, relative: str, data: bytes, mode=None) -> None:
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".se-tools-tmp")
    temporary.write_bytes(data)
    if mode is not None:
        os.chmod(temporary, mode)
    os.replace(temporary, destination)


def check_destination(target: Path, relative: str) -> list:
    problems = []
    destination = target / relative
    current = destination
    while current != target and target in current.parents:
        if current.is_symlink():
            problems.append("refusing symbolic link at " + current.relative_to(target).as_posix())
            return problems
        current = current.parent
    resolved_target = target.resolve()
    resolved_destination = destination.resolve()
    if resolved_destination != resolved_target and resolved_target not in resolved_destination.parents:
        problems.append(relative + " resolves outside the target")
    return problems


def tracked_roots_check(target: Path, mode: str) -> list:
    if mode != "untracked":
        return []
    path = target / ".gitignore"
    if not path.is_file():
        return ["untracked mode requires a .gitignore"]
    patterns = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
    missing = [root for root in INSTALL_ROOTS if root not in patterns and root + "/" not in patterns]
    if missing:
        return ["untracked mode requires .gitignore to list " + ", ".join(missing)]
    return []


def decide_mode(args, manifest) -> str:
    requested = getattr(args, "mode", None)
    if manifest is not None:
        if requested is not None and requested != manifest.mode:
            raise KitError("the installed tree records mode " + repr(manifest.mode) + "; refusing " + repr(requested) + " without an uninstall")
        return manifest.mode
    return requested or "tracked"


def is_self_target(target: Path, source_root) -> bool:
    return source_root is not None and target.resolve() == source_root.resolve()


def self_guard(args, target: Path, source_root, action: str) -> None:
    if not is_self_target(target, source_root):
        if args.self or args.confirm_self:
            raise KitError("--self and --confirm-self are only valid for the se-tools source repository")
        return
    if not (args.self and args.confirm_self):
        raise KitError(
            action + " would delete the se-tools source repository's generated installed tree; "
            "pass --self and --confirm-self to proceed (--self is se-tools-internal)"
        )


def describe(registry, selected, mode: str, command: str, target: Path) -> None:
    print("se-tools kit: " + command)
    print("  target: " + str(target))
    print("  mode: " + mode)
    if registry is not None:
        print("  kit revision: " + registry.revision)
    print("  components:")
    for component_id in selected:
        if registry is None or component_id not in registry.components:
            print("    " + component_id + " (recorded component)")
            continue
        component = registry.components[component_id]
        print("    " + component_id + " - " + component.consequence)
        print("      prerequisites: " + (", ".join(component.prerequisites) or "none"))


def print_problems(problems, header: str) -> None:
    print(header + ":", file=sys.stderr)
    for problem in problems:
        print("  " + problem, file=sys.stderr)


def resolve_target(value: str) -> Path:
    path = Path(value)
    if not path.exists():
        raise KitError("target " + repr(value) + " does not exist")
    if not path.is_dir():
        raise KitError("target " + repr(value) + " is not a directory")
    return path.resolve()


def check_manifest_blocks(manifest: Manifest, blocks, registry: Registry) -> list:
    problems = []
    for component_id in manifest.components:
        if component_id not in registry.components:
            problems.append("manifest records unknown component " + repr(component_id))
            continue
        if component_id not in blocks:
            problems.append("manifest records a block for " + component_id + " but AGENTS.md has none")
            continue
        if manifest.blocks.get(component_id) != sha_text(blocks[component_id].text):
            problems.append("AGENTS.md block for " + component_id + " does not match the manifest digest")
    return problems


class _InstallRequest:
    """Arguments for the reinstall step of an upgrade (attribute named self is legal here)."""

    def __init__(self, target, components, mode, apply):
        self.target = target
        self.components = components
        self.mode = mode
        self.apply = apply
        self.self = False
        self.confirm_self = False


def command_install(args, registry: Registry, source_root, removal=None) -> int:
    target = resolve_target(args.target)
    manifest = read_manifest(target)
    ignored_paths = set()
    if removal is not None:
        # Validate the reinstall against the post-removal view without changing disk.
        if args.apply:
            raise KitError("a projected install must be a dry run")
        removed_components, ignored_paths = removal
        remaining_components = [item for item in manifest.components if item not in removed_components]
        manifest = Manifest(
            kit_revision=manifest.kit_revision, components=remaining_components, mode=manifest.mode,
            agents_md_created=manifest.agents_md_created,
            files=[item for item in manifest.files if item["component"] not in removed_components],
            blocks={key: value for key, value in manifest.blocks.items() if key not in removed_components},
        )
    selected = select_components(registry, args.components)
    already_installed = set(manifest.components if manifest is not None else [])
    satisfied = set(selected) | already_installed
    missing = []
    for component_id in selected:
        for prerequisite in registry.components[component_id].prerequisites:
            if prerequisite not in satisfied:
                missing.append(component_id + " requires " + prerequisite)
    if missing:
        print_problems(missing, "unmet prerequisites")
        print("nothing written; add the required components to the selection", file=sys.stderr)
        return 1
    mode = decide_mode(args, manifest)
    problems = tracked_roots_check(target, mode)
    if problems:
        print_problems(problems, "invalid installation mode")
        return 1
    describe(registry, selected, mode, "install", target)

    files = expand_files(registry, selected)
    remap = source_target_map(registry)
    component_targets = {}
    for target_rel, source in files.items():
        component_targets.setdefault(source.component, set()).add(target_rel)
    if manifest is not None:
        for record in manifest.files:
            component_targets.setdefault(record["component"], set()).add(record["path"])
    problems = validate_fragments(registry, selected, component_targets)
    problems.extend(validate_payload(registry, selected, files, remap, component_targets))
    if problems:
        print_problems(problems, "payload closure failed")
        print("nothing written", file=sys.stderr)
        return 1

    writes = []
    conflicts = []
    collisions = []
    rendered = {}
    for target_rel, source in sorted(files.items()):
        problems = check_destination(target, target_rel)
        if problems:
            conflicts.extend(problems)
            continue
        data = render_bytes(registry, source, remap)
        rendered[target_rel] = data
        destination = target / target_rel
        if destination.exists() and target_rel not in ignored_paths:
            if destination.is_symlink() or not destination.is_file():
                conflicts.append(target_rel + ": exists but is not a regular file")
                continue
            if destination.read_bytes() != data:
                conflicts.append(target_rel + ": differs from the kit source")
                if target_rel.startswith(".agents/skills/") and target_rel.count("/") == 3:
                    collisions.append(target_rel.split("/")[2])
                continue
        else:
            writes.append((target_rel, data, source.path.stat().st_mode & 0o777))

    existing_text, existing_lines, blocks, block_problems = read_agents(target)
    if removal is not None and existing_text is not None and not block_problems:
        projected = remove_blocks(existing_text.splitlines(), blocks, removed_components)
        existing_text = "\n".join(projected)
        existing_text = existing_text + "\n" if existing_text.strip() else None
        _, blocks, block_problems = parse_agents(existing_text or "")
    if block_problems:
        conflicts.extend(block_problems)
    expected_blocks = {}
    for component_id in selected:
        component = registry.components[component_id]
        expected_blocks[component_id] = "\n".join(render_block(component, fragment) for fragment in component.fragments)
    unknown_blocks = [component_id for component_id in blocks if component_id not in registry.components]
    if unknown_blocks:
        conflicts.append("AGENTS.md has unregistered block(s): " + ", ".join(unknown_blocks))
    for component_id in selected:
        if component_id in blocks and blocks[component_id].text != expected_blocks[component_id]:
            conflicts.append("AGENTS.md block for " + component_id + " differs from the kit source")
    if manifest is not None:
        conflicts.extend(check_manifest_blocks(manifest, blocks, registry))

    if collisions:
        print("skill collisions (refusing to overwrite a different existing skill):", file=sys.stderr)
        for name in sorted(set(collisions)):
            print("  " + name, file=sys.stderr)
    if conflicts:
        print_problems(conflicts, "conflicts")
        print("nothing written", file=sys.stderr)
        return 1

    new_agents, block_changes = compose_agents(existing_text, blocks, expected_blocks, registry.order)
    if new_agents == existing_text:
        new_agents = None
    installed = [component_id for component_id in registry.order if component_id in set(
        (manifest.components if manifest is not None else []) + selected
    )]
    records = {record["path"]: record for record in (manifest.files if manifest is not None else [])}
    for target_rel, data in rendered.items():
        records[target_rel] = {
            "path": target_rel,
            "sha256": sha_bytes(data),
            "component": files[target_rel].component,
        }
    final_files = sorted(records.values(), key=lambda record: (
        registry.order.index(record["component"]) if record["component"] in registry.order else len(registry.order),
        record["path"],
    ))
    final_agents = new_agents if new_agents is not None else existing_text
    final_blocks = {}
    if final_agents is not None:
        _, parsed_blocks, _ = parse_agents(final_agents)
        final_blocks = {component_id: sha_text(block.text) for component_id, block in parsed_blocks.items()}
    created = manifest.agents_md_created if manifest is not None else existing_text is None
    new_manifest = Manifest(
        kit_revision=registry.revision,
        components=installed,
        mode=mode,
        agents_md_created=created,
        files=final_files,
        blocks=final_blocks,
    )

    print("planned: " + str(len(writes)) + " file(s), " + str(block_changes) + " block(s)")
    if not args.apply:
        print("dry run: pass --apply to write")
        return 0

    for target_rel, data, file_mode in writes:
        write_file(target, target_rel, data, file_mode)
    if new_agents is not None:
        write_file(target, AGENTS_REL, new_agents.encode("utf-8"))
    write_file(target, MANIFEST_REL, manifest_text(new_manifest, registry).encode("utf-8"))
    print("installed: " + str(len(writes)) + " file(s), " + str(block_changes) + " block(s)")
    return 0


def plan_removal(target: Path, manifest: Manifest, selected) -> tuple:
    prompts = []
    deletes = []
    for record in manifest.files_of(selected):
        destination = target / record["path"]
        if not destination.exists():
            prompts.append(record["path"] + ": recorded but missing")
            continue
        if destination.is_symlink() or not destination.is_file():
            prompts.append(record["path"] + ": recorded but not a regular file")
            continue
        if sha_bytes(destination.read_bytes()) != record["sha256"]:
            prompts.append(record["path"] + ": digest differs from the manifest")
            continue
        deletes.append(record["path"])
    existing_text, existing_lines, blocks, block_problems = read_agents(target)
    if block_problems:
        prompts.extend(block_problems)
    for component_id in selected:
        if component_id not in manifest.blocks:
            continue
        if component_id not in blocks:
            prompts.append("AGENTS.md: block for " + component_id + " is missing")
            continue
        if sha_text(blocks[component_id].text) != manifest.blocks[component_id]:
            prompts.append("AGENTS.md: block for " + component_id + " differs from the manifest digest")
    return deletes, blocks, existing_text, prompts


def remove_blocks(lines, blocks, selected) -> list:
    ranges = sorted(
        [(blocks[component_id].start, blocks[component_id].end) for component_id in selected if component_id in blocks],
        reverse=True,
    )
    for start, end in ranges:
        del lines[start : end + 1]
        if start > 0 and lines[start - 1].strip() == "":
            del lines[start - 1]
        if start < len(lines) and lines[start].strip() == "":
            del lines[start]
    while lines and lines[-1].strip() == "":
        lines.pop()
    return lines


def prune_directories(target: Path, relative_paths) -> None:
    candidates = set()
    for relative in relative_paths:
        parent = (target / relative).parent
        while parent != target and target in parent.parents:
            candidates.add(parent)
            parent = parent.parent
    for directory in sorted(candidates, key=lambda path: len(path.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def apply_removal(target: Path, manifest: Manifest, selected, deletes, blocks, existing_text, registry) -> None:
    for relative in deletes:
        (target / relative).unlink()
    remaining = [component_id for component_id in manifest.components if component_id not in selected]
    remaining_files = [record for record in manifest.files if record["component"] not in selected]
    remaining_blocks = {component_id: digest for component_id, digest in manifest.blocks.items() if component_id not in selected}
    if existing_text is not None:
        lines = existing_text.split("\n")
        if existing_text.endswith("\n") and lines and lines[-1] == "":
            lines = lines[:-1]
        lines = remove_blocks(lines, blocks, selected)
        text = "\n".join(lines)
        if text.strip() == "":
            if manifest.agents_md_created:
                (target / AGENTS_REL).unlink(missing_ok=True)
            else:
                write_file(target, AGENTS_REL, b"")
        else:
            write_file(target, AGENTS_REL, (text + "\n").encode("utf-8"))
    new_manifest = None
    if remaining:
        new_manifest = Manifest(
            kit_revision=manifest.kit_revision,
            components=remaining,
            mode=manifest.mode,
            agents_md_created=manifest.agents_md_created,
            files=remaining_files,
            blocks=remaining_blocks,
        )
    if new_manifest is None:
        (target / MANIFEST_REL).unlink(missing_ok=True)
    else:
        write_file(target, MANIFEST_REL, manifest_text(new_manifest, registry).encode("utf-8"))
    prune_directories(target, deletes)


def command_uninstall(args, source_root, registry) -> int:
    target = resolve_target(args.target)
    manifest = read_manifest(target)
    if manifest is None:
        print(MANIFEST_REL + " not found; nothing to uninstall", file=sys.stderr)
        return 1
    selected = list(manifest.components) if args.components is None else [
        item.strip() for item in args.components.split(",") if item.strip()
    ]
    if not selected or len(set(selected)) != len(selected):
        raise KitError("--components needs distinct installed component ids")
    unknown = [component_id for component_id in selected if component_id not in manifest.components]
    if unknown:
        print_problems(["component(s) not installed: " + ", ".join(unknown)], "invalid selection")
        return 1
    self_guard(args, target, source_root, "uninstall")
    describe(registry, selected, manifest.mode, "uninstall", target)
    deletes, blocks, existing_text, prompts = plan_removal(target, manifest, selected)
    if prompts:
        print_problems(prompts, "removal prompts")
        print("nothing deleted", file=sys.stderr)
        return 1
    print("planned: delete " + str(len(deletes)) + " file(s), remove " + str(len(selected)) + " block(s)")
    if not args.apply:
        print("dry run: pass --apply to delete")
        return 0
    apply_removal(target, manifest, selected, deletes, blocks, existing_text, registry)
    print("removed: " + str(len(deletes)) + " file(s), " + str(len(selected)) + " block(s)")
    return 0


def command_upgrade(args, registry: Registry, source_root) -> int:
    target = resolve_target(args.target)
    manifest = read_manifest(target)
    if manifest is None:
        print(MANIFEST_REL + " not found; install before upgrading", file=sys.stderr)
        return 1
    retired = set(manifest.components) - set(registry.components)
    if retired:
        if args.components is not None:
            raise KitError("component ownership changed; upgrade all components without --components")
        current_files = expand_files(registry, registry.order)
        replacements = set(manifest.components) - retired
        for component_id in sorted(retired):
            owners = {current_files[record["path"]].component
                      for record in manifest.files_of([component_id]) if record["path"] in current_files}
            if not owners:
                raise KitError("no replacement owns files of retired component " + component_id + "; uninstall it explicitly first")
            replacements.update(owners)
        selected = prerequisite_closure(registry, replacements)
        removing = list(manifest.components)
    else:
        selected = select_components(registry, args.components) if args.components else [
            component_id for component_id in registry.order if component_id in manifest.components
        ]
        removing = selected
    self_guard(args, target, source_root, "upgrade")
    mode = decide_mode(args, manifest)
    problems = tracked_roots_check(target, mode)
    if problems:
        print_problems(problems, "invalid installation mode")
        return 1
    remaining = [component_id for component_id in manifest.components if component_id not in removing]
    blocking = []
    for component_id in remaining:
        for prerequisite in registry.components[component_id].prerequisites:
            if prerequisite in selected:
                blocking.append(component_id + " still requires " + prerequisite + "; select it too or remove " + component_id + " first")
    if blocking:
        print_problems(blocking, "unmet prerequisites after removal")
        print("nothing changed", file=sys.stderr)
        return 1
    describe(registry, selected, mode, "upgrade", target)
    deletes, blocks, existing_text, prompts = plan_removal(target, manifest, removing)
    if prompts:
        print_problems(prompts, "removal prompts")
        print("nothing changed", file=sys.stderr)
        return 1
    preflight = _InstallRequest(target=str(target), components=",".join(selected), mode=mode, apply=False)
    result = command_install(preflight, registry, source_root, removal=(set(removing), set(deletes)))
    if result:
        print("upgrade preflight failed; nothing changed", file=sys.stderr)
        return result
    print("planned: validate removal of " + str(len(deletes)) + " file(s) and " + str(len(removing)) + " block(s), then reinstall")
    if not args.apply:
        print("dry run: pass --apply to upgrade")
        return 0
    apply_removal(target, manifest, removing, deletes, blocks, existing_text, registry)
    install_args = _InstallRequest(
        target=str(target),
        components=",".join(selected),
        mode=mode,
        apply=True,
    )
    return command_install(install_args, registry, source_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="Install, upgrade or remove se-tools kit components in a target repository.",
        epilog=(
            "Every subcommand is a dry run unless --apply is given. --self is se-tools-internal: "
            "uninstalling or upgrading the se-tools source repository additionally requires --confirm-self. "
            "See .agents/se/README.md for the adoption guide."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "uninstall", "upgrade"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--target", required=True, help="target repository directory")
        sub.add_argument("--components", help="comma-separated component ids; default all")
        sub.add_argument("--mode", choices=["tracked", "untracked"], help="installation mode")
        sub.add_argument("--apply", action="store_true", help="write the plan instead of printing it")
        sub.add_argument("--self", action="store_true", help="se-tools-internal: allow uninstall/upgrade of the source repository")
        sub.add_argument("--confirm-self", action="store_true", help="second confirmation for --self")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source_root = find_source_root(Path(__file__))
    try:
        if args.command == "install" and (args.self or args.confirm_self):
            raise KitError("--self and --confirm-self are only valid with uninstall or upgrade")
        registry = load_registry(source_root) if source_root is not None else None
        if args.command == "install":
            if registry is None:
                raise KitError("no kit source tree found; run the installer from the kit checkout")
            return command_install(args, registry, source_root)
        if args.command == "uninstall":
            return command_uninstall(args, source_root, registry)
        if args.command == "upgrade":
            if registry is None:
                raise KitError("no kit source tree found; run the installer from the kit checkout")
            return command_upgrade(args, registry, source_root)
        raise KitError("unknown command " + str(args.command))
    except KitError as exc:
        print("se-tools kit: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
