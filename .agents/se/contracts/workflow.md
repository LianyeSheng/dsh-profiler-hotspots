# Workflow contract

English | [中文](/.agents/se/contracts/workflow.zh.md)

> The operative statement of the development workflow: how a request is classified, how its history is preserved, what binds and what does not, how delivery is validated, and which gate runs when. It is self-contained; nothing it requires lies outside the installed `.agents/` tree.

A repository that installs this contract can run its whole development procedure from it: the entry instructions summarize these rules, skills apply them on demand, and the sibling contracts add the finer formats. Where a summary and this page differ, this page is authoritative for the procedure.

## Contents

- [Purpose and the installed tree](#purpose)
- [Rule layers and promotion](#layers)
- [Request classes](#classes)
- [Branch and event history](#history)
- [Records, evidence, approval and lifecycle](#records)
- [Evidence citations](#citations)
- [Reading the decisions in play](#reading)
- [When a decision record is warranted](#warranted)
- [The bypass marker](#bypass)
- [Delivery](#delivery)
- [Delivery validation](#validation)
- [Gate order and the unchecked declaration](#gates)
- [Authority and conflicts](#authority)
- [The record contracts](#contracts)

<a id="purpose"></a>

## Purpose and the installed tree

This contract governs every request in a repository that has the kit installed: how it is classified, how its proposal, discussion, reply and implementation events are preserved, when a human decides, what delivery must contain, and which validation decides acceptance.

The installed tree around it is fixed. `.agents/se/contracts/` holds this contract and its sibling contracts; `.agents/se/templates/` holds the record templates; `.agents/se/scripts/decisions/` and `.agents/se/scripts/docs/` hold the validators for the workflow and bilingual components respectively; `.agents/skills/` holds each component’s skills. A component that is not installed contributes nothing, and no rule here depends on an uninstalled component: the pairing gate is the only gate that enters conditionally.

The consumer keeps its own decision tree under `.agents/notes/`; nothing under it ships with the kit. Terms used throughout: a **request** is one change with its history; a **record** is a proposal pair that states constraints; **evidence** is a non-binding discussion or reply; **delivery** is the change plus the rewritten record; a **gate** is a validator that decides part of acceptance.

Record-tree paths in instructions, validator roots, examples and template placeholders refer to the target repository's own records. They are allowed in the installed payload. The payload must not depend on se-tools' development history: source decision anchors are removed when code is installed, and concrete Markdown links into the decision tree are rejected before installation writes anything. The same rendering applies to self-installation; se-tools developers trace development decisions through the component sources.

<a id="layers"></a>

## Rule layers and promotion

A rule takes effect only at the layer it belongs to. **A rule placed in the wrong register does not exist:** a format detail in the resident block is paid for every session, and a standing constraint in an on-demand skill is not in force when it is needed.

| Register | Content | Loaded when | Criterion |
|---|---|---|---|
| Resident AGENTS.md block | Rules that must hold before any situational choice: where the decisions are, what a decision path in a comment means, which side wins on conflict, the request classes | Every session | Every line is a standing context tax |
| Skill | A process with an event trigger, steps and an artifact | On demand | The trigger event is unique and discriminable |
| Contracts and checklists | The finer rules inside a skill: formats, gate behavior, checklists | Read after the skill loads | No independent trigger |
| Decision records | The decisions themselves, in the consumer's own tree | On demand | — |

**Promotion criterion**: a new capability starts as a contract or as a section of an existing skill. It is promoted to a skill only when **its trigger event, input object and artifact are all independent**. Nothing enters the resident block unless it must hold before any situational choice.

<a id="classes"></a>

## Request classes

Classify the request before changing anything; the class decides whether implementation may start.

- **Pure implementation.** The constraints hold and only the approach changes. Do it; start the commit sequence at `impl:`; no proposal folder is needed.
- **Decision change or new decision.** The change adds, relaxes or overturns a constraint. Write a proposal before writing any code, check it against the decisions in play, then stop and wait for a human ruling on any violation or uncertainty.
- **Unclear.** Trace what the change actually touches and which constraints it falls under, then classify it as one of the two above.

<a id="history"></a>

## Branch and event history

Create one branch from `main` before changing files, named `<type>/<slug>`: the type describes the request (`feat`, `fix`, `chore`, and so on) and the slug is a short lowercase hyphenated summary. Branch types describe requests; commit subjects describe events.

Record the starting integration commit as `Base-SHA: <sha>` in the first request commit body. That SHA is fixed: do not recompute the base from a moving `main`.

Use `tag: description` commit subjects, one complete event per commit:

| Subject | Event |
|---|---|
| `proposal:` | The initial proposal or a substantive proposal revision |
| `discuss:` | Reviewer or user feedback recorded in the repository |
| `reply:` | Author response and disposition, without a proposal edit in this commit |
| `reply & revise:` | Author response together with the proposal revision it caused |
| `decision:` | Human approval, rejection, postponement or reopening, recorded after it happens |
| `impl:` | Implementation, including its tests and documentation |
| `review:` | Implementation review findings and conclusions |
| `fix:` | Corrections following review or validation |

`reply & revise:` carries both the reply and the proposal change it caused; `reply:` carries only the response. The reply file is named `reply-<slug>` in both cases, with the discussion's slug.

Once a commit is shared with a reviewer or used as a review reference, it is append-only: correct it with a subsequent commit, never by amending, rebasing or squashing. Integration preserves the original proposal, discussion and implementation commits through a normal merge or a fast-forward; squash merging is excluded. In either merge direction, a conflict-resolution commit uses `fix:` and a clean merge uses `impl:`.

Read the sequence with `git log --reverse --oneline <base>..HEAD` and inspect one event with `git show <sha>`.

<a id="records"></a>

## Records, evidence, approval and lifecycle

Only the proposal pair binds: `proposal.md` and `proposal.zh.md` state the candidate or delivered constraints. `discuss-*` and `reply-*` files are non-binding evidence even inside `implemented/`; they record review and response and never acquire authority from where they sit.

Approval happens directly between the human decision maker and the proposal author, in conversation. No repository artifact, gate result or signature proves it; an agent never invents approval, and agreement among agents is advice, not authorization.

The lifecycle is the directory, not a field: `proposed/`, `implemented/`, `rejected/` and `archived/`. An approved but unfinished record stays proposed; a postponed one stays proposed. A rejected record carries a one-line reason in its status line and freezes its body; an archived record is frozen and is no longer the basis for current behavior.

Delivery moves the whole request folder — proposal pair, evidence triplets and chain file — to `implemented/<class>/` and rewrites the fixed `proposal.md` from the proposal sections to the implemented decision sections, folding acceptance criteria and risks into the consequences. The same change repairs inbound links, switcher lines and pairing records; Git history and verbatim quotations keep their original paths and words.

A `decision:` commit may mark the event after it happens; it is a marker, not proof of approval.

<a id="citations"></a>

## Evidence citations

Each request folder that has evidence carries a `chain.yaml` recording the event coordinates: for every event, the commit and the decision-record path, stored as one English anchor with the Chinese path derived by adding `.zh.md`. The discussion and reply headers themselves carry only `Chain` and `Author`; the coordinates live in the chain file, not in the evidence headers.

The evidence body cites a concrete range as `Chain <ref> L<a>-L<b>`, where `<ref>` names the sibling file and the line range is read in the citing file's language. A full ID of the form `<request>/<thread>/<discuss|reply>/<ref>` resolves through the installed chain resolver at `.agents/se/scripts/decisions/chain.py`; it offers the read-only `refs`, `show` and `diff` subcommands and the `add`, `modify` and `delete` editing subcommands, and an editing command is a dry run unless `--write` is passed.

The chain is historical evidence addressing, validated by the document gate; it is not approval and it never proves that a discussion is resolved. A frozen folder's chain file is not rewritten: frozen evidence keeps its original addresses.

<a id="reading"></a>

## Reading the decisions in play

Read the decisions before changing behavior: implemented records under `.agents/notes/implemented/` are the constraints in force, and open proposals under `.agents/notes/proposed/` are candidate constraints the change may need to satisfy or revise.

A decision path in a code comment is the decision for that code; read the record before changing the code.

When a task disagrees with a record, follow the decision and report the conflict instead of smoothing it over. If the record itself is wrong, that is a decision change with its own proposal and human ruling — not an implementation choice.

Do not substitute memory for the records, and do not treat a comment's restatement as the whole constraint; the record is the authority. Legacy flat records remain valid.

<a id="warranted"></a>

## When a decision record is warranted

Ask one question: does this change alter what must always hold — a constraint added, relaxed or overturned? A bug fix that reveals a constraint we were always supposed to satisfy counts. A pure implementation swap, a mechanical edit or a local UI change does not.

Write a record only when the answer is yes: the record tree stays the size of the decisions, not of the commits. One record states one constraint whose violation can be judged independently, and it records the genuine alternatives it beat.

The record's own format, the evidence format and the example rules are specified by the format contract; the judgments no machine makes are in the review checklist. Both are named in the last section of this page.

<a id="bypass"></a>

## The bypass marker

Skip the decision process for a change only when the user explicitly asks for that change. Record it in the commit message as `Decision process: bypassed (reason: …)`.

A bypass is not a violation, and it does not relax delivery: history stays append-only and the delivered artifact still passes the gates. The bypass rate is a signal worth watching.

<a id="delivery"></a>

## Delivery

A decision change is deliverable only after the human ruling and green gates; integration follows the user's authorization to publish or merge.

Deliver the constraint, not only the prose: the code, tests and documentation that make the constraint hold, the record moved and rewritten to the implemented sections, and the repaired links and pairing records in the same change.

Before deleting a request branch, preserve its original commits through a normal merge or fast-forward into `main`. Do not merge unfinished implementation just to retain evidence: keep the branch pushed to the remote until an authorized retention arrangement preserves the commits. A squashed snapshot is not a substitute for preserved history.

<a id="validation"></a>

## Delivery validation

Delivery validation decides acceptance from tracked repository artifacts, the applicable contracts, and only the Git objects a contract explicitly requires: the `commit:path` blobs of evidence references and the explicit CI comparison base.

The install manifest is installation state, never evidence. Session logs, plugin or profile state, a tool invocation sequence and agent reasoning are forbidden as proof of compliance. Branch topology, commit subjects and human approval remain process obligations reviewed by people, not delivery gates.

Validators are deterministic functions of tracked content, the required Git objects and an explicit comparison base: no network, no wall clock, no randomness, no ambient environment. They may block integration or publication on format, bilingual pairing, links, evidence references, builds, types and tests.

A green result cannot establish human approval, the correctness of a decision or reviewer agreement.

`decision-check` stays advisory: it flags violations and uncertainty for a human ruling and never becomes a CI approval gate.

Checks a repository adds are committed and additive: they may add coverage but cannot disable a core validator, and every gate keeps its unchecked declaration, printing its effective selection and the checks it skipped.

Artifact validation cannot prove that every process obligation was performed; the workflow states that limit instead of promising machine proof.

<a id="gates"></a>

## Gate order and the unchecked declaration

The gates run in order, each independent and each invoking no other:

1. the bilingual pairing gate, only when the bilingual component is installed;
2. the document gate;
3. the link gate.

Never merge the gates into one script that hides a failure, and never let one gate call another: running them separately keeps each failure attributable.

Locally the gates check the index against `HEAD` with `--staged`. CI requires an explicit comparison base and passes it with `--base <sha>`; an absent, zero or unresolvable base is an error, never a silently skipped check.

Every run ends by declaring what it did not check. Read that declaration and review those items: green checks prove neither human approval nor reviewer agreement.

The workflow component's installed AGENTS.md block carries the exact commands and paths of the installed validators; this contract names the gates instead of linking the commands.

<a id="authority"></a>

## Authority and conflicts

In the kit's source repository the decision records outrank this contract; a disagreement between them is a defect fixed in the same change, and the records keep the rationale this contract summarizes. A consumer reads only the installed tree, so the records it must obey are its own.

In an installed consumer repository this contract is the operative authority: no decision history from the kit's source repository ships with it, and the consumer records its decisions in its own tree.

A change to a shipped rule updates the decision that states it and this contract in the same change; a contract change that alters a constraint needs its own proposal. Existing project instructions are retained rather than overwritten: expose a conflict instead of silently resolving it.

<a id="contracts"></a>

## The record contracts

- [The format contract](/.agents/se/contracts/note-format.md) specifies record paths, headers, sections, status transitions, evidence format and examples.
- [The anchor contract](/.agents/se/contracts/anchor-convention.md) specifies anchors in code and references between records, code and documentation.
- [The review checklist](/.agents/se/contracts/review-checklist.md) carries the judgments no machine makes.
- Record templates are installed under `.agents/se/templates/`.

When the bilingual component is installed, the bilingual contract under `.agents/se/contracts/i18n/` specifies how both language sides of a document are maintained and checked, and the pairing gate in the chain above belongs to that component.
