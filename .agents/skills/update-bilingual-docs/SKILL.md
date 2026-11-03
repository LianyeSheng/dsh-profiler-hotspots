---
name: update-bilingual-docs
description: Use when the user explicitly asks for a full bilingual translation or a pair review pass. Routine editing does not use this skill; run it only when the user names it, and follow the bilingual contract for section-by-section translation, patch updates, structural validation and re-recording.
---

# update-bilingual-docs: full translation and pair review

English | [中文](/.agents/skills/update-bilingual-docs/SKILL.zh.md)

**Run only when the user explicitly invokes it.** Routine changes update both sides in one pass per [the pairing contract](/.agents/se/contracts/i18n/README.md); this skill is not needed. It carries the heavier mechanisms and neither changes the rules nor relaxes the pairing contract.

## Trigger

- The user asks for a "full translation", "translate this into Chinese", "review this pair section by section", or names this skill.
- A new document has no counterpart yet and the user wants both sides produced in one go.
- Do not load it just because "translation is needed here"; that is the routine case.

## Invariants

1. Both languages carry equal authority; a change may be authored in either language and the edited side is the source for that update.
2. A pair is three sibling files: `foo.md`, `foo.zh.md` and `foo.i18n.yaml`, merged as a whole.
3. Never apply an update by re-translating a whole file; patch an existing counterpart minimally against the diff.
4. The gate checks the structure mirror and byte-identical code blocks; review owns the quality the gate cannot see.

## Input

One of these (or both):

- The edited side and its diff: `git diff -- <file>`
- The English source of a new document

## Steps

1. **Read the sources of truth.** Read [the pairing contract](/.agents/se/contracts/i18n/README.md), [translation rules](/.agents/se/contracts/i18n/translation-rules.md) and [terminology](/.agents/se/contracts/i18n/terminology.md). Load the terminology table before starting, not when an unfamiliar term appears.
2. **Locate the change granularity.** Use the diff to find the changed sections and Markdown units (paragraphs, table rows, list items, headings) and compare section by section without rereading unchanged parts. When only one side was changed externally, or the workspace has no usable `git diff` baseline, first run `node .agents/se/scripts/docs/translation-hints.ts <pair>`: it prints only changed sections and terminology and does not judge the translation. Patch only the changed sections it lists and keep reviewed wording elsewhere; take terms from [terminology](/.agents/se/contracts/i18n/terminology.md), and for unlisted words run `node .agents/se/scripts/docs/translation-hints.ts --term <word>` for precedents — the tool only supplies evidence, and choosing the word stays your decision.
3. **Write the counterpart.** For an existing counterpart, change only the minimal range aligned with the diff and keep the rest of the reviewed wording; for a new document, translate section by section and lock each section's structure as soon as it is written instead of fixing structure at the end.
4. **Mechanical validation.** Copy code blocks and inline code byte for byte; align heading depth, lists, tables and link order with the counterpart; rewrite paired-document links by locale (English side `/<path>.md`, Chinese side `/<path>.zh.md`, repository-root-relative with a leading `/`).
5. **Re-record.** `node .agents/se/scripts/docs/verify-translation-pairing.ts --write <pair>`, naming only the pairs confirmed in this change; use `--write --all` explicitly for a full re-record.
6. **Check.** `node .agents/se/scripts/docs/verify-translation-pairing.ts <pair>`; run the whole corpus once more before the PR. Read each finding as its four fields and fix until green.
7. **Declare.** State in the reply or PR description which pairs were confirmed, which are new, which are patch updates and whether the terminology table changed; also print the gate's four unchecked items (R1 译文忠实性, R2 术语一致性, R3 中文自然度, R4 行内代码、列表与表格顺序、图片替代文本与呈现、强调; list: `.agents/se/contracts/i18n/translation-rules.md`). Green does not mean the translation is good.

## Output

- The counterpart files and the updated `*.i18n.yaml`.
- A short report: pair paths, change type (new / patch), and any pending "undecided terms".

## Boundaries

- Handle documents only: do not change source code or implementation files outside the documentation.
- The pairing scope follows [the pairing contract](/.agents/se/contracts/i18n/README.md): READMEs in any directory, `docs/`, the decision-record tree, `.agents/se/` documents and `components/` Markdown, except single-language component fragments.
- Fidelity, terminology, naturalness, list and table order, inline code and emphasis markers are what the gate cannot check; green does not waive them, so say so in the report.
- When a term is added or changed, update [terminology](/.agents/se/contracts/i18n/terminology.md) in the same change; the terminology table is itself a paired document and moves with its counterpart.
- Report a problem with the contract itself to the user; do not edit [the pairing contract](/.agents/se/contracts/i18n/README.md) on your own.
