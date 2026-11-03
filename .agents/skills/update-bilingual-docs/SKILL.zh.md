---
name: update-bilingual-docs
description: 用户显式要求完整的双语翻译或配对复核流程时使用。例程编辑不走本技能；只有用户点名调用时才运行，按双语契约做逐小节翻译、补丁式更新、结构校验与重录。
---

# update-bilingual-docs：完整翻译与配对复核

[English](/.agents/skills/update-bilingual-docs/SKILL.md) | 中文

**只在用户显式调用时运行。** 日常改动按[配对约定](/.agents/se/contracts/i18n/README.zh.md)单遍更新两侧即可，不需要本技能。本技能承载更重的机制，不改变规则，也不放宽配对约定。

## 触发

- 用户要求「完整翻译」「把这篇翻成中文」「逐段复核这对文档」，或点名本技能。
- 新建一篇还没有对侧文件的文档，且用户要一次成对产出。
- 不要因为「这里需要翻译」自行加载；那是例程。

## 不变量

1. 两种语言同权，改动可以用任一语言撰写，被编辑的一侧是本次更新的源。
2. 一对文档是三个同目录文件：`foo.md`、`foo.zh.md`、`foo.i18n.yaml`，整体合并。
3. 禁止整篇重译来应用一次更新；已有对侧一律按 diff 打最小补丁。
4. 结构镜像与代码块逐字一致由门禁检查；门禁之外的质量由评审负责。

## 输入

二选一（或都读）：

- 被编辑一侧及其 diff：`git diff -- <file>`
- 新建文档的英文源

## 步骤

1. **读真源。** 读[配对约定](/.agents/se/contracts/i18n/README.zh.md)、[翻译规则](/.agents/se/contracts/i18n/translation-rules.zh.md)、[术语表](/.agents/se/contracts/i18n/terminology.zh.md)。术语表在动手前加载，不是遇到生词才查。
2. **定位改动粒度。** 按 diff 找出变化的小节与 Markdown 单元（段落、表格行、列表项、标题），逐小节对照，不重读未变化的部分。外部只改一侧、或工作区没有可用的 `git diff` 基线时，先运行 `node .agents/se/scripts/docs/translation-hints.ts <pair>`：它只输出 changed sections 与 terminology，不判断译文。只补它列出的 changed sections，其余保持已评审措辞；术语按[术语表](/.agents/se/contracts/i18n/terminology.zh.md)，未收录的词用 `node .agents/se/scripts/docs/translation-hints.ts --term <word>` 查先例，工具只给证据，选词仍由你判断。
3. **写对侧。** 已有对侧只改与 diff 对齐的最小范围，保持其余已评审措辞；新文档逐小节翻译，写完一节就锁定该节结构，不在末尾统一修结构。
4. **机械校验。** 代码块与行内代码逐字节照抄；标题层级、列表、表格、链接顺序与对侧对齐；成对文档链接按 locale 改写（英文侧 `/<path>.md`，中文侧 `/<path>.zh.md`，仓库根相对带前导 `/`）。
5. **重录。** `node .agents/se/scripts/docs/verify-translation-pairing.ts --write <pair>`，只点名本次确认过的配对；需要全量重录时显式用 `--write --all`。
6. **检查。** `node .agents/se/scripts/docs/verify-translation-pairing.ts <pair>`；PR 前再跑一次全语料。发现按四段式读出并修到全绿。
7. **声明。** 在回复或 PR 描述里写清确认了哪些配对、哪些是新建、哪些是补丁更新、术语表是否改了；并输出门禁的「未自动检查」四项（R1 译文忠实性、R2 术语一致性、R3 中文自然度、R4 行内代码、列表与表格顺序、图片替代文本与呈现、强调；清单：`.agents/se/contracts/i18n/translation-rules.md`）。全绿不等于译文合格。

## 输出

- 对侧文件与更新后的 `*.i18n.yaml`。
- 一段简短报告：配对路径、改动类型（新建／补丁）、遗留的「待定术语」。

## 边界

- 只处理文档，不改源码，也不改文档之外的实现文件。
- 配对范围以[配对约定](/.agents/se/contracts/i18n/README.zh.md)为准：任意目录下的 `README.md`、`docs/`、决策记录树、`.agents/se/` 文档与 `components/` 的 Markdown，单语的组件片段除外。
- 忠实性、术语、自然度、列表与表格顺序、行内代码、强调标记这些门禁查不了的事不因全绿而省略；报告里明说。
- 新增或修改术语的，在同一次变更里更新[术语表](/.agents/se/contracts/i18n/terminology.zh.md)；术语表本身也是配对文档，同样要带对侧。
- 发现约定本身有问题时报告给用户，不自行修改[配对约定](/.agents/se/contracts/i18n/README.zh.md)。
