"""Document rules and orchestration for RFC records and evidence.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath
import re
import subprocess

from chain_data import (
    Chain,
    ChainError,
    folder_identity,
    is_request_id,
    load_chain,
    ref_basename,
    ref_dir,
    ref_title,
)
from document_syntax import (
    CHAIN_VALUE,
    SLUG,
    ZH_SECTIONS,
    local_key,
    local_value,
    link_path,
    parse_markdown,
    parse_evidence,
    parse_example_markers,
    parse_quoted_document,
    prose_lines,
)
from document_report import Finding
from document_sources import (
    DocumentSources,
    blob,
    git,
    safe_path,
    read_text,
    read_bytes,
    write_text,
    iter_notes,
    is_file,
    is_dir,
)

NOTES_REL = ".agents/notes"

LIFECYCLES = ("proposed", "implemented", "rejected", "archived")
FROZEN_LIFECYCLES = ("rejected", "archived")
CLASSES = ("architecture", "process", "feature", "bug-fix", "simplification", "testing")

LANG = {
    "en": {
        "title": re.compile(r"^# Decision: \S"),
        "title_expect": "# Decision: <title>",
        "status": {
            "proposed": re.compile(r"^Status: proposed$"),
            "implemented": re.compile(r"^Status: implemented$"),
            "rejected": re.compile(r"^Status: rejected — .+$"),
            "archived": re.compile(r"^Status: implemented$"),
        },
        "status_expect": {
            "proposed": "Status: proposed",
            "implemented": "Status: implemented",
            "rejected": "Status: rejected — <one-line reason>",
            "archived": "Status: implemented",
        },
        "archived_line": re.compile(r"^Archived: \d{4}-\d{2}-\d{2}$"),
        "archived_expect": "Archived: YYYY-MM-DD",
        "sections": {
            "proposed": (
                "## Problem",
                "## Proposal",
                "## Scope",
                "## Alternatives considered",
                "## Acceptance criteria",
                "## Risks",
            ),
            "implemented": (
                "## Problem",
                "## Decision",
                "## Scope",
                "## Alternatives considered",
                "## Consequences",
            ),
            "rejected": ("## Problem", "## Proposal"),
        },
        "sections_text": {
            "proposed": "Problem, Proposal, Scope, Alternatives considered, Acceptance criteria, Risks",
            "implemented": "Problem, Decision, Scope, Alternatives considered, Consequences",
            "rejected": "Problem, Proposal (body frozen)",
        },
        "banned": ("## Proposal", "## Plan", "## Migration plan", "## Acceptance criteria"),
        "markers": ("**Symptom**", "**Cost**"),
        "first_section": "## Problem",
    },
    "zh": {
        "title": re.compile(r"^# 决策：\S"),
        "title_expect": "# 决策：<标题>",
        "status": {
            "proposed": re.compile(r"^状态：提案中$"),
            "implemented": re.compile(r"^状态：已落地$"),
            "rejected": re.compile(r"^状态：已否决 — .+$"),
            "archived": re.compile(r"^状态：已落地$"),
        },
        "status_expect": {
            "proposed": "状态：提案中",
            "implemented": "状态：已落地",
            "rejected": "状态：已否决 — <一句话理由>",
            "archived": "状态：已落地",
        },
        "archived_line": re.compile(r"^归档：\d{4}-\d{2}-\d{2}$"),
        "archived_expect": "归档：YYYY-MM-DD",
        "sections": {
            "proposed": (
                "## 问题",
                "## 提案",
                "## 作用域",
                "## 考虑过的替代方案",
                "## 验收标准",
                "## 风险",
            ),
            "implemented": (
                "## 问题",
                "## 决策",
                "## 作用域",
                "## 考虑过的替代方案",
                "## 后果",
            ),
            "rejected": ("## 问题", "## 提案"),
        },
        "sections_text": {
            "proposed": "问题、提案、作用域、考虑过的替代方案、验收标准、风险",
            "implemented": "问题、决策、作用域、考虑过的替代方案、后果",
            "rejected": "问题、提案（正文冻结，不改写）",
        },
        "banned": ("## 提案", "## 计划", "## 迁移计划", "## 验收标准"),
        "markers": ("**现象**", "**代价**"),
        "first_section": "## 问题",
    },
}

ENUMS = {
    "Kind": ("issue", "question", "suggestion"),
    "Blocking": ("yes", "no"),
    "Disposition": ("accepted", "partially-accepted", "declined", "deferred"),
    "Resolution": ("resolved", "unresolved"),
}
SECTIONS = {
    "discuss": ("Problem", "Evidence", "Impact", "Suggestion"),
    "reply": ("Answer", "Reason", "Accepted part", "Unaccepted part"),
}


@dataclass
class Issue:
    rule: str
    line: int
    message: str


@dataclass
class Entry:
    title: str
    line: int
    meta: dict[str, str] = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=dict)

@dataclass
class Evidence:
    kind: str
    locale: str
    meta: dict[str, str] = field(default_factory=dict)
    entries: list[Entry] = field(default_factory=list)
    context: str = ""
    issues: list[Issue] = field(default_factory=list)

    def error(self, rule, line, message):
        self.issues.append(Issue(rule, line, message))


def substantive(value):
    text = value.strip().strip("`").strip()
    if not text or re.fullmatch(
        r"(?:TODO|TBD|N/?A|none|无|待定|待补充|待填写|\.+|…+|[<>\[\]_-]+)", text, re.I
    ):
        return False
    return bool(re.search(r"\w", text))


def validate_response(doc, entry, source=None):
    m, s, loc = entry.meta, entry.sections, doc.locale
    disp, resolved = m.get("Disposition"), m.get("Resolution")
    none = local_value("none", loc)
    accepted, unaccepted = s.get("Accepted part", ""), s.get("Unaccepted part", "")
    if disp == "accepted":
        valid = substantive(accepted) and unaccepted == none
    elif disp == "partially-accepted":
        valid = substantive(accepted) and substantive(unaccepted)
    else:
        valid = accepted == none and substantive(unaccepted)
    if not valid:
        doc.error("E5", entry.line, "Accepted/Unaccepted part does not match disposition")
    if disp in ("deferred", "partially-accepted") and resolved != "unresolved":
        doc.error("E5", entry.line, "Deferred/partial responses remain unresolved")
    reason = s.get("Reason", "")
    sep = "：" if loc == "zh" else ": "
    if disp == "declined":
        prefix = local_key("Decline-Class", loc) + sep
        choices = "|".join(
            re.escape(local_value(v, loc)) for v in ("out-of-scope", "invalid", "tradeoff")
        )
        match = re.match(rf"{prefix}({choices})(?=\s|[.。;；]|$)", reason)
        if not match or not substantive(reason[match.end() :].strip(" .。;；\n")):
            doc.error("E5", entry.line, "Decline-Class must start Reason, followed by explanation")
    if disp == "deferred":
        for key in ("Owner", "Trigger"):
            prefix = local_key(key, loc) + sep
            rows = [t[len(prefix) :] for t in reason.splitlines() if t.startswith(prefix)]
            if len(rows) != 1 or not substantive(rows[0]):
                doc.error("E5", entry.line, f"Deferred reason needs exactly one nonempty {key}")
        explanation = "\n".join(
            t
            for t in reason.splitlines()
            if not any(t.startswith(local_key(k, loc) + sep) for k in ("Owner", "Trigger"))
        )
        if not substantive(explanation):
            doc.error("E5", entry.line, "Deferral requires explanation")
    if source:
        if m.get("Kind") != source.meta.get("Kind", "issue"):
            doc.error("E5", entry.line, "Kind must equal source finding Kind")
        if disp == "declined" and source.meta.get("Blocking") == "yes" and resolved != "unresolved":
            doc.error("E5", entry.line, "Declined blocking finding remains unresolved")
        if disp == "declined":
            quotes = re.findall(r'["“「`]([^"”」`\n]+)["”」`]', reason + "\n" + unaccepted)
            source_text = "\n".join(source.sections.values()) + "\n" + source.title
            if not any(q.strip() and q in source_text for q in quotes):
                doc.error("E5", entry.line, "Decline requires short exact source quotation")


def identity(doc):
    return doc.meta, [e.meta for e in doc.entries]


def validate_metadata(fields, keys, locale, doc, rule, start):
    found = {}
    if len(fields) != len(keys):
        doc.error(rule, start, f"Expected only ordered fields: {', '.join(keys)}")
    for key, item in zip(keys, fields):
        prefix = local_key(key, locale) + ("：" if locale == "zh" else ": ")
        if item.key != key or not substantive(item.value or ""):
            doc.error(rule, item.line, f"Expected nonempty {prefix}<value>")
            continue
        value = item.value
        if key in ENUMS:
            allowed = {local_value(v, locale): v for v in ENUMS[key]}
            if value not in allowed:
                doc.error(rule, item.line, f"{key}: expected {list(allowed)}")
            value = allowed.get(value, value)
        elif key == "Recorder" and value == local_value("self", locale):
            value = "self"
        found[key] = value
    return found


def validate_evidence_document(text, kind, locale, *, sample=False):
    """Apply evidence rules to the shared syntax tree, also used by typed samples."""
    del sample
    syntax = parse_evidence(text, kind, locale)
    lines = syntax.markdown.lines
    doc = Evidence(kind, locale)
    title = (
        ("# Discussion: " if kind == "discuss" else "# Reply: ")
        if locale == "en"
        else ("# 讨论：" if kind == "discuss" else "# 回复：")
    )
    if not lines or not lines[0].startswith(title) or not substantive(lines[0][len(title) :]):
        doc.error("E1", 1, f"Expected {title}<title>")
    if len(lines) < 4 or lines[1] or lines[3]:
        doc.error("E1", 2, "Expected blank lines 2 and 4")
    switch = (
        r"English \| \[中文\]\(/[^)]+\.zh\.md\)"
        if locale == "en"
        else r"\[English\]\(/[^)]+(?<!\.zh)\.md\) \| 中文"
    )
    if len(lines) < 3 or not re.fullmatch(switch, lines[2]):
        doc.error("E1", 3, "Expected localized repository-root language switcher")
    names = ("Context", "Findings") if kind == "discuss" else ("Responses",)
    expected = ["## " + (ZH_SECTIONS[n] if locale == "zh" else n) for n in names]
    rule = "E2" if kind == "discuss" else "E5"
    if [heading for _, heading in syntax.h2] != expected:
        doc.error(rule, 1, f"Expected only {expected}")
    doc.meta = validate_metadata(syntax.header, ["Chain", "Author"], locale, doc, "E1", 5)
    if CHAIN_VALUE.fullmatch(doc.meta.get("Chain", "")) is None:
        doc.error("E1", 5, "Chain must be <request-id>/<thread-slug>")
    doc.context = syntax.context
    if kind == "discuss" and syntax.h2 and not substantive(doc.context):
        doc.error("E2", syntax.h2[0][0] + 1, "Context must contain substantive text")
    if not syntax.entries:
        doc.error(rule, syntax.body_start + 1, "At least one finding/response required")
    if syntax.entries and syntax.leading_body:
        doc.error(rule, syntax.body_start + 2, "No stray prose before first entry")
    allowed = {0, *(i for i, _ in syntax.h2)}
    seen = set()
    for item in syntax.entries:
        expected_sections = [
            "#### " + (ZH_SECTIONS[n] if locale == "zh" else n) for n in SECTIONS[kind]
        ]
        if [section.heading for section in item.sections] != expected_sections:
            doc.error(rule, item.index + 1, f"Expected exactly {expected_sections}")
        allowed.add(item.index)
        allowed.update(section.index for section in item.sections)
        fields = (
            ["Finding-ID", "Kind", "Blocking"]
            if kind == "discuss"
            else ["Finding-ID", "Kind", "Disposition", "Resolution"]
        )
        meta = validate_metadata(item.fields, fields, locale, doc, rule, item.index + 2)
        identifier = meta.get("Finding-ID", "")
        if not re.fullmatch(SLUG, identifier) or identifier in seen:
            doc.error(
                "E4" if kind == "reply" else "E2",
                item.index + 2,
                f"Invalid or duplicate Finding-ID: {identifier}",
            )
        seen.add(identifier)
        if not substantive(item.title):
            doc.error(rule, item.index + 1, "Entry title must be substantive localized text")
        entry = Entry(item.title, item.index + 1, meta)
        for position, section in enumerate(item.sections):
            if position < len(SECTIONS[kind]):
                entry.sections[SECTIONS[kind][position]] = section.body
            if not substantive(section.body) and not (
                kind == "reply"
                and position in (2, 3)
                and section.body == local_value("none", locale)
            ):
                doc.error(rule, section.index + 1, "Section requires substantive text, not a placeholder")
        doc.entries.append(entry)
        if kind == "reply":
            validate_response(doc, entry)
    for index, heading in syntax.markdown.headings:
        if index not in allowed:
            doc.error(rule, index + 1, f"Unexpected heading: {heading}")
    return doc

@dataclass
class Example:
    identifier: str
    kind: str
    mode: str
    line: int
    body: str
    finding_ids: tuple = ()


def validate_examples(text, locale, *, required=False):
    issues, examples = [], []
    opened = None
    seen = set()
    lines = text.splitlines()
    for marker in parse_example_markers(text):
        index = marker.index
        if marker.operation == "begin":
            if opened or marker.identifier in seen:
                issues.append(Issue("X2", index + 1, "Examples cannot nest, overlap or reuse IDs"))
            else:
                opened = marker
                seen.add(marker.identifier)
        elif marker.operation == "end":
            if opened is None or marker.identifier != opened.identifier:
                issues.append(Issue("X2", index + 1, "End marker must match the open example ID"))
            else:
                start = opened.index
                body = "\n".join(lines[start + 1 : index]).strip()
                example = Example(opened.identifier, opened.kind, opened.mode, start + 1, body)
                examples.append(example)
                opened = None
                clean = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
                placeholder = re.fullmatch(
                    r"[<>`\s]*(?:[0-9a-f]{40}|[0-9a-f]{64}|C\d|SHA\S*)[<>`\s]*", clean, re.I
                )
                if (
                    not substantive(clean)
                    or placeholder
                    or re.fullmatch(r"`?<[^<>\n]*(?:sha|commit)[^<>\n]*>`?", clean, re.I)
                    or re.fullmatch(r"\.*\s*example content\s*\.*", clean, re.I)
                ):
                    issues.append(
                        Issue(
                            "X3",
                            start + 1,
                            "Example needs substantive content beyond syntax or placeholders",
                        )
                    )
                if example.kind in ("discuss", "reply"):
                    if any(line.strip() and not line.startswith(">") for line in body.splitlines()):
                        issues.append(
                            Issue("X4", start + 1, "Typed sample must contain one quoted document")
                        )
                    doc = validate_evidence_document(
                        parse_quoted_document(body), example.kind, locale, sample=True
                    )
                    for issue in doc.issues:
                        issues.append(Issue("X4", start + issue.line, issue.message))
                    example.finding_ids = tuple(e.meta.get("Finding-ID") for e in doc.entries)
                elif example.kind == "counterexample" and not re.search(
                    r"\b[EX][1-7]\b|\b(?:pass|fail)\b|通过|失败", clean, re.I
                ):
                    issues.append(
                        Issue(
                            "X4",
                            start + 1,
                            "Counterexample must declare its expected check outcome",
                        )
                    )
        else:
            issues.append(
                Issue(
                    "X2", index + 1, "Malformed example marker; exact id/kind/mode order required"
                )
            )
    if opened:
        issues.append(Issue("X2", opened.index + 1, "Unclosed example"))
    if required and not examples:
        issues.append(
            Issue("X1", 1, "New or changed proposal requires at least one marked example")
        )
    return issues, examples


def example_signature(examples):
    return [(e.identifier, e.kind, e.mode, e.finding_ids) for e in examples]


BT = chr(96)
MARKER = re.compile(rf"{BT}Chain\s+({SLUG})(?:\s+(L\d+(?:-L\d+)?))?{BT}")
MARKER_RANGE = re.compile(r"L(\d+)(?:-L(\d+))?")


def _is_ancestor(root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
    )
    return result.returncode == 0


def _blob_text(repo: Path, commit: str, path: str) -> str:
    if not safe_path(path):
        raise ValueError(f"unsafe ref path {path!r}")
    if git(repo, "cat-file", "-t", commit).strip() != b"commit":
        raise ValueError(f"{commit} is not a commit")
    if git(repo, "cat-file", "-t", f"{commit}:{path}").strip() != b"blob":
        raise ValueError(f"{commit}:{path} is not a blob")
    return git(repo, "show", f"{commit}:{path}").decode("utf-8")


def evidence_stem(path: Path) -> tuple[str, str] | None:
    name = path.name
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


def validate_chain(root: Path, repo: Path, folder: Path, chain: Chain, paths: list[Path]):
    """Validate one parsed chain against its folder and the repository history."""
    issues: list[tuple[Path, Issue]] = []
    chain_path = folder / "chain.yaml"
    lifecycle = folder.relative_to(root).parts[2]
    if chain.version == 1 and lifecycle in FROZEN_LIFECYCLES:
        issues.append((chain_path, Issue("C1", 1, "frozen chain files must be version 2; run migrate_chain.py")))
    kinds: dict[str, set[str]] = {}
    for path in paths:
        stem = evidence_stem(path)
        if stem is not None:
            kinds.setdefault(stem[0], set()).add(stem[1])
    discuss_files = kinds.get("discuss", set())
    reply_files = kinds.get("reply", set())
    threads = chain.threads
    for slug in sorted(discuss_files - set(threads)):
        issues.append((folder, Issue("C2", 1, f"discuss-{slug}.md has no thread entry")))
    for slug in sorted(set(threads) - discuss_files):
        issues.append((folder, Issue("C2", 1, f"thread {slug!r} has no discuss-{slug}.md")))
    for slug in sorted(reply_files):
        entry = threads.get(slug)
        if entry is None or entry.reply is None:
            issues.append((folder, Issue("C2", 1, f"reply-{slug}.md exists without a reply block")))
    for slug, entry in threads.items():
        if entry.reply is not None and slug not in reply_files:
            issues.append((folder, Issue("C2", 1, f"thread {slug!r} declares a reply block but has no reply-{slug}.md")))
    folder_id = folder_identity(folder.relative_to(root).as_posix())
    for slug, entry in threads.items():
        for kind, block in (("discuss", entry.discuss), ("reply", entry.reply)):
            if block is None:
                continue
            if "proposal" not in block:
                issues.append((chain_path, Issue("C2", 1, f"{slug}/{kind} must contain a proposal ref")))
            for name, ref in block.items():
                rule = "E3" if name == "proposal" else "C3"
                if name != "proposal" and not (name.startswith("discuss-") or name.startswith("reply-")):
                    issues.append((chain_path, Issue("C3", 1, f"{slug}/{kind}: ref {name!r} is not a local document stem")))
                    continue
                if ref.zh is not None:
                    if ref.zh.commit != ref.en.commit:
                        issues.append((chain_path, Issue("C3", 1, f"{slug}/{kind}/{name}: en and zh commits differ")))
                    pairs = [("en", ref.en), ("zh", ref.zh)]
                else:
                    try:
                        pairs = [("en", ref.en), ("zh", ref.locale_coord("zh"))]
                    except ChainError as exc:
                        issues.append((chain_path, Issue(rule, 1, f"{slug}/{kind}/{name}: {exc}")))
                        continue
                texts = {}
                for locale, coord in pairs:
                    try:
                        texts[locale] = _blob_text(repo, coord.commit, coord.path)
                    except ValueError as exc:
                        texts[locale] = None
                        issues.append((chain_path, Issue(rule, 1, f"{slug}/{kind}/{name}: {exc}")))
                for locale, coord in pairs:
                    text = texts.get(locale)
                    if text is None:
                        continue
                    if locale == "zh" and not coord.path.endswith(".zh.md"):
                        issues.append((chain_path, Issue(rule, 1, f"{slug}/{kind}/{name}.zh: path must end with .zh.md")))
                        continue
                    if locale == "en" and (coord.path.endswith(".zh.md") or not coord.path.endswith(".md")):
                        issues.append((chain_path, Issue(rule, 1, f"{slug}/{kind}/{name}.en: path must be an English .md file")))
                        continue
                    basename = ref_basename(coord.path, name)
                    expected_name = name + (".zh.md" if locale == "zh" else ".md")
                    if basename != expected_name:
                        issues.append((chain_path, Issue(rule, 1, f"{slug}/{kind}/{name}.{locale}: path basename must be {expected_name}")))
                    if ref_dir(coord.path, name) != folder_id:
                        issues.append((chain_path, Issue(rule, 1, f"{slug}/{kind}/{name}.{locale}: path is outside this request folder")))
                    try:
                        title = ref_title(name, locale)
                    except ValueError as exc:
                        issues.append((chain_path, Issue("C3", 1, str(exc))))
                        continue
                    if not text.startswith(title):
                        issues.append((chain_path, Issue(rule, 1, f"{slug}/{kind}/{name}.{locale}: blob is not a {title.strip()!r} document")))
                if not _is_ancestor(repo, ref.en.commit):
                    issues.append((chain_path, Issue("C3", 1, f"{slug}/{kind}/{name}: commit is not an ancestor of HEAD")))
    return issues, chain


def validate_chain_folder(root: Path, repo: Path, folder: Path, paths: list[Path]):
    chain_path = folder / "chain.yaml"
    if not is_file(chain_path):
        return [(folder, Issue("C1", 1, "missing chain.yaml for a folder with discuss/reply evidence"))], None
    try:
        chain = load_chain(folder)
    except ChainError as exc:
        return [(chain_path, Issue("C1", 1, str(exc)))], None
    return validate_chain(root, repo, folder, chain, paths)


def validate_markers(path: Path, block: dict, repo: Path) -> list[tuple[Path, Issue]]:
    locale = "zh" if path.name.endswith(".zh.md") else "en"
    issues: list[tuple[Path, Issue]] = []
    for number, line in prose_lines(read_text(path)):
        for match in MARKER.finditer(line):
            name, span_text = match[1], match[2]
            if name not in block:
                issues.append((path, Issue("C4", number, f"marker cites unknown ref {name!r}")))
                continue
            ref = block[name]
            try:
                coord = ref.locale_coord(locale)
                text = _blob_text(repo, coord.commit, coord.path)
            except ValueError as exc:
                issues.append((path, Issue("C4", number, f"marker ref {name!r} cannot be resolved: {exc}")))
                continue
            if span_text is None:
                continue
            match_range = MARKER_RANGE.fullmatch(span_text)
            start = int(match_range[1])
            end = int(match_range[2]) if match_range[2] is not None else start
            count = len(text.splitlines())
            if start < 1 or end < start or end > count:
                issues.append((path, Issue("C4", number, f"marker range {span_text} is outside {name!r} ({count} lines)")))
    return issues


def validate_evidence_relations(root: Path, paths, *, git_root=None):
    repo = git_root or root
    issues: list[tuple[Path, Issue]] = []
    overview: list[str] = []
    docs = {}
    for path in paths:
        locale = "zh" if path.name.endswith(".zh.md") else "en"
        kind = "discuss" if path.name.startswith("discuss-") else "reply"
        doc = validate_evidence_document(read_text(path), kind, locale)
        docs[path] = doc
        issues.extend((path, issue) for issue in doc.issues)
        match = CHAIN_VALUE.fullmatch(doc.meta.get("Chain", ""))
        if match is not None:
            request, thread = match.groups()
            stem = evidence_stem(path)
            if request != path.parent.name:
                issues.append((path, Issue("E3", 5, f"Chain request {request!r} does not match folder {path.parent.name!r}")))
            if stem is not None and stem[1] != thread:
                issues.append((path, Issue("E3", 5, f"Chain thread {thread!r} does not match the filename")))
    chains = {}
    for folder in sorted({path.parent for path in paths}):
        folder_paths = [path for path in paths if path.parent == folder]
        chain_issues, chain = validate_chain_folder(root, repo, folder, folder_paths)
        issues.extend(chain_issues)
        chains[folder] = chain
    for path, doc in docs.items():
        kind = doc.kind
        locale = doc.locale
        chain = chains.get(path.parent)
        block = None
        if chain is not None:
            stem = evidence_stem(path)
            if stem is not None and stem[1] in chain.threads:
                entry = chain.threads[stem[1]]
                block = entry.discuss if kind == "discuss" else entry.reply
        if kind == "reply":
            discuss_path = path.with_name(path.name.replace("reply-", "discuss-", 1))
            if is_file(discuss_path):
                discuss_doc = docs.get(discuss_path)
                if discuss_doc is None:
                    discuss_doc = validate_evidence_document(read_text(discuss_path), "discuss", locale)
                    docs[discuss_path] = discuss_doc
                originals = {entry.meta.get("Finding-ID") for entry in discuss_doc.entries}
                replies = {entry.meta.get("Finding-ID") for entry in doc.entries}
                if originals != replies or len(replies) != len(doc.entries):
                    issues.append((path, Issue("E4", 1, f"Response IDs must equal the current discussion IDs; missing={sorted(originals - replies)}, extra={sorted(replies - originals)}")))
        if block is not None:
            issues.extend(validate_markers(path, block, repo))
    for path, doc in docs.items():
        if doc.locale != "en":
            continue
        sibling = path.with_name(path.stem + ".zh.md")
        other = docs.get(sibling)
        if other is None:
            continue
        if identity(doc) != identity(other):
            issues.append((path, Issue("E6", 1, "Normalized bilingual metadata, IDs or states differ")))
    for path, doc in docs.items():
        if doc.kind != "discuss":
            continue
        reply_path = path.with_name(path.name.replace("discuss-", "reply-", 1))
        reply = docs.get(reply_path)
        responses = {entry.meta.get("Finding-ID"): entry for entry in reply.entries} if reply else {}
        for entry in doc.entries:
            identifier = entry.meta.get("Finding-ID", "?")
            response = responses.get(identifier)
            disposition = response.meta.get("Disposition", "unanswered") if response else "unanswered"
            resolution = response.meta.get("Resolution", "unanswered") if response else "unanswered"
            overview.append(
                f"{path.relative_to(root)} id={identifier} kind={entry.meta.get('Kind')} blocking={entry.meta.get('Blocking')} disposition={disposition} author-resolution={resolution} disagreement={'recorded' if disposition in ('partially-accepted', 'declined') else 'not-assessed'} verification=unverified reply={reply_path.relative_to(root) if reply else 'missing'}"
            )
    return issues, overview


def language_of(name: str) -> str:
    return "zh" if name.endswith(".zh.md") else "en"


def sibling_of(note: Path) -> Path:
    name = note.name
    if name.endswith(".zh.md"):
        return note.with_name(name[: -len(".zh.md")] + ".md")
    return note.with_name(name[: -len(".md")] + ".zh.md")


def check_path(note: Path, root: Path) -> list[Finding]:
    findings = []
    parts = note.relative_to(root / NOTES_REL).parts
    if len(parts) not in (3, 4):
        return [
            Finding(
                "P1",
                note,
                None,
                f"Path segments = {len(parts)}",
                "Request folder or legacy flat record",
                "Correct the path according to P1",
            )
        ]
    if parts[1] not in CLASSES:
        findings.append(
            Finding(
                "P3",
                note,
                None,
                f"class = {parts[1]!r}",
                " | ".join(CLASSES),
                "Select a class according to P3",
            )
        )
    name = parts[2]
    if len(parts) == 3:
        name = name.removesuffix(".md").removesuffix(".zh")
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})-(.*)", name)
    if match is None:
        findings.append(
            Finding(
                "P4",
                note,
                None,
                f"Topic name = {name!r}",
                "yyyy-mm-dd-slug",
                "Provide the topic date and slug",
            )
        )
        return findings
    try:
        date(int(match[1]), int(match[2]), int(match[3]))
    except ValueError:
        findings.append(
            Finding(
                "P4",
                note,
                None,
                f"Invalid date: {name[:10]}",
                "Valid calendar date",
                "Correct the date",
            )
        )
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", match[4]):
        findings.append(
            Finding(
                "P5",
                note,
                None,
                f"slug = {match[4]!r}",
                "Lowercase letters and digits separated by single hyphens",
                "Correct the topic slug",
            )
        )
    return findings


def check_header(note: Path, lifecycle: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    lang = LANG[language_of(note.name)]

    if not lang["title"].match(lines[0] if lines else ""):
        findings.append(
            Finding(
                "H1",
                note,
                1,
                repr(lines[0] if lines else "<empty file>"),
                lang["title_expect"],
                f"Set line 1 to `{lang['title_expect']}`",
            )
        )
    if len(lines) > 1 and lines[1] != "":
        findings.append(
            Finding(
                "H2",
                note,
                2,
                repr(lines[1]),
                "Blank line",
                "Leave line 2 blank",
            )
        )

    sibling = sibling_of(note)
    switcher = lines[2] if len(lines) > 2 else ""
    if "]( " not in switcher and (sibling.name not in switcher or "](" not in switcher):
        findings.append(
            Finding(
                "H3",
                note,
                3,
                repr(switcher) if switcher else "<missing>",
                f"Language switcher linking to {sibling.name}",
                f"On line 3, write `English | [中文](<sibling-path>)` or `[English](<sibling-path>) | 中文`",
            )
        )

    if len(lines) > 3 and lines[3] != "":
        findings.append(
            Finding(
                "H4",
                note,
                4,
                repr(lines[3]),
                "Blank line",
                "Leave line 4 blank",
            )
        )

    status_index = 4
    if len(lines) <= status_index:
        findings.append(
            Finding(
                "H5",
                note,
                None,
                "<record too short>",
                "Status line on line 5",
                "Complete the header: title / blank / language switcher / blank / status",
            )
        )
        return findings

    status_lines = [
        (i, line)
        for i, line in parse_markdown("\n".join(lines)).prose
        if line.startswith("Status:") or line.startswith("状态：")
    ]
    if len(status_lines) != 1:
        findings.append(
            Finding(
                "H6",
                note,
                None,
                f"Found {len(status_lines)} status lines"
                + (f"(lines {', '.join(str(i) for i, _ in status_lines)})" if status_lines else ""),
                "Exactly one status line in the document, on line 5",
                "Remove extra status lines; keep the one on line 5",
            )
        )
    else:
        line_no, text = status_lines[0]
        if line_no != status_index + 1:
            findings.append(
                Finding(
                    "H6",
                    note,
                    line_no,
                    f"Status line is on line {line_no}",
                    "Status line must be on line 5",
                    "Move the status line to line 5",
                )
            )
        pattern = lang["status"].get(lifecycle)
        if pattern is not None and not pattern.match(text):
            findings.append(
                Finding(
                    "H5",
                    note,
                    line_no,
                    repr(text),
                    lang["status_expect"][lifecycle],
                    f"Use `{lang['status_expect'][lifecycle]}` to match the {lifecycle}/ directory",
                )
            )

    body_line = status_index + 1  # 0-based index of the line after the status line
    if lifecycle == "archived":
        archive_line = lines[body_line] if len(lines) > body_line else ""
        if not lang["archived_line"].match(archive_line):
            findings.append(
                Finding(
                    "H7",
                    note,
                    body_line + 1,
                    repr(archive_line) if archive_line else "<missing>",
                    lang["archived_expect"],
                    f"Insert `{lang['archived_expect']}` immediately after the status line",
                )
            )
        body_line += 1
    elif len(lines) > body_line and (
        lines[body_line].startswith("Archived:") or lines[body_line].startswith("归档：")
    ):
        findings.append(
            Finding(
                "H8",
                note,
                body_line + 1,
                repr(lines[body_line]),
                "Only archived records may have an archive line",
                "Remove the line",
            )
        )

    if len(lines) > body_line and lines[body_line] != "":
        findings.append(
            Finding(
                "H4",
                note,
                body_line + 1,
                repr(lines[body_line]),
                "Blank line",
                f"Leave line {body_line + 1} blank",
            )
        )
    return findings


def check_sections(note: Path, lifecycle: str, lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    lang = LANG[language_of(note.name)]
    first = lang["first_section"]
    syntax = parse_markdown("\n".join(lines))

    sections = [(i, line.strip()) for i, line in syntax.prose if line.startswith("## ")]
    names = [name for _, name in sections]

    if not names:
        findings.append(
            Finding(
                "S1",
                note,
                None,
                "No `##` sections found",
                f"First section must be `{first}`",
                "Add the sections required by contract section 3",
            )
        )
        return findings

    if names[0] != first:
        findings.append(
            Finding(
                "S1",
                note,
                sections[0][0],
                repr(names[0]),
                f"First section must be `{first}`",
                f"Move `{first}` to the beginning; state the problem before the solution",
            )
        )

    required = lang["sections"].get(lifecycle)
    if required is not None:
        missing = [name for name in required if name not in names]
        if missing:
            rule = "S2" if lifecycle == "proposed" else "S3" if lifecycle == "implemented" else "S4"
            findings.append(
                Finding(
                    rule,
                    note,
                    None,
                    f"Missing sections: {', '.join(missing)}",
                    f"{lifecycle}/ requires: {lang['sections_text'][lifecycle]}",
                    "Add missing sections; explain unknown content using the documented dated not-recorded marker",
                )
            )

    if lifecycle == "implemented":
        banned = [name for name in names if name in lang["banned"]]
        if banned:
            findings.append(
                Finding(
                    "S7",
                    note,
                    None,
                    f"Proposal-stage sections found: {', '.join(banned)}",
                    "Proposal-stage sections are not allowed under implemented/",
                    "Rewrite `## Proposal` / `## 提案` as a present-tense decision section; "
                    "fold acceptance criteria and risks into `## Consequences` / `## 后果`",
                )
            )

    scope_heading = "## Scope" if language_of(note.name) == "en" else "## 作用域"
    body = syntax.section_body(scope_heading)
    if body is not None and not body.strip():
        findings.append(
            Finding(
                "S5",
                note,
                None,
                f"`{scope_heading}` is empty",
                "One sentence defining the scope",
                "State what the decision governs (for example, all request-handling paths); "
                "if the scope cannot be defined, revisit the problem before recording a decision",
            )
        )

    alt_heading = (
        "## Alternatives considered" if language_of(note.name) == "en" else "## 考虑过的替代方案"
    )
    alternatives = syntax.section_body(alt_heading)
    if alternatives is not None:
        stripped = alternatives.strip()
        if not stripped:
            findings.append(
                Finding(
                    "S6",
                    note,
                    None,
                    f"`{alt_heading}` is empty",
                    "List real alternatives and why they lost, or use the documented dated not-recorded marker",
                    "Add alternatives; if none were considered, use the documented not-recorded marker with the current date. "
                    "A decision that omits the alternatives it defeated invites repeated reconsideration",
                )
            )
        elif len(stripped) < 20 and not re.search(r"未记录（\d{4}-\d{2}-\d{2}）", stripped):
            findings.append(
                Finding(
                    "S6",
                    note,
                    None,
                    f"Alternatives section is too short: {stripped!r}",
                    "One paragraph per real alternative: conclusion and reason for rejection",
                    "Explain the alternatives; if none were considered, use the documented dated not-recorded marker",
                )
            )

    problem = syntax.section_body(first)
    if problem is not None:
        missing_markers = [m for m in lang["markers"] if m not in problem]
        if missing_markers:
            findings.append(
                Finding(
                    "C1",
                    note,
                    None,
                    f"Problem section is missing {', '.join(missing_markers)}",
                    f"Separate {lang['markers'][0]} (the event that exposed the problem) from "
                    f"{lang['markers'][1]} (what is lost if it remains unsolved)",
                    "Add the missing layer. A symptom without a cost does not justify a decision",
                )
            )
    return findings


def apply_fix(note: Path, lifecycle: str, lines: list[str]) -> bool:
    """Rewrite the status line to match the lifecycle. The only mechanical fix."""
    lang = LANG[language_of(note.name)]
    expectation = lang["status_expect"].get(lifecycle)
    if expectation is None:
        return False
    prefix = "Status:" if language_of(note.name) == "en" else "状态："
    for index, line in enumerate(lines):
        if line.startswith(prefix) and line != expectation:
            lines[index] = expectation
            write_text(note, "\n".join(lines))
            return True
    return False


def check_tree(root: Path, changed: set[str], *, git_root=None, fix=False):
    findings = []
    total = 0
    notes_dir = root / NOTES_REL
    examples = {}
    evidence = []
    archived_evidence = []
    folders = set()
    chain_files = set()
    for note in iter_notes(notes_dir):
        rel = note.relative_to(notes_dir)
        parts = rel.parts
        if len(parts) >= 3 and is_dir(note):
            if len(parts) == 3:
                folders.add(note)
            elif len(parts) > 3:
                findings.append(
                    Finding("P1", note, None, "Nested directory", "Only the triplets defined by the contract are allowed in a request folder", "Remove the nested directory")
                )
            continue
        if not is_file(note):
            continue
        lifecycle = parts[0]
        if lifecycle not in LIFECYCLES:
            findings.append(Finding("P2", note, None, f"Unknown lifecycle {lifecycle}", str(LIFECYCLES), "Correct the lifecycle directory"))
        if len(parts) >= 4:
            allowed = re.fullmatch(
                r"(?:proposal|(?:discuss|reply)-[a-z0-9]+(?:-[a-z0-9]+)*)(?:\.zh\.md|\.md|\.i18n\.yaml)|chain\.yaml",
                note.name,
            )
            if len(parts) != 4 or not allowed:
                findings.append(Finding("P1", note, None, "Unknown file or nested path", "proposal/discuss-<slug>/reply-<slug> triplets or chain.yaml", "Follow the folder contract"))
                continue
            if note.name == "chain.yaml":
                chain_files.add(note.parent)
                continue
        if not note.name.endswith(".md"):
            continue
        if len(parts) == 4 and note.name not in ("proposal.md", "proposal.zh.md"):
            if lifecycle == "archived":
                archived_evidence.append(note)
            else:
                evidence.append(note)
            continue
        if language_of(note.name) == "en":
            total += 1
        lines = read_text(note).splitlines()
        findings.extend(check_path(note, root))
        findings.extend(check_header(note, lifecycle, lines))
        if lifecycle != "archived":
            findings.extend(check_sections(note, lifecycle, lines))
            required = lifecycle == "proposed" and str(note.relative_to(root)) in changed
            errors, samples = validate_examples(read_text(note), language_of(note.name), required=required)
            examples[note] = samples
            findings.extend(Finding(i.rule, note, i.line, i.message, "X1–X5 example contract", "Correct the markers and example structure") for i in errors)
        if fix:
            apply_fix(note, lifecycle, lines)
    names: dict[str, list[Path]] = {}
    for folder in sorted(folders):
        names.setdefault(folder.name, []).append(folder)
    for name in sorted(names):
        group = names[name]
        if len(group) > 1:
            for folder in group:
                findings.append(
                    Finding("C0", folder, None, f"duplicate request folder name {name!r}: " + ", ".join(str(item.relative_to(root)) for item in group), "Request folder names must be unique across lifecycles and classes so a full chain ID resolves", "Rename or merge the duplicated request folders")
                )
    for folder in sorted(folders):
        for name in ("proposal.md", "proposal.zh.md", "proposal.i18n.yaml"):
            if not is_file(folder / name):
                findings.append(Finding("P1", folder, None, f"Missing {name}", "A complete proposal triplet in every request folder", "Complete the record"))
    evidence_folders = {path.parent for path in evidence} | {path.parent for path in archived_evidence}
    for folder in sorted(chain_files - evidence_folders):
        findings.append(Finding("C1", folder / "chain.yaml", None, "chain.yaml exists without discuss/reply evidence", "chain.yaml only in folders with evidence", "Remove the file or add the evidence"))
    for note, samples in examples.items():
        if language_of(note.name) == "en":
            other = sibling_of(note)
            if other in examples and example_signature(samples) != example_signature(examples[other]):
                findings.append(Finding("X5", note, None, "Bilingual example identities or finding IDs differ", "Matching ID/kind/mode/order/sample finding IDs", "Synchronize both language examples"))
    errors, overview = validate_evidence_relations(root, evidence, git_root=git_root)
    findings.extend(
        Finding(issue.rule, path, issue.line, issue.message, "E1–E6 / C evidence contract", "Correct the evidence according to the contract") for path, issue in errors
    )
    repo = git_root or root
    archived_issues: list[tuple[Path, Issue]] = []
    archived_chains = {}
    for folder in sorted({path.parent for path in archived_evidence}):
        folder_paths = sorted(path for path in folder.iterdir() if path.is_file())
        chain_issues, chain = validate_chain_folder(root, repo, folder, folder_paths)
        archived_issues.extend(chain_issues)
        archived_chains[folder] = chain
    for path in archived_evidence:
        chain = archived_chains.get(path.parent)
        if chain is None:
            continue
        stem = evidence_stem(path)
        if stem is None or stem[1] not in chain.threads:
            continue
        entry = chain.threads[stem[1]]
        block = entry.discuss if stem[0] == "discuss" else entry.reply
        if block is not None:
            archived_issues.extend(validate_markers(path, block, repo))
    findings.extend(
        Finding(issue.rule, path, issue.line, issue.message, "E1–E6 / C evidence contract", "Correct the evidence according to the contract") for path, issue in archived_issues
    )
    return findings, total, overview


@dataclass
class ValidationReport:
    root: Path
    findings: list[Finding]
    records: int
    overview: list[str]

    @property
    def exit_code(self):
        return int(any(finding.severity == "error" for finding in self.findings))


def validate_documents(sources: DocumentSources, *, fix=False) -> ValidationReport:
    """Validate record names, content and cross-document relations."""
    findings, records, overview = check_tree(
        sources.root, sources.changed, git_root=sources.git_root, fix=fix
    )
    if fix:
        findings, records, overview = check_tree(
            sources.root, sources.changed, git_root=sources.git_root
        )
    return ValidationReport(sources.root, findings, records, overview)
