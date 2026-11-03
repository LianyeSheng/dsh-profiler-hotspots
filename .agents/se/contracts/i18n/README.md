# Bilingual documentation

English | [中文](/.agents/se/contracts/i18n/README.zh.md)

Every document in scope is maintained in English and Simplified Chinese, because this repository is read by people and agents working in both. This page defines the pairing contract, the gate, scope and exclusions, and the division of labor; [translation-rules.md](/.agents/se/contracts/i18n/translation-rules.md) defines how to translate; [terminology.md](/.agents/se/contracts/i18n/terminology.md) is the terminology source of truth. Routine work follows the rules below; the extended [update-bilingual-docs](/.agents/skills/update-bilingual-docs/SKILL.md) workflow runs only when the user explicitly invokes it.

## The pairing contract

- **Both languages carry equal authority.** A change is authored in either language, and the edited side is the source for that update; the counterpart states the same thing. Neither file outranks the other. Record keys come from English heading slugs, so the English file anchors the record's addressing, not the content.
- **A pair is three sibling files.** The English `foo.md`, the Chinese `foo.zh.md`, and the consistency record `foo.i18n.yaml`, all in the same directory. No locale directories, no separate translation repository, no interleaved bilingual files. Pairs merge whole: a change never lands one side without the other two files.
- **The consistency record.** `foo.i18n.yaml` holds one entry per heading section, keyed by the section's English heading-slug path (`/` for text before the first heading; a repeated path gets `~2`, `~3`, …). Each entry stores the hash of each side's content in that section: the section's lines in document order, excluding fenced code blocks, leading YAML frontmatter and the language-switcher line, with the heading line included; leading and trailing blank lines are trimmed and paired-document link targets are replaced by a locale-neutral `pair:/<anchor path><query/fragment>` marker. A target normalizes when it names an in-scope pair path, not when the counterpart happens to exist on disk, so a pair's records are identical before and after installation. Hashed with SHA-256 and truncated to 16 lowercase hex digits.

  ```yaml
  /foo:
    en: 41d772192075e133
    zh: dda91c6c670cfd9d
  /foo/usage:
    en: 86940bea4a3c7ed6
    zh: de78429597783c7f
  ```

  The file starts with fixed header comments naming no path; entries follow in document order as three-line entries. Fenced code blocks stay out of the hash because P4 already requires them to be byte-identical, and the switcher line stays out because installation rewrites its target to the installed counterpart. Section `i` of one side corresponds to section `i` of the other. Edits to different sections land on separate record lines, so Git's default text merge composes them; a record conflicts only when both branches changed the same section. An out-of-sync pair is updated by patching the counterpart minimally against the edited side's diff, never by re-translating whole files; the gate names each changed section.
- **Language switcher.** One blank line after the H1 — line 3 when the H1 is line 1 — the English file carries `English | [中文](/<path>/foo.zh.md)` and the Chinese file carries `[English](/<path>/foo.md) | 中文`. An extra blank line between the H1 and the switcher fails P3. The target is the counterpart's repository-root-relative path. A pair maintained in a source tree before installation points the switcher at the counterpart beside it; installation renders the installed copy and rewrites the target to the installed counterpart. Both directions keep the link: the Chinese file never drops its English backlink, and the English file never drops its Chinese link.
- **Structure mirrors the counterpart.** Heading depths and order, fenced code blocks (info string and content verbatim), table row and column counts, lists (kind, ordered-list start, and item count at each nesting level), and semantic link targets with exact query and fragment suffixes match one to one. A link to a paired document follows the locale rule in P5. Leading YAML frontmatter is exempt: both sides may carry different frontmatter, because it is excluded from both the structural mirror and the section hashes. Full preservation rules are in [translation-rules.md](/.agents/se/contracts/i18n/translation-rules.md).

## The supported Markdown subset

Pairing analyzes a fixed Markdown subset: ATX headings, fenced code blocks, GFM tables whose delimiter row and header row have the same column count, tight and loose lists, inline links and reference definitions, and inline images (an image target compares as an `image:` structure entry; reference-style image definitions are not distinguished from text).

The gate does not support or promise: setext headings (reported as P4), indented code blocks, inline links that span lines, and HTML blocks; HTML comments are ignored by structural analysis but still count toward the P2 hash. Leading YAML frontmatter is tolerated: when a document opens with a `---` line and a closing `---` line exists, those lines are excluded from structural comparison and from section hashes and are never compared as fenced code, so the two sides may carry different frontmatter. A `---` line that does not open the document, or an opening `---` with no closing line, is ordinary text.

## The gate: verify-translation-pairing

`node .agents/se/scripts/docs/verify-translation-pairing.ts` enforces this contract mechanically. It runs on Node ≥ 24 through native type stripping and has no dependencies.

- No argument checks the whole corpus.
- `--list` prints each document's pairing state — `ok`, `missing`, or `out-of-sync` — plus one `excluded-artifact <path>` row per leftover pairing artifact next to a manifest-excluded path. It does not fail on pairing state; configuration errors still exit `2`.
- Positional arguments check only the named pairs: any of a pair's three files, or its unsuffixed stem, names the pair. Naming a pair that is out of scope, excluded, or absent from disk is a usage error (`2`), not a clean pass.
- `--write <pair...>` re-records the named pairs; `--write --all` re-records every pair whose two language files both exist, creates missing records, and skips pairs that lack either language file. A named pair that is incomplete, out of scope, or excluded is refused with `2`, and so is a pair whose content cannot be recorded (for example a heading-count mismatch). The resulting record diff is the reviewable act of confirming consistency, which is why a bulk re-record must be named as `--all`.

Exit codes: `0` all checks pass, `1` at least one finding, `2` usage or configuration error.

<a id="p1"></a>

### P1 Complete pairs

Every document in scope has all three files. A manifest-excluded file has no `.zh.md` and no `.i18n.yaml`; the full check reports any leftover, and `--list` prints it as an `excluded-artifact` row.

<a id="p2"></a>

### P2 Consistency record

The record is canonical and its entries equal the entries computed from the current contents. Changing language-specific content on either side without re-confirming the pair turns the check red.

<a id="p3"></a>

### P3 Language switcher

The switcher sits exactly one blank line after the H1 — line 3 when the H1 is line 1 — with the Chinese file linking back to the English file and the English file linking to the Chinese file. An extra blank line between the H1 and the switcher fails P3; the exact text is specified under the pairing contract. The target is the counterpart's path: the installed counterpart for an installed pair, and the counterpart's source path for a pair that installation renders.

<a id="p4"></a>

### P4 Structural mirror

The two sides match in heading depths and order, fenced code blocks (info string and content, byte for byte), table row and column counts, lists (kind, ordered-list start, and item count at each nesting level), and semantic link targets with their exact query and fragment suffixes.

<a id="p5"></a>

### P5 Paired-document link locale

A link that resolves to an in-scope paired document uses its side's locale: the `.md` path on the English side and the `.zh.md` path on the Chinese side, written repository-root-relative with a leading `/`. Whether a target counts as a paired document follows the scope rule, not whether the counterpart has been installed yet. A missing counterpart in scope is a completeness error, not a fallback. Links to targets outside the paired corpus are outside P5; their repository-root-relative form is governed by the repository link gate. The language switcher is the explicit cross-locale exception.

Every finding carries its rule ID, and its `契约` line points at `.agents/se/contracts/i18n/README.md#p1` … `#p5` on this page. Every run ends with the unchecked-items declaration this repository requires of every gate, including a green one:

```
✗ .agents/se/contracts/i18n/README.zh.md:1  [P3]
  发现：H1 后的第一段不是规范的语言切换行
  期望：[English](/.agents/se/contracts/i18n/README.md) | 中文
  修复：在 H1 之后空一行写入 [English](/.agents/se/contracts/i18n/README.md) | 中文
  契约：.agents/se/contracts/i18n/README.md#p3

未自动检查（4 项，需 review）
  R1 译文忠实性   R2 术语一致性   R3 中文自然度
  R4 行内代码、列表与表格顺序、图片替代文本与呈现、强调
  清单：.agents/se/contracts/i18n/translation-rules.md
```

The declaration names what the gate cannot check: whether the two sides say the same thing, whether the terminology follows the table, whether the Chinese reads naturally, and the structure its signature does not encode — inline code, list and table order, image alt text and presentation, and emphasis.

The practical rule the gate creates: **a change that edits either side of a paired document updates the counterpart and re-records the pair with `--write <pair>` in the same change.** A pair left out of sync fails the check.

The gate's limit, stated plainly: **a green check means the pair was confirmed consistent at these exact contents, not that the confirmation was sound.** It checks recorded hashes and Markdown structure; it cannot judge whether the two sides say the same thing, or whether the wording is accurate, well-termed, and natural. That half belongs to review, under [translation-rules.md](/.agents/se/contracts/i18n/translation-rules.md). A re-recorded pair with a bad counterpart passes the gate; it must not pass review.

## Scope and exclusions

Request folders in the decision-record tree include the proposal, every `discuss-<topic>` contribution, and its same-slug `reply-<topic>`; each is a complete English/Chinese/record triplet. Evidence has no English-only exemption. Lifecycle moves carry every triplet and repair switchers, live links, and record headers together; frozen archives retain their triplets without re-recording.

Every `README.md`, matched case-insensitively on the basename in any directory; every active `.md` file under `docs/`; every active `.md` file in the decision-record tree that [the record format contract](/.agents/se/contracts/note-format.md) defines, except its frozen archive; every `.md` file under `.agents/se/`; and every `.md` file under `components/`, except each component's single-language `agents.md` fragment — is in scope. The repository-root `archive/` directory is a different tree and stays in scope. A new directory or a new README joins the scope without a manifest edit.

Scope follows discovery, not a file list. Paths that are neither a README nor under those roots are outside it: skill documents (`.agents/skills/**/SKILL.md` and the `references/` and `assets/` files beside them) and templates (`.agents/se/templates/**/*.tmpl`) never match the `.md` source rule, and a single-language component `agents.md` fragment is excluded by name. These paths are outside the scope because discovery does not reach them, not because the manifest exempts them.

**Discovery exclusions.** The gate does not scan dependency, build, or ignored trees: `node_modules/`, `.git/`, `dist/`, `lib/`, `.pnpm-store/`, `coverage/`, `.cache/`, and `.tmp/`, matching `NON_SOURCE_DIRECTORIES` in `.agents/se/scripts/docs/translation-pairing.ts`; a nested directory with one of these names is excluded the same way. These trees are not manifest exclusions, and their artifacts are never checked.

**Manifest exclusions.** [The manifest](/.agents/se/scripts/docs/translation-pairing.manifest.json) explicitly excludes this project's own documentation-writing instruction, `docs/AGENTS.md`: it is single-language by design and is not part of the shipped payload. Only that path must stay free of `.zh.md` and `.i18n.yaml`; the full check reports any leftover, and `--list` prints it as an `excluded-artifact` row. The frozen archive subtree of the decision-record tree stays outside scope, but an archived decision record keeps its complete English/Chinese/record triplet: the gate neither requires nor rewrites those files, and links from a paired document into an archived record are normalized locale-neutrally so both language sides can cite it. The manifest holds no per-file rollout list, date cutoff, or README-specific policy class.

**Universal requirement**: every current or future document in scope — decision records and READMEs included — merges as a complete pair.

## Division of labor

Routine counterparts are updated directly by the agent making the change, in one pass, after it loads [terminology.md](/.agents/se/contracts/i18n/terminology.md). It does not invoke a translation skill, generate a briefing, run a separate translation-review pass, or delegate to a subagent. The routine path is this contract: update both language files in the same change, patch the counterpart minimally against the edited side, keep structure and locale rules, and re-record the pair. Decision records and READMEs are paired documents too, so edits to them follow the same routine path.

The extended [update-bilingual-docs](/.agents/skills/update-bilingual-docs/SKILL.md) workflow keeps the heavier mechanisms for explicit user invocation: reading the sources of truth, comparing section by section, patching the counterpart, validating code blocks and structure, re-recording, and reporting what was and was not checked. It does not change the routine path and never relaxes the pairing contract.

Review owns translation quality: fidelity of meaning, terminology, naturalness, and the structural requirements that the signature does not encode. The gate's unchecked-items declaration is the standing list of what review has to cover.
