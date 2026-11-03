# Decision-record format contract

English | [中文](/.agents/se/contracts/note-format.zh.md)

> This is the single format statement shared by the `decision-*` skills and the document gate `python3 .agents/se/scripts/decisions/verify.py`. Format questions come back to this file; the rules are not copied anywhere else.
>
> Every requirement is a **rule ID**. When the gate fails it prints a marker such as `[P1]` or `[S7]` that points at the section below.

Software is a collection of decisions and implementation is their result. A decision record preserves **what must always hold** and **why**; code, tests and documents are its derivatives.

---

## 0. Bilingual

Every record is a bilingual pair:

| File | Language | Title | Status | Sections |
|---|---|---|---|---|
| `X.md` | English | `# Decision: <title>` | `Status: <status>` | `## Problem` etc. |
| `X.zh.md` | Chinese | `# 决策：<标题>` | `状态：<状态>` | `## 问题` etc. |

Both files sit in the same request folder (existing flat records in `{lifecycle}/{class}/`), and line 3 links each to the other (see H3).

**The pairing completeness and consistency record (`.i18n.yaml`) is owned by the bilingual pairing gate `node .agents/se/scripts/docs/verify-translation-pairing.ts --write <pair>`; the document gate does not re-check it.** That is the shipped bilingual contract, whose rules are in `.agents/se/contracts/i18n/README.md`.

This section states only that **each language version's header tokens and section names must match its language and must not be mixed.**

---

## 1. File tree

### P1 Path shape

```
.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-slug.md
.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-slug.zh.md
```

The above are legacy flat records that remain supported. New records use `.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-slug/proposal.md` and `proposal.zh.md`, with `proposal.i18n.yaml` alongside. One folder holds one decision; independent constraints use several linked folders on the same request branch. Only the proposal, `discuss-<topic-slug>` and `reply-<same-topic-slug>` triplets and `chain.yaml` are allowed; unknown files and nested folders are forbidden. Only the proposal is a record; evidence is not. Counting is by decision, not by Markdown file.

**Counterexample**: `.agents/notes/2026-09-03-x.md` (missing lifecycle and class).

### P2 Lifecycle segment is valid

The first segment must be one of four:

| Value | Meaning |
|---|---|
| `proposed` | Proposal: written, not implemented yet (or only partly implemented) |
| `implemented` | Delivered: the decision is delivered and the file stays consistent with the code |
| `rejected` | Rejected: the proposal was discussed and refused |
| `archived` | Archived: once implemented, no longer guides future work, frozen as-is |

**The directory is the state.** A decision's status change appears as a file move, never as a field edit.

### P3 Class segment is valid

The second segment comes from a closed set; the gate rejects any other value:

| class | What it covers |
|---|---|
| `architecture` | Structural decisions about the source we deliver: how packages are organized, what the runtime vocabulary is |
| `process` | Tooling and procedure around the source: gates, package management, release cadence |
| `feature` | New capabilities exposed to users or models |
| `bug-fix` | Fixing a defect, or closing a gap that a review exposed |
| `simplification` | Removing code, behavior or interface surface without adding capability |
| `testing` | Test infrastructure and strategy |

The boundary between `architecture` and `process`: **architecture is the source code we deliver, process is the tooling and procedure around it.**

`refactor` is deliberately absent: it overlaps `simplification`, and the test "did observable behavior change?" already covers it.

### P4 Date segment is valid

Request folder names (and the filenames of legacy flat records) begin with `yyyy-mm-dd` and name a date that exists.

The date is the day the topic was **first raised**. New records take the current day; existing flat records carry the date from Git history.

### P5 Slug segment is valid

The remainder after the date in the request folder name is a lowercase English phrase of letters, digits and hyphens that describes the topic. The Chinese version adds `.zh` before `.md`; the slug is unchanged.

**No numbering.** A number is a global counter and a coordination point under parallel work; cross-references always use links.

---

## 2. Header

Both languages share the same header shape and differ only in tokens. The English form:

```markdown
# Decision: <title>

English | [中文](/.agents/notes/implemented/architecture/2026-09-03-x.zh.md)

Status: implemented

## Problem
```

The Chinese version swaps the tokens for Chinese and writes the switcher line as `[English](<counterpart path>) | 中文`.

### H1 Title line

The first line, by language:

| Language | Form |
|---|---|
| English | `# Decision: <title>` |
| Chinese | `# 决策：<标题>` |

The title is the topic in one sentence, without a number, a date or a status.

### H2 Blank line 2

### H3 Language switcher line

The third line links to the other language version of the same record:

```markdown
English | [中文](/.agents/notes/implemented/architecture/2026-09-03-x.zh.md)
```

```markdown
[English](/.agents/notes/implemented/architecture/2026-09-03-x.md) | 中文
```

The link is repository-root relative (leading `/`); see section 6.

### H4 Blank line 4

### H5 Status line matches the directory

The fifth line is the status line; its value follows from the directory and the language:

| Directory | English | Chinese |
|---|---|---|
| `proposed/` | `Status: proposed` | `状态：提案中` |
| `implemented/` | `Status: implemented` | `状态：已落地` |
| `rejected/` | `Status: rejected — <one-line reason>` | `状态：已否决 — 一句话理由` |
| `archived/` | `Status: implemented` | `状态：已落地` |

The status line **carries no date and no parentheses**. The date is in the filename; everything else is in Git.

**Rejection is the only status that carries content** — a reader comes to that line for the conclusion. Archiving is not a fourth status: an archived file is still implemented, and the archive fact gets its own line.

### H6 Status line is unique

The document has exactly one status line, and it sits on line 5. When the body mentions a status, use body wording; never write a status line.

### H7 Archive line (required under archived/)

Records under `archived/` insert this line after the status line:

| Language | Form |
|---|---|
| English | `Archived: YYYY-MM-DD` |
| Chinese | `归档：YYYY-MM-DD` |

### H8 Archive line (forbidden outside archived/)

Only records under `archived/` may carry the archive line.

---

## 3. Body sections

Section names are fixed per language and **must not be mixed**.

### S1 The first section is the problem

The first `##` section must be `## Problem` (English) or `## 问题` (Chinese). **The problem comes before the solution** — without a clear problem, a reader cannot judge whether the solution solved the right thing.

### S2 Sections required in proposed

| English | Chinese |
|---|---|
| `## Problem` | `## 问题` |
| `## Proposal` | `## 提案` |
| `## Scope` | `## 作用域` |
| `## Alternatives considered` | `## 考虑过的替代方案` |
| `## Acceptance criteria` | `## 验收标准` |
| `## Risks` | `## 风险` |

Free technical sections sit between the proposal section and the scope section.

### S3 Sections required in implemented

| English | Chinese |
|---|---|
| `## Problem` | `## 问题` |
| `## Decision` | `## 决策` |
| `## Scope` | `## 作用域` |
| `## Alternatives considered` | `## 考虑过的替代方案` |
| `## Consequences` | `## 后果` |

### S4 Sections required in rejected

Only the problem and proposal sections are required.

The body is **frozen**: keep every section as written at proposal time; do not rewrite or remove anything. The conclusion sits in the status line, not in the body.

### S5 Non-empty scope

State in one sentence what this decision governs:

```markdown
## Scope
Every code path that handles a request (including middleware and the request branch of background tasks).
```

It is the only basis for finding new code that falls inside the scope without an anchor, and the entry point for `decision-check`'s forward check.

**Content that cannot be phrased as a scope shows that it is not yet a decision** — send it back to the problem level.

### S6 Non-empty alternatives considered

Each genuine alternative gets its own paragraph: the conclusion first, then why it lost.

Reason: **a decision that does not record what it beat invites repeated re-litigation** — that is a decision record's first purpose.

When there truly was no alternative at the time, write `未记录（YYYY-MM-DD）` with the date and the gate passes.

### S7 implemented forbids proposal-phase sections

`implemented/` must not contain:

| English | Chinese |
|---|---|
| `## Proposal` | `## 提案` |
| `## Plan` | `## 计划` |
| `## Migration plan` | `## 迁移计划` |
| `## Acceptance criteria` | `## 验收标准` |

Proposal-phase normative language inside a delivered record leaves readers unable to tell the present state from the intent. The rewrite direction is in "Status transitions".

### C1 The problem separates symptom and cost

The problem section must give both layers:

| Layer | English | Chinese | Meaning |
|---|---|---|---|
| Symptom | `**Symptom**` | `**现象**` | The event that made it visible (a traceable fact) |
| Cost | `**Cost**` | `**代价**` | What is lost if it is not fixed (the value layer) |

```markdown
## Problem

**Symptom**: On 2026-08-12 a payment callback timed out; synchronous log flushing pushed p99 to 3s under disk stalls.
**Cost**: Tail latency is a product promise that outranks implementation convenience.
```

**A symptom without a cost does not qualify.** A problem is not something objectively present; value projects it — if we do not care, it is no problem, and without a cost there is no reason to decide.

### A1 archived status line

See H5: an archived record's status line reads implemented.

### A2 archived is frozen

Once archived a record **may not be edited, translated, reordered, moved or deleted**, and **may not be cited as the basis for current behavior**.

Historical references may link into it, but that cites history, not authority.

---

## 4. Status transitions

Every transition completes **within the same change** and re-satisfies the target lifecycle's section requirements — otherwise the gate fails. **Both language versions, the evidence and the consistency record move together; the current inbound links, switcher lines and pairing records are repaired in the same change. Historical Git paths and verbatim quotations stay as they are.** Approved but undelivered stays proposed; postponement also stays proposed. The proposal header names its author with a stable role or handle, and a handoff is kept as an attributed header-change commit.

### proposed → implemented

On delivery, within the same commit:

1. `git mv` the whole request folder to `implemented/<class>/`, keeping the fixed `proposal.md` filename and all evidence triplets; existing flat-record triplets move together
2. change the status line to implemented
3. rewrite the proposal sections as present-tense decision sections
4. fold acceptance criteria and risks into the consequences section (or a present-tense verification section)
5. drop the plan and keep only the delivered facts

### proposed → rejected

1. `git mv` the whole folder (or the existing flat triplet) to `rejected/<class>/`
2. add a one-sentence reason to the status line
3. freeze the body; not a single word changes

### implemented → archived

1. `git mv` the whole folder (or the existing flat triplet) to `archived/<class>/` — **there is no `implemented` level in the path**
2. keep the status implemented
3. insert the archive line under the status line
4. the record is then frozen permanently

### implemented → deletion

Delete only records that describe a **small UI adjustment** or a **purely mechanical change**, and repair the inbound links.

A local bug fix, a performance change, a new capability or a substantive behavior decision **does not qualify for deletion because the implementation is small**.

### Merging (fully superseded)

An old record may be merged into a new owner and deleted, under these preconditions:

- keep **every** unique rationale, alternative, consequence, verification requirement and named coverage gap of the old record;
- repair all inbound links;
- partial replacement does not count — a partial supersession keeps both records and links them to each other.

**Rewriting an old file into its opposite is never allowed.** A reversed decision is a new decision plus bidirectional links.

---

## 5. Archiving

The criterion for archiving is semantic, not word count or age: **the decision is done, unlikely to guide future work again, but its historical rationale is still worth keeping.**

Handling after archiving is in A2.

> **This contract introduces no content-hash manifest.**
> The reference implementation has 900+ archived records and a public release repository, so it needs tamper evidence. Here the archive is small and the repository private, so **Git itself is the tamper-evident record**.
> Trigger for introducing one: more than 100 archived records, or a published repository.

---

## 6. Cross-references

### Resolution base

**Uniformly the repository root. This is the only convention.**

The two media are written differently because of their syntax, but they are **two spellings of the same convention**, not two rules:

| Medium | Form | Reason |
|---|---|---|
| Markdown link | `[title](/.agents/notes/implemented/architecture/2026-09-03-x.md)` | GitHub requires the leading `/` to resolve from the repository root; without it the path is taken relative to the current file |
| Code comment | `.agents/notes/implemented/architecture/2026-09-03-x.md` | No leading `/`, so it does not look like an absolute filesystem path |

Link validity is checked by the independent link gate `python3 .agents/se/scripts/decisions/verify_links.py --staged`, whose rules are in [anchor-convention.md](/.agents/se/contracts/anchor-convention.md).

---

## 7. Judgment requirements

The three items below cannot be checked by a machine; [review-checklist.md](/.agents/se/contracts/review-checklist.md) owns them:

- **J1** Write a record only when a decision changed
- **J2** One record = one constraint whose violation can be judged independently
- **J3** Alternatives are genuine alternatives, not straw men

Every gate run ends by declaring these three unchecked.

## 8. RFC evidence format (E1–E6 and the C group)

The request procedure itself is stated by [the workflow contract](/.agents/se/contracts/workflow.md); the format is this contract, and drafting uses [templates/](/.agents/se/templates/). Discussions and replies are non-binding paired evidence; they record review and response only, and never initiate a ruling, an approval, an assignment or continued work. Verbatim quotations are kept as attributed source evidence. Reviewers maintain their discussions; the proposal author maintains the separate same-slug reply.

### E1 Evidence header

`discuss-<topic-slug>` / `reply-<same-topic-slug>` use lowercase hyphenated slugs, each a triplet of `.md`, `.zh.md` and `.i18n.yaml`. The H1 is `# Discussion: <title>` / `# Reply: <title>` (Chinese `# 讨论：<标题>` / `# 回复：<标题>`). Line 3 is the exact counterpart switcher line; lines 2 and 4 are blank; lines 5 and 6 are exactly `Chain` then `Author` in order (Chinese `Chain：` then `作者：`). The `Chain` value is `<request-date-slug>/<thread-slug>`; `Author` is the `git config user.name` in use for a human and the agent's own stable identifier. The header may not carry `Evidence`, `Proposal`, `Discussion`, `Reviewed-*`, `Proposal-Digest`, `Result` or a human-contribution group, and admits no free-form text.

### E2 Discussion structure

Only `## Context` and `## Findings` (Chinese 「背景」／「问题条目」), in fixed order. Context states the review scope and attributed sources and holds no finding without an ID. Each entry is an H3 title readable in the document's language, then Finding-ID, Kind and Blocking, followed by exactly four H4 sections: Problem, Evidence, Impact and Suggestion (Chinese 「问题」「证据」「影响」「建议」). IDs are unique within one discussion and lowercase-hyphenated; Kind is issue/question/suggestion and Blocking is yes/no. Every section must carry substantive text — empty sections and TODO/TBD/ellipsis placeholders fail; extra sections and text outside entries are forbidden.

### E3 Proposal reference

Both the `discuss` and `reply` blocks must carry a `proposal` ref (see the C group). That ref's English coordinate (its `en` coordinate in v1) resolves to the decision record blob of this request folder, titled with that language's decision title; v2's Chinese blob is verified through the `.zh.md` derived from the same commit, while v1 uses the stored `zh` coordinate. The lifecycle segment may be a historical location; the bootstrap flat proposal path normalizes by the same topic identity.

### E4 Reply coverage

Parse the IDs from the reply file; the reply ID set must equal the ID set of the current same-language `discuss-<slug>.md`, each exactly once — missing, repeated or extra IDs fail. A reply no longer references historical discussion snapshots.

### E5 Reply completeness

Only `## Responses` (Chinese 「回应」). Each H3 is followed in order by Finding-ID, Kind (the same as the source), Disposition and Resolution; then only four H4 sections: Answer, Reason, Accepted part and Unaccepted part (Chinese 「回答」「理由」「采纳部分」「未采纳部分」). The first sentence of Answer restates the source concern and answers it directly; Reason explains the disposition; a declined part keeps a short verbatim quotation of the disputed wording. For `accepted` the accepted part is substantive and the unaccepted part is exactly `none`; for `partially-accepted` both parts are substantive; for `declined`/`deferred` the accepted part is exactly `none` and the unaccepted part explains the decline or the postponement. Partially accepted, deferred and declined blocking findings must be `unresolved`. A declined Reason opens with `Decline-Class: out-of-scope/invalid/tradeoff` and explains it; a deferred Reason contains exactly one non-empty `Owner` and `Trigger` and explains them. Unresolved entries keep their reason; no separate open-issues or next-steps section is opened. A structurally complete unresolved reply may pass; it is not a unanimity gate.

### E6 Bilingual identity

Compare `Author`, `Chain` and the finding-level Finding-ID, Kind, Blocking, disposition and resolution state across both languages; inside the chain file, the v2 derived Chinese blob and the v1 en/zh path pairing and same-commit relation are verified by C3. `Proposal-Digest` no longer exists.

### The C group: chain.yaml

One `chain.yaml` per request folder that contains evidence, frozen when the folder moves or is archived; a folder without evidence does not need one. Restricted block-style YAML (mappings and inline scalar mappings only; no lists, anchors, quotes, multi-line scalars or trailing comments). Readers accept version 1 and 2. `proposed/` and `implemented/` dispatch shape rules by the declared `version`; in `rejected/` and `archived/` the chain file converts to v2 on transition (the chain is bookkeeping; the frozen evidence bodies do not change), and a leftover v1 reports C1. There is no migration window and no version error for an active v1.

Version 2 stores a single English coordinate per ref; the Chinese path is derived from `.md` as `.zh.md`:

```yaml
version: 2
threads:
  <thread-slug>:
    discuss:
      proposal:
        commit: <full-lowercase-SHA>
        path: .agents/notes/<lifecycle>/<class>/<yyyy-mm-dd-slug>/proposal.md
    reply:
      proposal: { ... }
```

Version 1 keeps both `en`/`zh` coordinates: each is `{commit, path}` with the same commit, and the `zh` path is the `en` path plus `.zh.md`. v1 remains valid forever in `proposed/` and `implemented/`; a frozen folder's chain file converts to v2.

- C0 The request folder name (`yyyy-mm-dd-slug`) is unique across every lifecycle and class, so searching a full ID is unambiguous.
- C1 `chain.yaml` appears only when discuss/reply evidence exists; its shape is `version` + `threads`, with version 1 or 2; in `rejected/` and `archived/` it must be 2.
- C2 Thread keys correspond one to one with files: every `discuss-<slug>` has a thread, a thread must have a discuss, and the `reply` block and `reply-<slug>.md` exist or are absent together. Every discuss/reply block carries at least one ref and must include `proposal`.
- C3 Ref keys are the sibling filename stems (`proposal`, `discuss-*`, `reply-*`); a v2 value is `{commit, path}` where `path` is the English `<ref>.md` and the same commit's `<ref>.zh.md` must resolve to a blob; a v1 value is `en`/`zh` each `{commit, path}` with identical commits. Both versions: the commit is a full 40-character lowercase SHA that resolves to a commit and is an ancestor of the commit under check; the path is a safe repository-relative path with the correct language suffix and a basename matching the ref, located in the same request folder by topic identity (the lifecycle segment may be historical; the bootstrap flat proposal is the exception); `commit:path` resolves to a Markdown blob of the matching type.
- C4 Body citation markers: `Chain <ref> [L<a>-L<b>]` must resolve to a ref block of the file it appears in; the line span uses the cited file's language (v2 Chinese uses the derived path, v1 the stored `zh` coordinate) and must not run past the cited blob.

Validators never fetch the network; the CI checkout keeps full history. Unavailable history is a diagnostic error.

### Derived overview and the reference CLI

The gate prints a read-only overview per finding (discussion path, ID, Kind, Blocking, disposition, author resolution state, verification state, reply path); author closure is not reviewer confirmation, and a closure without attributable confirmation stays `unverified`. `python3 .agents/se/scripts/decisions/chain.py` serves read-only `refs`, `show [L<a>-L<b>] [--locale en|zh]` and `diff` by full ID `<request>/<thread>/<discuss|reply>/<ref>`, without network, and prints the corresponding `git show` command; the default is `--locale en`, v2's `--locale zh` uses the derived path at the same commit, and v1 uses the stored `zh` coordinate. The same script has `add`, `modify` and `delete` editing subcommands: dry run by default, printing the target and a unified diff; `--write` replaces atomically, writes v2 and converts losslessly mappable v1 in the same write, refuses frozen folders and unmappable v1, and validates v2 shape, bilingual blobs, ancestry and C2 correspondence before writing; editing touches only `chain.yaml`. `python3 .agents/se/scripts/decisions/migrate_chain.py` converts losslessly mappable v1 to v2 once (including chain bookkeeping in frozen folders, without changing frozen evidence bodies); dry run by default, atomic replacement with `--write`; unmappable files stay v1 and remain valid. The gate is read-only and never calls the editing commands; it does not compare revision freshness — whether a citation is still on point is review's job.

## 9. Proposal examples (X1–X5)

### X1 Proposal coverage

A new or revised proposed record carries at least one marked example at the document level; not every section needs one. Unchanged old proposals and frozen archives are not retrofitted. CI and the local call run the same validator; locally the index is compared with HEAD, and CI passes --base explicitly.

### X2 Marker syntax

Outside code fences, wrap an example with `<!-- example:begin id=timeout-flow kind=walkthrough mode=optional -->` and `<!-- example:end id=timeout-flow -->`. The attributes are exactly id, kind and mode, in fixed order; the ID is a unique lowercase hyphenated phrase shared by both sides; kind is walkthrough/discuss/reply/counterexample and mode is optional/when-needed. Markers may not nest, overlap, stay unclosed or repeat. Syntax illustrations inside fences do not count.

### X3 Substantive content

A sample body must not be empty, whitespace-only, placeholder-only or a single placeholder SHA. Fictional commits and paths in an example may remain; they need not resolve in Git.

### X4 Typed samples

A discuss/reply sample body is one quoted document, with explanatory prose outside the marker. After removing the quotation prefix and the presentation backticks, it parses with the E1/E2/E5 structure: this language's header (Chain, Author), IDs, enums and the four body sections complete, without resolving fictional Git sources or executing commands. A counterexample states its expected check and pass or fail outcome and is not required to pass as valid evidence. A walkthrough may narrate a concrete flow. CI does not judge teaching quality, example density or whether a section needs an example.

### X5 Bilingual correspondence

The two sides correspond in example ID, kind, mode, order and the finding IDs of typed samples. Each side uses its own language format; translation quality stays with review.
