# 决策记录格式契约

[English](/.agents/se/contracts/note-format.md) | 中文

> 这是 `decision-*` 技能与文档门禁 `python3 .agents/se/scripts/decisions/verify.py` 共用的唯一格式说明。格式问题回到本文件，不在别处复制规则。
>
> 每个要求是一个**规则 ID**。门禁失败时输出 `[P1]`、`[S7]` 这样的标记，指向本文件对应小节。

软件是决策的集合，实现是决策的结果。一条决策记录保存的是**必须一直满足什么**以及**为什么**——代码、测试、文档都是它的派生。

---

## 〇、双语

每条记录是一个双语配对：

| 文件 | 语言 | 标题 | 状态 | 章节 |
|---|---|---|---|---|
| `X.md` | 英文 | `# Decision: <title>` | `Status: <status>` | `## Problem` 等 |
| `X.zh.md` | 中文 | `# 决策：<标题>` | `状态：<状态>` | `## 问题` 等 |

两份文件在同一个请求文件夹（既有扁平记录在 `{lifecycle}/{class}/`）下，第 3 行互相链接（见 H3）。

**配对完整性与一致性记录（`.i18n.yaml`）由双语配对门禁 `node .agents/se/scripts/docs/verify-translation-pairing.ts --write <pair>` 负责，文档门禁不重复检查。** 那是随包分发的双语契约，规则在 `.agents/se/contracts/i18n/README.md`。

本节只规定：**每个语言版本的头部 token 和章节名必须与它的语言一致，不得混用。**

---

## 一、文件树

### P1 路径形状

```
.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-slug.md
.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-slug.zh.md
```

以上为继续支持的既有扁平记录。新记录采用 `.agents/notes/{lifecycle}/{class}/yyyy-mm-dd-slug/proposal.md` 与 `proposal.zh.md`，同层携带 `proposal.i18n.yaml`。一个文件夹一条决策；独立约束在同一请求分支用多个互链文件夹。只允许 proposal、discuss-<topic-slug>、reply-<same-topic-slug> 三件组与 chain.yaml，禁止未知文件与嵌套目录。只有 proposal 是记录，证据不是记录；计数按决策而非 Markdown 数。

**反例**：`.agents/notes/2026-09-03-x.md`（缺生命周期与 class）。

### P2 生命周期段合法

第一段必须是四个之一：

| 值 | 含义 |
|---|---|
| `proposed` | 提案：已写出、尚未实现（或只完成一部分） |
| `implemented` | 已落地：决策已交付，文件保持与代码一致 |
| `rejected` | 已否决：提案被讨论后拒绝 |
| `archived` | 已归档：曾是 implemented，不再指导未来工作，冻结保存 |

**目录即状态。** 决策的状态变化表现为文件移动，不表现为字段修改。

### P3 class 段合法

第二段取自封闭集合，门禁拒绝其他取值：

| class | 覆盖什么 |
|---|---|
| `architecture` | 交付源码的结构决定：包如何组织、运行时词汇是什么 |
| `process` | 源码周围的工具与流程：门禁、包管理、发布节奏 |
| `feature` | 新的、面向用户或模型的能力 |
| `bug-fix` | 修正缺陷，或补上复盘暴露的缺口 |
| `simplification` | 移除代码、行为或接口面，不新增能力 |
| `testing` | 测试基础设施与策略 |

`architecture` / `process` 的分界：**architecture 是我们要交付的源码，process 是源码周边的工具与流程。**

刻意不设 `refactor`——它和 `simplification` 重合，判别式「可观察行为变了吗」已经覆盖。

### P4 日期段合法

请求文件夹名（既有扁平记录的文件名）以 `yyyy-mm-dd` 开头，且是真实存在的日期。

日期 = 该主题**首次提出**的日期。新建时取当天；从旧台账迁移时从 git 历史取。

### P5 slug 段合法

请求文件夹名日期之后的剩余部分是小写字母、数字、短横线的英文短语，描述主题。中文版在 `.md` 前加 `.zh`，slug 不变。

**不用编号。** 编号是全局计数器，在并行工作中是协调点；跨引用一律用链接。

---

## 二、头部

双语的头部结构相同，只有 token 不同。英文版形态：

```markdown
# Decision: <title>

English | [中文](/.agents/notes/implemented/architecture/2026-09-03-x.zh.md)

Status: implemented

## Problem
```

中文版把 token 换成中文，切换行改成 `[English](<对方路径>) | 中文`。

### H1 标题行

第 1 行，按语言：

| 语言 | 形态 |
|---|---|
| 英文 | `# Decision: <title>` |
| 中文 | `# 决策：<标题>` |

标题是一句话的主题，不带编号、不带日期、不带状态。

### H2 第 2 行空行

### H3 语言切换行

第 3 行，链接到同一记录的另一语言版本：

```markdown
English | [中文](/.agents/notes/implemented/architecture/2026-09-03-x.zh.md)
```

```markdown
[English](/.agents/notes/implemented/architecture/2026-09-03-x.md) | 中文
```

链接用仓库根相对（前导 `/`），见第六节。

### H4 第 4 行空行

### H5 状态行与目录一致

第 5 行是状态行，取值由所在目录与语言共同决定：

| 目录 | 英文 | 中文 |
|---|---|---|
| `proposed/` | `Status: proposed` | `状态：提案中` |
| `implemented/` | `Status: implemented` | `状态：已落地` |
| `rejected/` | `Status: rejected — <one-line reason>` | `状态：已否决 — <一句话理由>` |
| `archived/` | `Status: implemented` | `状态：已落地` |

状态行**不带日期、不带括号**。日期在文件名里，其余在 git 里。

**被否决是唯一带内容的状态**——因为读者来这一行就是要看结论。归档不是第四种状态：归档的文件仍然是「已落地」，归档信息另有专行。

### H6 状态行唯一

全文只能有一个状态行，且必须在第 5 行。正文里提到状态时改用正文措辞，不要写成状态行。

### H7 归档行（archived 必填）

`archived/` 下的记录，在状态行下一行插入：

| 语言 | 形态 |
|---|---|
| 英文 | `Archived: YYYY-MM-DD` |
| 中文 | `归档：YYYY-MM-DD` |

### H8 归档行（非 archived 禁止）

只有 `archived/` 下的记录可以有归档行。

---

## 三、正文章节

章节名按语言固定，**不得混用**。

### S1 首章节是「问题」

第一个 `##` 章节必须是 `## Problem`（英文）或 `## 问题`（中文）。**问题先于方案**——没有写清问题就写方案，读者无法判断方案是否解决了对的东西。

### S2 proposed 必备章节

| 英文 | 中文 |
|---|---|
| `## Problem` | `## 问题` |
| `## Proposal` | `## 提案` |
| `## Scope` | `## 作用域` |
| `## Alternatives considered` | `## 考虑过的替代方案` |
| `## Acceptance criteria` | `## 验收标准` |
| `## Risks` | `## 风险` |

自由技术章节放在提案章节与作用域章节之间。

### S3 implemented 必备章节

| 英文 | 中文 |
|---|---|
| `## Problem` | `## 问题` |
| `## Decision` | `## 决策` |
| `## Scope` | `## 作用域` |
| `## Alternatives considered` | `## 考虑过的替代方案` |
| `## Consequences` | `## 后果` |

### S4 rejected 必备章节

只要求问题章节与提案章节。

正文**冻结**：保留提案当时写下的全部章节，不改写、不删减。结论在状态行，不写进正文。

### S5 作用域非空

用一句话说明这条决策管辖什么：

```markdown
## Scope
Every code path that handles a request (including middleware and the request branch of background tasks).
```

它是发现「落进作用域但没有锚点的新代码」的唯一依据，也是 `decision-check` 做前向检查的入口。

**写不成作用域的内容，说明它还构不成决策**——退回问题层。

### S6 考虑过的替代方案非空

每个真实备选一段，结论开头，后接它为什么输。

理由：**没有记录「它打败了什么」的决策会招来反复重翻**——这是决策记录存在的首要目的。

确实当时没考虑过备选的，写 `未记录（YYYY-MM-DD）` 并注明日期，门禁放行。

### S7 implemented 禁止提案期章节

`implemented/` 中禁止出现：

| 英文 | 中文 |
|---|---|
| `## Proposal` | `## 提案` |
| `## Plan` | `## 计划` |
| `## Migration plan` | `## 迁移计划` |
| `## Acceptance criteria` | `## 验收标准` |

提案期的规范语言出现在已落地的记录里，会让读者分不清现状与意向。改写方向见「状态迁移」。

### C1 问题分现象与代价

问题章节必须同时给出两层：

| 层 | 英文 | 中文 | 含义 |
|---|---|---|---|
| 现象 | `**Symptom**` | `**现象**` | 什么事件让它显现（可追溯的事实） |
| 代价 | `**Cost**` | `**代价**` | 不解决会损失什么（价值层） |

```markdown
## Problem

**Symptom**: On 2026-08-12 a payment callback timed out; synchronous log flushing pushed p99 to 3s under disk stalls.
**Cost**: Tail latency is a product promise that outranks implementation convenience.
```

**只有现象没有代价，不合格。** 问题不是客观存在的东西，是价值投射出来的——不重视就不构成问题，没有代价就没有决策理由。

### A1 archived 状态行

见 H5：归档记录的状态行是「已落地」。

### A2 archived 冻结

归档后**不得编辑、翻译、重排、移动、删除**，且**不得作为现行行为的依据**。

历史引用可以链进去，但那是引历史，不是引权威。

---

## 四、状态迁移

每次迁移都在**同一次变更**内完成，并重新满足目标生命周期的章节要求——否则门禁失败。**两个语言版本、证据和一致性记录一起迁移；同次修复当前入链、切换行与配对记录。历史 Git 路径和逐字引文保持原样。** 批准但未交付仍在 proposed；延期也留 proposed。提案头部用稳定角色或 handle 标明作者，交接以署名头部修改提交保留。

### proposed → implemented

实现落地时，同一个提交内：

1. `git mv` 整个请求文件夹到 `implemented/<class>/`，保留固定的 `proposal.md` 文件名与全部证据三件组；既有扁平记录三件组一起迁移
2. 状态行改为「已落地」
3. 提案章节改写成现在时的决策章节
4. 验收标准与风险折叠进后果章节（或一个现在时的验证章节）
5. 删掉计划，只留已交付的事实

### proposed → rejected

1. `git mv` 整个文件夹（或既有扁平三件组）到 `rejected/<class>/`
2. 状态行补一句话理由
3. 正文冻结，一个字不改

### implemented → archived

1. `git mv` 整个文件夹（或既有扁平三件组）到 `archived/<class>/`——**路径里没有 `implemented` 这一层**
2. 状态保持「已落地」
3. 状态行下插入归档行
4. 之后永久冻结

### implemented → 删除

只描述**小 UI 调整**或**纯机械改动**的，直接删文件并修复入链。

局部 bug 修复、性能改动、新能力、实质行为决策，**不因为实现规模小就符合删除条件**。

### 合并（被完全取代）

可把旧记录合并进新的 owner 并删除，前置条件：

- 保留旧记录的**每一个**独有理由、备选、后果、验证要求和已点名的覆盖缺口；
- 修复所有入链；
- 不完全取代不算——部分取代要保留两篇并互链。

**绝不允许把旧文件改写成它的反面。** 决策反了就是新决策 + 双向链接。

---

## 五、归档

归档的判断标准是语义的，不是字数或年龄：**决策已完成、不太可能再指导未来工作、但历史理由仍值得保存。**

归档后处理见 A2。

> **本契约不引入内容哈希清单。**
> 参照实现有 900+ 篇归档和公开发布仓库，需要防篡改证明。此处归档量小、仓库私有，**git 本身就是不可篡改证据**。
> 触发条件：归档超过 100 篇，或仓库需要对外发布时再引入。

---

## 六、跨引用

### 解析基准

**统一为仓库根。这是唯一约定。**

两种介质因语法差异写法不同，但这是**同一约定的两种拼写**，不是两套规范：

| 介质 | 写法 | 原因 |
|---|---|---|
| Markdown 内链 | `[标题](/.agents/notes/implemented/architecture/2026-09-03-x.md)` | 前导 `/` 是 GitHub 解析仓库根的要求；不带会被当成相对当前文件 |
| 代码注释 | `.agents/notes/implemented/architecture/2026-09-03-x.md` | 无前导 `/`，避免看起来像文件系统绝对路径 |

链接的有效性由独立的链接门禁 `python3 .agents/se/scripts/decisions/verify_links.py --staged` 检查，规则见 [anchor-convention.zh.md](/.agents/se/contracts/anchor-convention.zh.md)。

---

## 七、判断性要求

下面三项机器检查不了，由 [review-checklist.zh.md](/.agents/se/contracts/review-checklist.zh.md) 承担：

- **J1** 只有决策变化才写记录
- **J2** 一条记录 = 一条可独立判定「何时被违反」的约束
- **J3** 备选方案是真实备选，不是稻草人

门禁每次运行都会在输出末尾声明这三项未检查。


## 八、RFC 证据格式（E1–E6 与 C 组）

请求本身的流程由[工作流契约](/.agents/se/contracts/workflow.zh.md)陈述；格式以本契约为准，起草使用 [templates/](/.agents/se/templates/)。讨论与回复均为非约束性配对证据；只记录评审与回应，不发起裁决、批准、任务分派或继续工作。原话作为署名来源证据保留。评审者维护讨论，提案作者维护同 slug 的单独回复。

### E1 证据头部

`discuss-<topic-slug>` / `reply-<same-topic-slug>` 使用小写连字符 slug，每项为 `.md`、`.zh.md`、`.i18n.yaml` 三件组。H1 为 `# Discussion: <title>` / `# Reply: <title>`（中文 `# 讨论：<标题>` / `# 回复：<标题>`）。第 3 行是精确对侧切换行；第 2、4 行空白；第 5、6 行按序恰为 `Chain`、`Author`（中文 `Chain：`、`作者：`）。`Chain` 值为 `<request-date-slug>/<thread-slug>`；`Author` 人类使用当时的 `git config user.name`，agent 使用自身稳定标识。头部不得出现 `Evidence`、`Proposal`、`Discussion`、`Reviewed-*`、`Proposal-Digest`、`Result` 或人工贡献组，也不收自由文字。

### E2 讨论结构

只有 `## Context` / `## Findings`（中文「背景」／「问题条目」），顺序固定。背景说明评审范围与署名来源，不塞无 ID 的问题。每个条目是本语言可读的 H3 标题、Finding-ID、Kind、Blocking，后跟且仅跟四个 H4：Problem、Evidence、Impact、Suggestion（中文「问题」「证据」「影响」「建议」）。ID 在单个讨论内唯一，小写连字符；Kind 为 issue/question/suggestion，Blocking 为 yes/no。各节必须有实质文字，不能为空或 TODO/TBD/省略号占位；禁止额外章节和条目外文字。

### E3 提案引用

`discuss` 与 `reply` 块都必须含 `proposal` ref（见 C 组）。该 ref 的英文坐标（v1 为其 `en` 坐标）解析为本请求文件夹的决策记录 blob，标题为本语言的决策标题；v2 的中文 blob 由同一 commit 的派生 `.zh.md` 校验，v1 使用存储的 `zh` 坐标。生命周期段可以是历史位置，bootstrap 的扁平提案路径按同一 topic 身份归一。

### E4 回复覆盖

从回复文件解析 ID，回复 ID 集合必须等于当前同语言 `discuss-<slug>.md` 的 ID 集合，各一次；缺少、重复、多出均失败。回复不再引用历史讨论快照。

### E5 回复完整性

只有 `## Responses`（「回应」）。每条 H3 后依次 Finding-ID、Kind（与源相同）、Disposition、Resolution；然后只有四个 H4：Answer、Reason、Accepted part、Unaccepted part（「回答」「理由」「采纳部分」「未采纳部分」）。Answer 首句复述源关注点并直接回答；Reason 解释处置；拒绝部分保留争议原文短引。`accepted` 的采纳部分为实质内容、未采纳部分精确为 `none`；`partially-accepted` 两部分都有实质内容；`declined`/`deferred` 的采纳部分精确为 `none`、未采纳部分解释拒绝或延期。部分采纳、延期和拒绝阻塞问题必须 `unresolved`。拒绝的 Reason 以 `Decline-Class: out-of-scope/invalid/tradeoff` 起头并解释；延期的 Reason 含恰好一个非空 `Owner` 和 `Trigger` 并解释。未解决条目保留原因，不另开未决事项或下一步章节。结构完整的未解决回复可以通过，不是一致同意门禁。

### E6 双语身份

比较两语言的 `Author`、`Chain` 与 finding 级 Finding-ID、Kind、Blocking、处置、解决状态；chain 文件内 v2 的派生中文 blob 与 v1 的 en/zh 路径配对和同 commit 由 C3 校验。`Proposal-Digest` 不再存在。

### C 组：chain.yaml

每个含证据的请求文件夹一份 `chain.yaml`，随文件夹移动/归档冻结；没有证据的文件夹不需要。受限块式 YAML（仅映射与内联标量映射；禁止列表、锚点、引号、多行标量与尾注释）。读取器接受版本 1 与 2。`proposed/` 与 `implemented/` 按声明的 `version` 分派形状规则；`rejected/` 与 `archived/` 的 chain 文件由迁移转为 v2（chain 是簿记，冻结的证据正文不变），残留 v1 报 C1。没有迁移窗口，也不对活跃 v1 报版本错误。

版本 2 每条 ref 只存一个英文坐标，中文路径由 `.md` 派生为 `.zh.md`：

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

版本 1 保留 `en`/`zh` 双坐标：两者 `{commit, path}`，commit 相同，`zh` 路径为 `en` 路径加 `.zh.md`。v1 在 `proposed/` 与 `implemented/` 中永久有效；冻结文件夹的 chain 文件迁移为 v2。

- C0 请求文件夹名（`yyyy-mm-dd-slug`）在全部生命周期与 class 下唯一，使完整 ID 的搜索无歧义。
- C1 `chain.yaml` 仅在存在 discuss/reply 时出现；结构为 `version` + `threads`，版本为 1 或 2；`rejected/` 与 `archived/` 中必须为 2。
- C2 线程键与文件一一对应：每个 `discuss-<slug>` 有 thread，thread 必须有 discuss；`reply` 块与 `reply-<slug>.md` 同时存在或同时缺失。每个 discuss/reply 块至少一条 ref，且必须含 `proposal`。
- C3 ref 键为同文件夹文件名 stem（`proposal`、`discuss-*`、`reply-*`）；v2 的值为 `{commit, path}`，`path` 为英文 `<ref>.md`，同一 commit 的 `<ref>.zh.md` 必须解析为 blob；v1 的值为 `en`/`zh` 各 `{commit, path}`，两者 commit 相同。两版共同：commit 为完整 40 位小写 SHA、可解析为提交、是当前被检查提交的祖先；path 为安全的仓库相对路径、语言后缀正确、basename 与 ref 一致、按 topic 身份位于同一请求文件夹（生命周期段可历史；bootstrap 扁平提案例外）；`commit:path` 解析为对应类型的 Markdown blob。
- C4 正文引用标记：`Chain <ref> [L<a>-L<b>]` 必须解析到所在文件自己的 ref 块；行段为引用文件语言的行号（v2 中文用派生路径，v1 用存储的 `zh` 坐标），且不越出被引用 blob。

校验器不联网 fetch；CI checkout 保留全部历史。不可用历史是诊断错误。

### 派生概览与引用 CLI

门禁输出逐问题只读概览（讨论路径、ID、Kind、Blocking、处置、作者解决状态、验证状态、回复路径）；作者闭合不等于审阅者确认，缺少可归属确认时保持 `unverified`。`python3 .agents/se/scripts/decisions/chain.py` 以完整 ID `<request>/<thread>/<discuss|reply>/<ref>` 提供只读的 `refs`、`show [L<a>-L<b>] [--locale en|zh]`、`diff`，无网络，并打印对应 `git show` 命令；默认 `--locale en`，v2 的 `--locale zh` 使用同一 commit 的派生路径，v1 使用存储的 `zh` 坐标。同一脚本另有 `add`、`modify`、`delete` 编辑子命令：默认 dry-run 打印目标与 unified diff，`--write` 原子替换，写 v2 并在同一次写入中转换可无损映射的 v1，拒绝冻结文件夹与不可映射 v1，写前校验 v2 形状、双语 blob、祖先与 C2 对应；编辑只改 `chain.yaml`。`python3 .agents/se/scripts/decisions/migrate_chain.py` 一次性把可无损映射的 v1 转为 v2（包括冻结文件夹中的链簿记，不改变冻结证据正文），默认 dry-run，`--write` 原子替换；不可映射的文件保持 v1 并继续有效。门禁只读，不调用编辑命令；门禁不比较修订新鲜度，引用是否仍然切题由评审负责。

## 九、提案示例（X1–X5）

### X1 提案覆盖

新增或修改的 proposed 记录在文档层至少有一个标记示例，不要求每节都有。未变更的旧提案和冻结归档不追补。CI 与本地调用相同校验器；本地以索引与 HEAD 比较，CI 显式传 --base。

### X2 标记语法

代码围栏外用 `<!-- example:begin id=timeout-flow kind=walkthrough mode=optional -->` 与 `<!-- example:end id=timeout-flow -->` 包围示例。属性恰为 id、kind、mode 且顺序固定；ID 为唯一的小写连字符短语，两侧共享；kind 为 walkthrough/discuss/reply/counterexample，mode 为 optional/when-needed。不得嵌套、重叠、不闭合或重复。围栏内的语法示意不计数。

### X3 实质内容

示例体不得为空、纯空白、纯占位或仅一条占位 SHA。示例中的虚构提交和路径可保留，不需解析 Git。

### X4 类型化样例

discuss/reply 样例体为一个引用文档，说明文字放标记外。去除引用前缀和展示反引号后，复用 E1/E2/E5 结构解析：本语言头部（Chain、Author）、ID、枚举和四段正文完整，不解析虚构 Git 来源或执行命令。counterexample 标明预期检查及通过／失败，不按有效证据强制通过。walkthrough 可叙述具体流程。CI 不评价教学质量、例子密度或段落是否需要示例。

### X5 双语对应

两侧示例的 ID、kind、mode、次序与类型化样例的问题 ID 对应。各自使用本语言格式，译文质量仍由 review。
