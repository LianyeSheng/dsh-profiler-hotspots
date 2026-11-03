# Review checklist

English | [中文](/.agents/se/contracts/review-checklist.zh.md)

> The three things a machine cannot check. Every gate run declares that it does not cover them; this checklist is their home.

The document gate `python3 .agents/se/scripts/decisions/verify.py` (including `document_validation.py`) being green **is not the same as** a qualifying record. It only guarantees the shape; only a reader can judge the three items below.

---

## J1 Write a record only when a decision changed

**Question**: does this change alter "what must always hold"?

| Situation | Write a record? |
|---|---|
| The decision changed (a constraint added, relaxed or overturned) | **Yes** |
| A pure implementation swap (constraints unchanged, only the approach changes) | **No** |
| A mechanical edit, a local edit, a local UI adjustment | **No** |
| A bug fix that exposes "we should have satisfied a constraint all along" | **Yes** |

**Why not write one**: the record tree's size must stop at the number of decisions, not grow to the number of commits. Among thousands of records, the dozens that truly bear re-reading get drowned.

**The cost of getting it wrong**: too many records dilute the tree and nobody reads it; too few and the next agent reinvents what you already worked out.

---

## J2 One record = one constraint whose violation can be judged independently

**Self-check question**: can you state under what circumstances this is violated?

- Yes → it qualifies
- No ("the system should be simple") → send it back to the `## Problem` level; it is not yet a decision

**Why**: decidability is the dividing line between a decision and a wish. A wish cannot be violated, so it cannot constrain any implementation.

**Common non-qualifying shapes**:

| Non-qualifying wording | Problem | Fix |
|---|---|---|
| "The system should be simple" | Cannot tell when it is violated | Write a concrete assertion, or go back to the problem level |
| "Watch performance" | No threshold, no scope | Write p99 ≤ 50ms plus the scope |
| "All modules must…" | Scope undefined | Say which modules |
| Three unrelated constraints crammed into one record | Cannot be judged independently | Split into three |

---

## J3 Alternatives are genuine alternatives, not straw men

**Self-check question**: among these alternatives, was there one I was genuinely torn about at the time?

- Yes → it qualifies
- All obviously bad ideas → it does not qualify; you are dressing up the conclusion

**What a good alternative looks like**: it has a real advantage you would have conceded something for. It is written as "where it wins, and what it loses by winning", not "where it is wrong".

**Counterexample**:

```markdown
- **用随机数决定架构。** 否决：太荒谬。
```

**Good example**:

```markdown
- **每条决策一个编号，编进单一台账。** 否决：编号是全局计数器，并行工作时是协调点，
  而且被指向的文件一移动就断链。但它赢在「短引用」——`#7` 比一长串路径好写，
  这一点我们靠「代码注释里只留一句复述 + 路径」部分补偿。
```

---

## Review output

A review produces no score, only **blocking items**:

```
复查：2 项阻塞

[J2] .agents/notes/implemented/process/2026-10-01-x.md
  `## 决策` 写的是「注意日志量」，无法判定何时被违反
  → 改成具体断言，或退回 `## 问题` 层

[J3] .agents/notes/proposed/architecture/2026-10-20-y.md
  `## 考虑过的替代方案` 只有一条明显荒谬的备选
  → 补一条你当时真的在犹豫的，或说明为什么没有
```

With no blocking items, print one line: `复查：通过`.

---

## Who executes it

| Occasion | Executor |
|---|---|
| After writing a new record, before committing | The agent that wrote it, self-checking |
| Pull-request review | The reviewer |
| Periodic audit at a phase boundary | The `decision-audit` skill (`.agents/skills/decision-audit/SKILL.md`) |

A machine does not check these three items, but **every gate run reminds the reader that they exist** — see the end of the `python3 .agents/se/scripts/decisions/verify.py` output.
