---
name: decision-revise
description: The only write entry into decision records. Creates, revises, merges and archives records, initializes a project (directory tree, gates, AGENTS.md) and migrates from an old ledger. The other decision-* skills are read-only; every write passes through here.
---

# decision-revise: Landing records

English | [中文](/.agents/skills/decision-revise/SKILL.zh.md)

**Every write passes through here.** `decision-intake`, `decision-check` and `decision-audit` are read-only.

Before writing any entry, read [the note format](/.agents/se/contracts/note-format.md).

## Invariants

1. **One decision per request folder; the `proposal` pair is the only record.** No numbering, no reordering, cross-references are always links.
2. **The directory is the state.** A state change is a `git mv`, not a field edit.
3. **A changed decision is a new record.** Revising a record under `implemented/` may update **facts** only (paths, names, mechanisms); rewriting the decision into its opposite is a new record plus a two-way link.
4. **Do not hand-write lineage.** Git carries the history; to say "this supersedes X", write one two-way link line in the body and do not maintain an `r1 / r2` chain.
5. **Judge `J1` before acting.** Write only when a decision changes (see [the review checklist](/.agents/se/contracts/review-checklist.md)). Pure implementation swaps and mechanical edits are not written.

## Initialization (greenfield project)

1. Run `git rev-parse --show-toplevel` to confirm the repository root. If a decision tree already exists, use `bootstrap` below instead.
2. The installer writes the marked `AGENTS.md` blocks. For a repository without an `AGENTS.md`, write a minimal map that names the installed [workflow contract](/.agents/se/contracts/workflow.md) and the decision tree; never overwrite an existing `AGENTS.md` — report the conflict to the user instead of merging silently.
3. Create the skeleton: create the `{lifecycle}/{class}/` directories with the path shape of [the note format](/.agents/se/contracts/note-format.md).
4. Install the gates as the pre-commit hook: run the bilingual pairing gate, the document gate and the link gate in that order; the installed `AGENTS.md` blocks of the gate and bilingual components carry the exact commands and paths, and the pairing gate exists only when the bilingual component is installed.
5. Take the constraints the user states on the spot through "Create" below one by one. **Do not backfill what you do not know.**

## Requests, discussion and delivery

Follow [the workflow contract](/.agents/se/contracts/workflow.md); the complete format lives only in [the note format](/.agents/se/contracts/note-format.md), and drafting shapes are in [the templates](/.agents/se/templates/). One request is completed on one branch, and the first commit body records a fixed `Base-SHA`. Independent constraints use several mutually linked folders. The proposal author maintains the proposal, and reviewers use separate discussion files; the author replies to each ID in the same-slug discussion; the discussion and reply headers carry only `Chain` and `Author`, the reference coordinates live in the same folder's `chain.yaml`, the body marks the specific referenced line ranges with `Chain <ref> L<a>-L<b>`, and `chain.py` can resolve the full IDs; `reply & revise:` contains both the reply and the proposal edits, while a reply alone is `reply:`. Reviewers never edit the author's reply and authors never edit a reviewer's position; handing over or normalizing on someone's behalf requires a signature.

Implementation starts only after a human approves a concrete version. Approved but undelivered work stays under `proposed/`; on delivery, move the whole folder, keep the `proposal.md` filename fixed, rewrite it into the implemented sections, repair the inbound links, switcher lines and pairing record, and refresh the reply summaries. Any other edit to approved text needs re-approval. A rejection states its reason and freezes the text, a deferral stays proposed, and archiving freezes the whole folder. Approval given in direct conversation requires no ruling file or commit; a report is read-only derived output that preserves disagreement and unconfirmed proposer closures and never counts as approval.

The local hook checks the index with `--staged`; CI runs strictly and passes `--base <sha>` explicitly. Commits that were shared or referenced are never amended, rebased or squashed; a normal merge or fast-forward keeps the original commits. A clean merge uses `impl:`, conflict resolution uses `fix:`. Keep the original commits before deleting a branch; an unfinished implementation must not be merged to save evidence — keep the pushed branch until the authorized arrangement lands. Release and merging follow user authorization.

## Create

1. Determine the class (see P3 in the contract) and the target lifecycle.
2. Take the first-proposal date (today; for migrated records read git history) and coin the slug.
3. In the decision tree, create the `<lifecycle>/<class>/<yyyy-mm-dd>-<slug>/` folder with `proposal.md`, `proposal.zh.md` and `proposal.i18n.yaml`; state the stable author role or handle in the proposal header. Existing flat records and archives are not migrated.
4. Write all sections per the contract. **The `## Problem` section must split into two layers, `**Symptom**` and `**Cost**`.**
5. If an implementation already exists, add code anchors (see [the anchor convention](/.agents/se/contracts/anchor-convention.md)).
6. Run the document gate and the link gate.

## Revise

1. **Change facts**: when a path, symbol, default or mechanism changed, change it in place. There is no history, only the current state.
2. **Change the decision**: not done here. Write a new record, link the two (Supersedes / Superseded by), and treat the old one with "Archive" or "Merge".
3. If the scope changes, re-check whether other records now conflict and hand the ruling to the user.
4. Inspect the defenses, bridges and compatibility branches specialized for the old constraint, and propose keeping or refactoring them — **propose only; never widen the repair scope on your own**.
5. Run the gates after the fix.

## Merge (an old record entirely superseded)

Preconditions, all of them required:

- Keep **every** unique rationale, alternative, consequence, verification requirement and named coverage gap of the old record;
- repair every inbound link;
- an incomplete supersession does not count — a partial one keeps both records, mutually linked.

**Never rewrite the old file into its opposite.**

## Archive

1. Confirm three things: the decision is complete, it is unlikely to guide future work, and the historical rationale is still worth keeping.
2. `git mv` the whole folder (or the existing flat triplet) to `archived/<class>/` (the path has no `implemented` layer).
3. The status line stays `Status: implemented`, and the next line gets `Archived: YYYY-MM-DD`.
4. Repair inbound links — a link to an archived record must either point at the current authority or be explicitly labeled a historical snapshot.
5. Afterwards it is frozen permanently: no editing, translating, reordering, moving or deleting.

The archiving judgment is semantic, not a matter of word count or age. A record with no archiving reason that is also not worth keeping is handled as `implemented → deleted` per the contract.

## Bootstrap (migrate from an old ledger)

1. Identify the decisions already formed in the old documents and structure them one by one.
2. Take the first-proposal date — prefer git history; fall back to the motive date in the old ledger.
3. Create records per "Create" one by one; keep the old ledger as **read-only history** and do not delete it.
4. Backfill code anchors: search the whole repository for old numbered references and replace them with record paths.
5. Rewrite `AGENTS.md` into a map form: name the installed contracts and the decision tree, keep the existing project instructions, and expose conflicts explicitly instead of overwriting them.
6. Run the gates and repair each broken link.

## Before committing

All three gates must pass in order (pairing → document → link); the installed `AGENTS.md` blocks of the gate and bilingual components carry the exact commands and paths, and the pairing gate exists only when the bilingual component is installed. **Every run ends with the unchecked items** — `J1–J3` are in [the review checklist](/.agents/se/contracts/review-checklist.md) and `J4` in [the anchor convention](/.agents/se/contracts/anchor-convention.md); go through them yourself.

## Boundaries

- Does not change business logic; orphaned specializations only get refactoring suggestions.
- Records hold no work items or roadmaps. Non-binding discussion and proposer replies are explicitly allowed evidence, as `discuss-<topic>` / `reply-<same-topic>` triplets validated by the format contract's E1–E6, C group and X1–X5; evidence never counts as a new decision.
- Commit messages carry the decision reference paths.
