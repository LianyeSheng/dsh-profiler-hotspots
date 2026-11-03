---
name: decision-intake
description: Use when the user proposes a new feature, a new idea or a new requirement, or asks whether an approach conflicts with the existing design. Turn a vague request into decidable candidate constraints, compare them with the current decisions to find conflicts and limits, lay out the ladder of ways forward, and hand the ruling to the user. Read-only — it changes neither code nor records. Use decision-check instead for a change that has already started modifying code.
---

# decision-intake: Request admission

English | [中文](/.agents/skills/decision-intake/SKILL.zh.md)

This skill handles "should we do it, and what must it satisfy", before any code is written. A request is usually just a direction — "faster", "don't add a heavy dependency", "add automatic backfill" — so first turn it into constraints that can be judged, then compare it with the current decisions.

**Read-only. It changes neither code nor records directly.**

Reading records follows [the workflow contract](/.agents/se/contracts/workflow.md): in a request folder only the `proposal` pair is a record, while `discuss-*` / `reply-*` are non-binding evidence; final approval happens in direct conversation between the human and the proposal author. Review contributions and the reply format are in [the note format](/.agents/se/contracts/note-format.md); a read-only skill changes neither evidence nor records. Preserve disagreement and do not treat an author's reply or a green gate as reviewer confirmation.

## Step 1: Read the source of truth

Read [the note format](/.agents/se/contracts/note-format.md) to learn the record format, then walk every record under the decision tree's `proposed/` and `implemented/` lifecycles.

**Do not substitute memory for records.** If the decision tree does not exist, the conflict surface is currently invisible: report that and suggest running `decision-revise` initialization first instead of guessing.

Records under `rejected/` are read on demand — they are vaccines; read them only when the request is exactly the direction that was rejected.

## Step 2: Turn the request into candidate judgments

A request is pressure; a judgment is a constraint. Translate the user's words into the form "must never …" and confirm each one with the user:

| What the user says | Candidate judgment |
|---|---|
| "Could we add scheduled backfill?" | "Proactive backfill must be a separate process and must never enter the daemon loop." |
| "The logs are too noisy." | "Production logs record counts and structure only, never content." |

**Do not dress a soft preference up as a universal rule.** A preference may drive the choice, but the report must say whether it is about performance, privacy, maintainability or personal taste.

## Step 3: Compare against scopes

Read each current decision's `## Scope` section and decide whether a candidate judgment falls inside it. **No anchor does not mean no constraint** — new code never carries an anchor.

For each decision that matches, give a conclusion:

| Conclusion | Meaning |
|---|---|
| **Conflict** | The new judgment and the existing constraint cannot hold together |
| **Limited** | It can be satisfied, but the existing constraints shape how it is implemented |
| **Harmless** | Inside the scope, and the two are compatible |

## Step 4: Conflict exits, strictly in order

When a conflict is found, look for a way out in this order, and **write out every exit**, not just the recommended one:

1. **Coexistence construction** — design a solution under which both sides hold. Write the sketch and its cost. This is the best answer because it leaves the decision set untouched.
2. **Revise the judgment** — say which decision changes, why, and what consequences it leaves. Hand it to `decision-revise` to land through the proposal process.
3. **Reject the request** — say which side cannot yield. Rejections that keep recurring can settle into non-goals.

## Step 5: Report

Fixed structure:

```markdown
intake：<需求一句话>

候选判断：
  - <不得……>
  - <不得……>

命中决策：
  <决策链接>  冲突 —— <依据>
  <决策链接>  受限 —— <依据>
  <决策链接>  无碍

出路（按序）：
  1. 并存构造：<草图 + 代价>
  2. 修订判断：<改哪条、为什么、后果>
  3. 拒绝需求：<哪一方不能让>

建议：<需要新决策 / 需要修订 / 可直接实现>
```

When nothing matches, print one line `intake：无冲突` (no conflict) and give a draft of the new decision.

## Boundaries

- Writes no code and changes no record directly.
- Does not rule on a value conflict for the user — lay out both sides' motives and costs, then stop.
- A request never becomes a second ledger: an accepted request enters the motive of the decision it drives, a rejected one enters the revision reasoning or the non-goals.
- Deciding whether something counts as a new decision uses `J1`, see [the review checklist](/.agents/se/contracts/review-checklist.md).
