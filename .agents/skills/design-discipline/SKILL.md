---
name: design-discipline
description: Use before implementation and during structure review to check whether module boundaries, dependency direction and code shape make the code easy to verify, maintain and revise. Use when the user asks "is this design reasonable", "should this be split", or is about to start implementing. After the design is done this skill only prepares the material for human review; no coding before approval.
---

# design-discipline: Design check

English | [中文](/.agents/skills/design-discipline/SKILL.zh.md)

A design-level check; it does not replace lint, type checking or language-level code review. A classic rule applies only when it improves **decision traceability, verifiability, review efficiency or revision scope**.

Reading records follows [the workflow contract](/.agents/se/contracts/workflow.md): in a request folder only the `proposal` pair is a record, while `discuss-*` / `reply-*` are non-binding evidence; final approval happens in direct conversation between the human and the proposal author. Review contributions and the reply format are in [the note format](/.agents/se/contracts/note-format.md); a read-only skill changes neither evidence nor records. Preserve disagreement and do not treat an author's reply or a green gate as reviewer confirmation.

## Four questions

A unit (module / class / group of functions) is healthy when all four can be answered:

1. Can decision anchors land clearly on code regions?
2. Can the tests be written from the constraints instead of backfilled from the implementation?
3. Can the diff be split into intent-sized blocks that are easy to review?
4. When the constraint changes, is the affected scope controllable?

**Ideally one unit maps to one independently verifiable constraint.** Do not split one coherent flow into seven files in pursuit of brevity — **fused responsibilities are the problem, line count is not.**

## Checks

1. **Boundaries map to constraints**: does the unit carry a single kind of decision or contract? Can the tests be written without implementation details? Can the change stand as its own diff? Several decisions crowded into one spot → split signal.
2. **Dependencies point one way**: the dependency graph is acyclic and lower layers do not depend on upper layers.
3. **Abstract on the third occurrence**: consider abstracting isomorphic logic only when it appears for the third time. First decide whether it will change together with the same decision — if so, do not abstract.
4. **Push side effects to the boundary**: keep core logic away from IO, clocks and randomness so it can be verified.
5. **Do not swallow errors**: an error is handled, propagated, or explicitly justified as ignorable. An empty catch must name the error and the reason to ignore it.
6. **Every construct has a source**: "might need it later" code with no matching requirement or decision should be deleted.
7. **Names are searchable**: a name should predict the content, so searching it finds the relevant implementation.
8. **Hand what tools can do to tools**: formatting, lint and type checking should not consume human review time.

## Where tests come from

**Tests derived from decisions are guards; tests mirrored from the implementation are only implementation selfies.**

Tests backfilled after the code show only that the implementation is self-consistent, not that it matches the intent. So:

- before writing tests, read the record's `## Decision` and `## Scope` sections and derive cases from the constraints;
- when a test goes red there are only three lawful exits: change the implementation, use `decision-revise` to change the decision, or show that the test itself is wrong. **"Making the test green" is drift manufacturing.**

## Human review gate

Design discussion lives in proposal records under the decision tree's `proposed/` lifecycle — **that record is the design document**. When a new domain or complex mechanism needs a longer design document, put it under the project's own `docs/` and link it from the proposal's `## Proposal` section.

After the design is done, assemble the review material for the user, **mark the status `pending-human-review` and pause**. The review package contains at least:

- the proposal record path + version
- related decisions (links)
- module boundaries and dependency direction
- the call chain or data flow
- key tradeoffs and alternatives (the record's `## Alternatives considered` section)
- key assumptions
- acceptance criteria
- open questions and potential drift points

Coding starts only after **the user explicitly approves this concrete version** (for example, "approve this design, start implementing").

When the user requests changes, the status becomes `changes-requested`; after the edits, **bump the version** and re-enter `pending-human-review`. **Do not implement in the same round.**

Approval covers one concrete version only. After approval, any change to the interface, data model, boundaries, flow or acceptance criteria **needs re-review**.

## Boundaries

- This skill owns design structure; `decision-check` owns which decisions a change touches. They complement each other and do not replace each other.
- A check conclusion never replaces user approval.
- Report problems found while reviewing a diff; never widen the repair scope on your own.
