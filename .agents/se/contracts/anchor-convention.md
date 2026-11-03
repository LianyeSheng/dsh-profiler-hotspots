# Anchor and link contract

English | [中文](/.agents/se/contracts/anchor-convention.zh.md)

> Rule IDs share one numbering space with `.agents/se/contracts/note-format.md`. The single source for links and anchors.

## Why anchors are needed

**You cannot know which context to choose before choosing context.** Any instruction of the form "read the right thing first" requires the agent to possess information it does not have.

The only way out of that loop is to **put the index on the thing being read**. A code comment is not documentation; it is an index entry.

---

## 1. When to leave an anchor in code

### J4 Trigger condition (executed by review; a machine cannot check it)

When the following holds in code, it requires one sentence of why plus a link:

> **It could obviously be simpler and more direct, yet it deliberately is not.**

A reader will ask "why the detour here?" — that is exactly where the anchor belongs.

**Three cases that need no anchor:**

| Case | Reason |
|---|---|
| Already stopped mechanically by lint / a gate / a test | The gate fires, which is stronger than a comment |
| The code shape already shows it (type signature, constant name) | Repeating it is noise |
| Merely "inside some decision's scope" | That is `decision-check`'s job, not the index's job |

**The test tightens into one sentence: a reader would reasonably change this code, and a decision forbids or restricts that change.**

---

## 2. The shape of an anchor

### A3 Shape

One line, containing **why** + **the repository-root-relative path to the record**:

```python
# 故意保留同步读：日志已改异步刷盘，磁盘抖动风险已消除；放宽条件与实测数据见
# .agents/notes/implemented/architecture/2026-09-03-hot-path-sync-io.md
```

Three elements, none optional:

1. **Why** (one sentence, so a reader can judge whether the condition changed this time)
2. **Link** (a repository-root-relative path, without a leading `/`)
3. **Position** (near the module or function that actually enforces the constraint, not at the top of the file)

### A4 A bare prohibition does not qualify

```python
# 不要删除这个判断          ← 不合格：读者不知道为什么，遇到「更聪明的改法」就失效了
```

```python
# 故意保留：合并转发必须递归补全到 5 层，否则嵌套卡片会丢内容
# 见 .agents/notes/implemented/feature/2026-09-30-forward-depth.md   ← 合格
```

**A comment that states only a prohibition is overturned by "a cleverer approach".** With the why written down, a reader can judge whether the condition still holds.

---

## 3. Links

### L1 The resolution base is the repository root

Every reference inside the repository resolves against the **repository root**, not against the current file.

That is the only convention. It removes half of the "links break when files move" problem class — **an anchor does not break when its own code file moves; only the referenced record moving breaks it.**

### L2 Markdown links carry a leading `/`

```markdown
[rationale](/.agents/notes/implemented/architecture/2026-09-03-x.md)
```

The leading `/` is what GitHub requires to resolve from the repository root. Without it the path is taken relative to the current file.

**Counterexample**: `[x](.agents/notes/x.md)` inside a file under `.agents/se/` resolves to `.agents/se/.agents/notes/x.md` and breaks silently.

### L3 The link target must exist

`python3 .agents/se/scripts/decisions/verify_links.py` scans the whole repository and fails on an unresolved reference.

**Scan scope**: every text file in the repository, not only `notes/`. Markdown, code comments and script comments wherever they sit are in scope.

### L4 The referenced file changed in this change → hint (does not block)

If a link's target file appears in this commit's changed-file set, print a **warning**:

```
被引用的文件在本次提交中有改动，确认代码注释中的说明仍然成立
```

Reason: link validity is purely mechanical, but **whether the restatement still holds is semantic**. This turns stale-anchor discovery from a periodic sweep into a touch-time hint — **perception happens at the moment of touching, with no periodic census**.

The severity is warn, not error: the link is valid but the meaning may have changed, and that must not block the commit.

---

## 4. Gate behavior

What `python3 .agents/se/scripts/decisions/verify_links.py` checks:

| ID | Check | Severity |
|---|---|---|
| L2 | Whether a Markdown link carries the leading `/` | error |
| L3 | Whether the link target exists | error |
| L4 | Whether the referenced file changed in this change | warn |

**Resolution rule (the only one)**:

```
对每个仓库内链接：
  外部 URL（http/https/mailto）、页内锚点（#...） → 跳过
  以 / 开头 → 去掉前导 /，按仓库根解析
  代码注释中的 .agents/... 路径 → 按仓库根解析
  否则 → 报 L2（应为仓库根相对）
```

**Scan scope**: every text file in the repository (Markdown, code comments, script comments), not only `notes/`.

**Exclusions**: build-output directories such as `node_modules`, the `test` / `tests` / `__tests__` / `fixtures` directories, and `*.test.*` / `*.spec.*` files. The `.agents/notes/...` paths in tests are mostly synthetic and point at no real record.

**Severity split**: `L2` is an error inside `.agents/se/`, `.agents/notes/` and `.agents/skills/decision-*`, and a warning elsewhere. `L3` is an error everywhere, because a broken link is broken wherever it sits.

---

## 5. Three causes of broken links and how to handle them

| Cause | What the gate can do | Handling |
|---|---|---|
| The referenced record changed lifecycle | Report the position and the target | The agent locates the new path with `find` and fixes it |
| The record was merged or deleted | Report the position and the target | A human confirms where it went |
| A typo | Report the position and the target | The agent fixes it |

**The gate only reports the position; it never guesses the fix.** A wrong guess is worse than none — the agent would change the code to match the bad advice.

---

## 6. Division of labor with `note-format.md`

| File | What it governs |
|---|---|
| `note-format.md` | The record's own shape (P/H/S/C/A groups) |
| `anchor-convention.md` | References between records, code and documentation (A/L groups) |
| `review-checklist.md` | Judgments machines cannot make (J group) |
