---
name: decision-check
description: Use when a proposal has been written or a change is about to land, to check how what is about to happen relates to the current decisions. Outputs three states — definite violation / uncertain / definite non-violation — and reports only information that changes the next action. Read-only — it changes neither code nor records.
---

# decision-check: Decision compliance check

English | [中文](/.agents/skills/decision-check/SKILL.zh.md)

It answers one question only: **which current decision does this change violate?**

Reading records follows [the workflow contract](/.agents/se/contracts/workflow.md): in a request folder only the `proposal` pair is a record, while `discuss-*` / `reply-*` are non-binding evidence; final approval happens in direct conversation between the human and the proposal author. Review contributions and the reply format are in [the note format](/.agents/se/contracts/note-format.md); a read-only skill changes neither evidence nor records. Preserve disagreement and do not treat an author's reply or a green gate as reviewer confirmation.

## Check scope: only constraints machines cannot check and people cannot see through

Not every decision belongs in this check. Triage first, so the check does not degrade into ritual:

| How the breakage is found | What it needs | Does this skill cover it |
|---|---|---|
| Tests, lint, gates, types | Writing the check is enough | **No** — the machine fires |
| A human gets it in one glance at the diff | One sentence resident in `AGENTS.md` | **No** — already resident |
| Only judgeable after reading the whole decision plus context | This skill | **Yes** |

If a constraint fits in one sentence and its violation is visible, it should already be in `AGENTS.md` and needs no repeated report. **Run this skill only in the third case.**

## Input

One of two:

- **Proposal**: a record under the decision tree's `proposed/` lifecycle (or a draft about to be written)
- **Change**: command output, or the actual `git diff`

## Steps

1. Read [the note format](/.agents/se/contracts/note-format.md), then walk the records under `implemented/` and `proposed/`.
2. Use `## Scope` to filter the decisions that govern the object in question. **Decisions outside the scope are not read** — new code has no anchor, so only the scope can catch it.
3. Judge each matching decision with the three states.

## Three states and their rulings

| State | Ruling | Next action |
|---|---|---|
| **Definite violation** | Clear grounds that the constraint surface is harmed | Block: change the implementation, or use `decision-revise` to change the decision |
| **Uncertain** | No grounds to exclude it, and it cannot be confirmed | Hand to the human — **a concrete question is mandatory** |
| **Definite non-violation** | Grounds that it is not governed, or only the implementation changed | Pass |

**"Uncertain" is a legitimate and encouraged answer.** Better to say you do not know than to invent a "pass" for the sake of a clean conclusion.

## Output

Two forms only. **A pass is one line and does not list what was checked.**

### Pass

```
check: 通过
```

Do not write "checked 22 decisions" and do not give coverage counts — that is an unverifiable claim, as good as nothing. To judge whether the work was done, reading the diff is faster.

### Findings

```
check: 阻塞

[违反] <记录路径>
  位置: packages/adapter/src/handler.py:88（新增）
  依据: 作用域为「一切请求处理路径」；本处新增同步磁盘写，决策无豁免记录。

[不确定] <记录路径>
  位置: packages/adapter/src/anon.py:41（修改）
  依据: 决策只列了白名单，未定义未列出类型的兜底边界。
  待裁: 新段类型 "xxx" 应归入白名单，还是按「其他消息」留类型标记？
```

Four elements: **tag → record path → location → ground**. `依据` must state both "how far the constraint reaches" and "what this spot does"; half of it is no ground.

`[不确定]` must add one more line, **`待裁:`** (ruling needed), and it must be one concrete question for the human. Without it, uncertainty is a state transition nobody can execute, the human replies "judge it yourself", and the process collapses.

### Mixing and ordering

- Violations first, uncertainties after.
- Several violations of the same decision merge into one item, with multiple locations.
- **At most 5 items.** More means the change is too big and should be split first — the cap is a signal, not a formatting rule.

## Covered but not violated

**Do not report.** Few decisions reach this skill, so `check: 通过` (pass) is enough.

The cost: if the judgment is wrong here, nobody notices the judgment "the agent believes it does not violate" itself. The defense is the "uncertain" state — it requires the agent to admit not knowing.

## Where the output goes

| Occasion | Destination |
|---|---|
| Agent reply | Print it directly, **write no file** |
| Blocked / needs a ruling | Stop here and wait for the human; **change no code, commit nothing** |
| Pass and going to a PR | Write it at the top of the PR description |

Do not produce a check-report file — it rots and nobody reads it.

## Boundaries

- Read-only. Revision, refactoring and record backfill each need later authorization.
- Does not replace language-level code review or documentation consistency checks.
- Classifications such as "untouched / re-derived / limited" are **not used**: they all lead to "continue" and carry zero information.
