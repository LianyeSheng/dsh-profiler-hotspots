---
name: decision-audit
description: Starting from the current decisions, checks whether code, documents and implementation still honor them. Use after a large change, at a phase wrap-up, or when the user asks for a sweep of decision drift, dead decisions, technical debt or the bypass rate. Read-only — it fixes nothing.
---

# decision-audit: Drift inspection

English | [中文](/.agents/skills/decision-audit/SKILL.zh.md)

`decision-check` follows a change to the decisions; audit reverses that and **asks the decisions about the implementation**. Before starting, read [the note format](/.agents/se/contracts/note-format.md) and [the review checklist](/.agents/se/contracts/review-checklist.md).

**Read-only. Touches no records, no code and no comments.**

Reading records follows [the workflow contract](/.agents/se/contracts/workflow.md): in a request folder only the `proposal` pair is a record, while `discuss-*` / `reply-*` are non-binding evidence; final approval happens in direct conversation between the human and the proposal author. Review contributions and the reply format are in [the note format](/.agents/se/contracts/note-format.md); a read-only skill changes neither evidence nor records. Preserve disagreement and do not treat an author's reply or a green gate as reviewer confirmation.

## What the gates already cover, this skill does not check

| Already guaranteed by the gates | Owner |
|---|---|
| Record format, status and directory consistency | The decision gate |
| Link validity | The link gate |
| Staleness hint when a referenced file changes | The link gate's L4 warning |

**Do not repeat the gates' work.** The audit's value lies where the gates cannot reach.

## Checklist

### 1. Dead decisions

A record under `implemented/` has lost all its code anchors and implementation, and the constraint is no longer enforced. Decide whether it should be archived or deleted, and hand that to `decision-revise`.

### 2. Orphan implementation

Code about security, privacy, invariants or constant conditions that no decision claims.

**This is the item unique to this skill** — it is a whole-repository reverse sweep, not an attribute of the current change. When found: either write a retrospective decision or confirm it is genuinely trivial and record that.

### 3. Still in force after archiving

An archived record's constraint still runs in the code. That means the archiving call was wrong — either restore it to `implemented/` or change the implementation.

### 4. Bypass rate

Count the frequency and reason distribution of `Decision process: bypassed` in commit messages. Older commits use the Chinese marker `决策流程: 绕过`; count it too, or historical bypasses are missed.

- A low bypass rate → the process is not in the way;
- **A high bypass rate is not a discipline problem but a criterion problem** — the three-class judgment in `AGENTS.md` is cut wrong; fix the criterion, not the discipline.

```bash
git log --format='%h %s%n%b' | grep -cE 'Decision process: bypassed|决策流程: 绕过'
```

### 5. Debt phase transition

Debt is not a static score but **the distance between the current implementation and the reasonable implementation re-derived from the current decisions**. Premature abstraction has its own cost, so act only when that cost crosses a threshold.

Watch only the signals that change the role; do not score periodically:

| Signal | Meaning | Action |
|---|---|---|
| **Re-touch** | Bridge code starts being touched repeatedly by changes outside the endpoint decision | Consider promoting it to a decision |
| **Rule of three** | One compromise appears in three or more places | Consider extracting it into a constraint |
| **Hub density** | One location carries several decisions | Consider merging the decisions |
| **Re-derivation survival** | How much of the current structure survives after re-deriving from the current decisions | Survives little → refactoring candidate |

Of the four, **only the rule of three can be mechanized** (grep for repeated patterns). The other three need judgment.

### 6. Record compliance

Missing motive, missing scope, an undecidable constraint — run `J2` from [the review checklist](/.agents/se/contracts/review-checklist.md) over them. Format problems belong to the gates and are not repeated here.

### 7. Dangling proposals

A proposal under `proposed/` that nobody has pushed for a long time and whose direction is stale is handed to `decision-revise` to reject (`proposed → rejected`) or to push forward. **Proposals are never archived.**

## Output

Two levels:

```markdown
audit：<范围>

阻塞观察
  <失效的约束 / 归档后仍生效 / 记录与实现矛盾>
  → 会破坏整个追踪基础，优先处理

工作项
  <无主实现 / 死决策 / 债务相变 / 记录缺陷>
  → 记录侧交 decision-revise，实现侧等用户授权
```

When nothing is found, print one line: `audit：无漂移` (no drift).

## Boundaries

- Reads code, records, documents and git history only.
- **A judgment must give its grounds and confidence; when unsure, list it as an observation and do not force a conclusion.**
- Findings stay in the report and are not written into records directly. Only promotion to a constraint or a resulting decision change goes through `decision-revise`.
- No periodic score statistics.
