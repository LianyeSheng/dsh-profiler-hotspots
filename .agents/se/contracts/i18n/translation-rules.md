# Translation rules

English | [中文](/.agents/se/contracts/i18n/translation-rules.zh.md)

How to translate between the two sides of a documentation pair. Both languages carry equal authority ([the pairing contract](/.agents/se/contracts/i18n/README.md)): the edited side is the source for that update. **MUST** / **MUST NOT** block a merge or review; **SHOULD** needs a stated reason; **MAY** is discretionary.

## Faithfulness

- The counterpart *MUST* say what the authored side says: nothing added or dropped. If the pair disagrees on substance, fix the wrong side and bring the other along in the same change.
- The counterpart *SHOULD* read as natural technical writing in its own language, not a word-by-word gloss; keep the author's register — terse stays terse.
- Give sentences an explicit actor where the target language would obscure it; in Chinese write the actor (系统、门禁、评审人), not a vague passive.

## Structure and code

- Heading depths and order stay fixed; heading text is translated. Lists (kind, ordered-list start, and item count at each nesting level) and table row and column counts mirror one to one. Do not add, remove, reorder, or merge sections. The supported Markdown subset is defined in [the pairing contract](/.agents/se/contracts/i18n/README.md).
- Fenced code blocks *MUST* be byte-identical, comments and info string included; never translate code. Inline code spans — commands, flags, config keys, paths, event names, API names, versions — stay verbatim.
- A link that resolves to an in-scope paired document uses the source side's locale: `/<path>.md` on the English side and `/<path>.zh.md` on the Chinese side, always with a leading `/`. Keep the exact query and fragment suffix; targets outside the paired corpus keep their authored path; external URLs, images, and in-page fragments are unchanged; link text is translated.

## Terminology

- [terminology.md](/.agents/se/contracts/i18n/terminology.md) is the source of truth in both directions. Load it before translating; every row binds, usage constraint included.
- For a Chinese target, use the Chinese column and its first-occurrence annotation. An unlisted technical term stays English unless a citable established Chinese rendering exists; never invent one inline. A decided term enters the terminology table in the same change.
- For an English target, use the established English term and add no Chinese gloss.

## Chinese typography

- Put one half-width space between Chinese text and Latin words or numerals: `每个 plugin 注册 3 个 tool`. Never use full-width digits or Latin letters.
- Use full-width punctuation in Chinese prose: `，。：；？！（）「」`. Half-width punctuation stays inside code, inside complete English sentences quoted as-is, and inside numbers such as `3.5` or `1,024`.
- Use 顿号（、）between parallel items; prefer colons, periods, commas, or parentheses over em dashes. Second person is 你, not 您.
- Emphasis markers stay on the same spans as the source. One physical line per paragraph; exactly one trailing newline.

## Patch updates

- Apply an update by patching the counterpart minimally against the edited side's diff, then re-record. Never re-translate a whole file: that throws away reviewed wording outside the change.
- Move first-occurrence annotations with the content: the gloss goes where the term now first appears, disappears with the term, and is written once per file.
- Read the patched counterpart on its own before re-recording; everything outside the diff keeps its reviewed phrasing.

## Quality bar

- A pair is done when a bilingual engineer reading either file alone gets the same facts, caveats, and tone, and nothing extra.
- Run `node .agents/se/scripts/docs/verify-translation-pairing.ts <pair>` for the pair and the corpus-wide check at PR level. The gate declares what it did not check — R1 译文忠实性, R2 术语一致性, R3 中文自然度, R4 行内代码、列表与表格顺序、图片替代文本与呈现、强调; review owns those four and tone.
