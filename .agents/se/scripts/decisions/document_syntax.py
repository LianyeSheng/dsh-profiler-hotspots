"""Shared syntax for RFC documents: Markdown lines, headers, examples and links.

"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
REQUEST_ID = rf"[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}-{SLUG}"
CHAIN_VALUE = re.compile(rf"({REQUEST_ID})/({SLUG})")
KEYS = dict(
    zip(
        ("Author", "Chain", "Finding-ID", "Blocking", "Disposition", "Resolution", "Kind", "Decline-Class", "Owner", "Trigger"),
        ("作者", "Chain", "问题标识", "是否阻塞", "处置", "解决状态", "类别", "拒绝类别", "负责角色", "重启条件"),
    )
)
VALUES = dict(
    zip(
        ("yes", "no", "accepted", "partially-accepted", "declined", "deferred", "resolved", "unresolved", "none", "issue", "question", "suggestion", "out-of-scope", "invalid", "tradeoff"),
        ("是", "否", "采纳", "部分采纳", "拒绝", "延期", "已解决", "未解决", "无", "问题", "疑问", "建议", "超出范围", "问题不成立", "取舍"),
    )
)
ENUMS = {
    "Kind": ("issue", "question", "suggestion"),
    "Blocking": ("yes", "no"),
    "Disposition": ("accepted", "partially-accepted", "declined", "deferred"),
    "Resolution": ("resolved", "unresolved"),
}
SECTIONS = {"discuss": ("Problem", "Evidence", "Impact", "Suggestion"), "reply": ("Answer", "Reason", "Accepted part", "Unaccepted part")}
ZH_SECTIONS = dict(
    zip(
        ("Context", "Findings", "Responses", "Problem", "Evidence", "Impact", "Suggestion", "Answer", "Reason", "Accepted part", "Unaccepted part"),
        ("背景", "问题条目", "回应", "问题", "证据", "影响", "建议", "回答", "理由", "采纳部分", "未采纳部分"),
    )
)


@dataclass(frozen=True)
class MarkdownDocument:
    lines: tuple[str, ...]
    prose: tuple[tuple[int, str], ...]
    headings: tuple[tuple[int, str], ...]

    def section_body(self, heading: str) -> str | None:
        start = None
        for index, title in self.headings:
            if start is None and title.strip() == heading:
                start = index + 1
            elif start is not None and title.startswith("## "):
                return "\n".join(self.lines[start:index])
        return None if start is None else "\n".join(self.lines[start:])


def prose_lines(text: str) -> tuple[tuple[int, str], ...]:
    """Return 1-based lines outside matching backtick or tilde code fences."""
    result = []
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match:
            token, tail = match.groups()
            if fence is None:
                fence = token
                continue
            if token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
                continue
        if fence is None:
            result.append((number, line))
    return tuple(result)


def parse_markdown(text: str) -> MarkdownDocument:
    prose = prose_lines(text)
    headings = tuple((number - 1, line) for number, line in prose if re.match(r"^#{1,6} ", line))
    return MarkdownDocument(tuple(text.splitlines()), prose, headings)


@dataclass(frozen=True)
class FieldSyntax:
    line: int
    text: str
    key: str | None
    value: str | None


def parse_fields(rows, locale: str) -> tuple[FieldSyntax, ...]:
    """Split localized metadata without imposing keys, order or value constraints."""
    separator = "：" if locale == "zh" else ": "
    reverse_keys = {value: key for key, value in KEYS.items()} if locale == "zh" else {}
    result = []
    for number, text in rows:
        if not text.strip():
            continue
        key, sep, value = text.partition(separator)
        result.append(FieldSyntax(number, text, reverse_keys.get(key, key) if sep else None, value if sep else None))
    return tuple(result)


@dataclass(frozen=True)
class SectionSyntax:
    index: int
    heading: str
    body: str


@dataclass(frozen=True)
class EntrySyntax:
    index: int
    title: str
    fields: tuple[FieldSyntax, ...]
    sections: tuple[SectionSyntax, ...]


@dataclass(frozen=True)
class EvidenceSyntax:
    markdown: MarkdownDocument
    header: tuple[FieldSyntax, ...]
    h2: tuple[tuple[int, str], ...]
    context: str
    body_start: int
    entries: tuple[EntrySyntax, ...]
    leading_body: str


def parse_evidence(text: str, kind: str, locale: str) -> EvidenceSyntax:
    markdown = parse_markdown(text)
    lines, headings = markdown.lines, markdown.headings
    h2 = tuple((index, title) for index, title in headings if title.startswith("## "))
    header_end = h2[0][0] if h2 else len(lines)
    header = parse_fields(((i + 1, lines[i]) for i in range(4, header_end)), locale)
    context_end = h2[1][0] if len(h2) > 1 else len(lines)
    context = "\n".join(lines[h2[0][0] + 1 : context_end]).strip() if kind == "discuss" and h2 else ""
    body_start = h2[-1][0] if h2 else len(lines)
    h3 = [(index, title) for index, title in headings if index > body_start and title.startswith("### ")]
    entries = []
    for position, (index, title) in enumerate(h3):
        end = h3[position + 1][0] if position + 1 < len(h3) else len(lines)
        h4 = [(i, h) for i, h in headings if index < i < end and h.startswith("#### ")]
        stop = h4[0][0] if h4 else end
        fields = parse_fields(((i + 1, lines[i]) for i in range(index + 1, stop)), locale)
        sections = tuple(
            SectionSyntax(i, h, "\n".join(lines[i + 1 : h4[k + 1][0] if k + 1 < len(h4) else end]).strip())
            for k, (i, h) in enumerate(h4)
        )
        entries.append(EntrySyntax(index, title[4:], fields, sections))
    leading_end = h3[0][0] if h3 else len(lines)
    leading = "\n".join(lines[body_start + 1 : leading_end]).strip()
    return EvidenceSyntax(markdown, header, h2, context, body_start, tuple(entries), leading)


@dataclass(frozen=True)
class ExampleMarker:
    index: int
    operation: str
    identifier: str | None = None
    kind: str | None = None
    mode: str | None = None


EXAMPLE_BEGIN = re.compile(rf"<!-- example:begin id=({SLUG}) kind=(walkthrough|discuss|reply|counterexample) mode=(optional|when-needed) -->")
EXAMPLE_END = re.compile(rf"<!-- example:end id=({SLUG}) -->")


def parse_example_markers(text: str) -> tuple[ExampleMarker, ...]:
    result = []
    for number, line in prose_lines(text):
        if "<!-- example:" not in line or line.lstrip().startswith(">"):
            continue
        begin, end = EXAMPLE_BEGIN.fullmatch(line), EXAMPLE_END.fullmatch(line)
        if begin:
            result.append(ExampleMarker(number - 1, "begin", *begin.groups()))
        elif end:
            result.append(ExampleMarker(number - 1, "end", end[1]))
        else:
            result.append(ExampleMarker(number - 1, "invalid"))
    return tuple(result)


def parse_quoted_document(body: str) -> str:
    return "\n".join(re.sub(r"^> ?", "", line).replace("`", "") for line in body.splitlines()).strip()


MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
INLINE_CODE = re.compile(r"`[^`]*`")
CODE_NOTE_PATH = re.compile(r"(?<![\w/])(\.agents/notes/[\w./\-]+\.md)")


def parse_markdown_links(text: str) -> tuple[tuple[int, str], ...]:
    return tuple(
        (number, target.strip())
        for number, line in prose_lines(text)
        for target in MD_LINK.findall(INLINE_CODE.sub("", line))
    )


def parse_code_references(text: str) -> tuple[tuple[int, str], ...]:
    return tuple(
        (number, target)
        for number, line in enumerate(text.splitlines(), 1)
        for target in CODE_NOTE_PATH.findall(line)
    )


def local_key(key, locale):
    return KEYS[key] if locale == "zh" else key


def local_value(value, locale):
    return VALUES.get(value, value) if locale == "zh" else value


def link_path(value):
    m = re.fullmatch(r"\[[^\]]+\]\(/([^\s)#]+)\)", value or "")
    return m[1] if m else None
