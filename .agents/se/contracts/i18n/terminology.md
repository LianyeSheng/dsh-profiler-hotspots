# Terminology

English | [中文](/.agents/se/contracts/i18n/terminology.zh.md)

This table is the terminology source of truth for this repository's English–Chinese documents, and it is itself a bilingual pair: both sides carry the same rows, and the Chinese column gives the Chinese term on both sides. The pairing contract is in [README.md](/.agents/se/contracts/i18n/README.md).

**General rules:**

- The Chinese column is the default wording for Chinese prose. When the column holds an English term, Chinese prose keeps that English term untranslated.
- When the first-occurrence gloss column is non-empty, use it only at the term's first occurrence in the document; afterwards write the Chinese-column term without the gloss.
- The usage-constraint column is part of the entry: the same concept may be written differently in product copy, code identifiers and narrative text, and you must not change only one of them.
- Terms not listed here follow [translation-rules.md](/.agents/se/contracts/i18n/translation-rules.md): keep the English term, or use an established Chinese rendering with a citable source; never coin one on the spot.
## Decisions and gates

| English | Chinese | First-occurrence gloss | Usage constraint |
|---|---|---|---|
| decision | 决策 |  | A constraint that must always hold, together with its rationale; not 决定. |
| decision record | 决策记录 |  | A record in the decision-record tree; not 决策日志 or 决策文档. |
| decision audit | 决策审计 |  | The read-only inspection skill; not 决策检查 (that is the three-state advice of `decision-check`). |
| gate | 门禁 |  | A machine-executed check that blocks; not 关卡 or 校验器. |
| rule ID | 规则 ID |  | The `[P1]`, `[S7]` marker in gate output; the prefix and number are not translated. |
| anchor | 锚点 |  | An index comment in code or documentation that points at a decision record; it is not the language switcher. |
| anchor convention | 锚点约定 |  | The A/L rule groups of `anchor-convention.md`: code anchors and links. |
| scope | 作用域 |  | The decision-record section that bounds where a constraint applies; the requirement field `scope` is written 适用范围. |
| lifecycle | 生命周期 |  | The four states of a decision record, `proposed`/`implemented`/`rejected`/`archived`; not 生命周期阶段. |
| proposed | 提案 |  | Prose says 提案; the directory name `proposed/` stays English. |
| implemented | 已落地 |  | The status line says 已落地; the directory name `implemented/` stays English. |
| rejected | 已否决 |  | The status line says 已否决; the directory name `rejected/` stays English. |
| archived | 已归档 |  | Frozen and no longer edited; the directory name `archived/` stays English. |
| contract | 契约 |  | An executable constraint that gates can check; not 合同 or 协议. |
| unchecked items | 未自动检查 |  | The fixed closing block of a gate; not 未检查项. |
| review | 评审 |  | A human owns what a machine cannot check; not 复审. The gate's fixed 未自动检查 block keeps 需 review verbatim as fixed product copy. |

## Requirements and ReqIR

| English | Chinese | First-occurrence gloss | Usage constraint |
|---|---|---|---|
| requirement | 需求 |  | One structured requirement; not 要求. |
| requirement spec | 需求 spec |  | The field name `spec` stays English; prose writes 需求 spec. |
| requirement record | 需求记录 |  | The 中文 column applies to prose; the type name `RequirementRecord` stays English. |
| semantic IR | 语义 IR |  | Requirements are stored as a structured IR rather than EARS sentences; IR is not translated. |
| EARS | EARS | EARS（Easy Approach to Requirements Syntax） | The requirements-syntax acronym stays; do not expand or paraphrase it. |
| preconditions | 前置条件 |  | The carrier of EARS `WHILE`; multiple conditions are a conjunction. |
| stimulus | 刺激 |  | An EARS term; not 触发器. |
| trigger | 触发 |  | The actor/action/object inside `stimulus`; worded separately from stimulus. |
| subject | 主体 |  | The `SHALL` actor of EARS. |
| responses | 响应 |  | One or more `SHALL` statements. |
| candidate | 候选 |  | The default state of a new requirement. |
| confirmed | 已确认 |  | Requires user evidence; not 确认过. |
| deprecated | 已弃用 |  | Immutable and the ID is never reused; not 废弃. |
| confirmation | 确认 |  | The dedicated action; not 审批. |
| deprecation | 弃用 |  | The action name; the state is written 已弃用. |
| tag | 标签 |  | Prose writes 标签; the `tag` field, parameter names and collection IDs stay English. |
| collection | 集合 |  | One named requirement set; not 库. |
| ID | ID |  | Assigned by the program, monotonically increasing, never reused; not 编号. |
| port | 端口 | port | The persistence abstraction the domain model depends on; not 接口. |
| adapter | 适配器 |  | A package that implements a port or integrates an external system. |
| store | 存储 |  | Not 仓库. |
| render | 渲染 |  | Present the semantic IR as text; not 生成. |
| classify | 分类 |  | `classifyRequirement` is a code name; prose writes 分类. |
| EARS pattern | EARS 模式 |  | Derived from the IR and not persisted. |
| evidence | 证据 |  | The record of user confirmation or of a transition reason; the `evidence[]` and `reference` fields stay English. |

## Workflow activities

| English | Chinese | First-occurrence gloss | Usage constraint |
|---|---|---|---|
| workflow | 工作流 |  | The activity state machine of requirement analysis; not 流程. |
| activity | 活动 |  | One workflow state; uppercase constants such as `REQUIREMENT_ANALYZING` stay English. |
| transition | 转移 |  | A move between activities; not 跳转. |
| transit | transit |  | The only tool name that triggers a transition; Chinese prose keeps it in English. |
| trace | 轨迹 |  | The transition record `{ from, target, reason, evidence, turn, step }`; not 追踪. |
| user story | 用户故事 |  | The unit of behavioral requirement confirmed during discovery. |
| example mapping | 示例映射 |  | The four-color-card discussion method; the method name `Example Mapping` stays English. |
| four-color card | 四色卡片 |  | The collective name for the story, rule, example and question cards. |
| reason | 理由 |  | The required `transit` argument that says why a transition holds. |
| exit criteria | 退出条件 |  | Advisory criteria for finishing a stage; not 退出标准. |
| tool surface | 工具面 |  | The set of tools visible to one activity; not 工具界面. |

## Plugins and runtime

| English | Chinese | First-occurrence gloss | Usage constraint |
|---|---|---|---|
| plugin | 插件 |  | A Cordis plugin implementation; not 扩展. |
| bundle | bundle |  | Stays English; not 捆绑包 or 组合包. |
| host half | 宿主半边 |  | The `src/index.ts` side; not 宿主端. |
| client half | 客户端半边 |  | The browser side; not 前端. |
| session | 会话 |  | Not 对话 (对话 is `conversation`). |
| conversation | 对话 |  | The back-and-forth between a user and an agent; not 会话. |
| handoff | 交接 |  | The `/handoff` command name and marker stay English; not 切换. |
| handback | 带回 |  | An exploration conclusion brought back to the source session; not 归还. |
| tool call | 工具调用 |  | Not 工具请求. |
| card | 卡片 |  | An inline diagram card at the end of a reply; not 图卡. |
| divider card | 分隔卡片 |  | The divider card that marks commands in a transcript. |
| transcript | 文本记录 |  | The full rendered text of a session, as distinct from the event log. |
| turn | 轮次 |  | Not 回合. |
| reply | 回复 |  | Not 响应 (that is ReqIR's responses). |
| composer | 输入区 |  | The input component; button-like controls are written 输入框. |
| draft | 草稿 |  | Editable content that has no effect before it is sent. |
| preset | 预设 |  | Agent 预设 keeps Agent in English. |
| profile | 配置档 |  | A DSH profile; not 配置文件. |
| provider | 提供方 |  | Use 提供方 when speaking generally; write 提供商 for a model vendor or gateway. |
| model | 模型 |  |  |
| reasoning effort | 推理强度 |  |  |
| settings | 设置 |  |  |
| sidebar | 侧边栏 |  |  |
| workspace | 工作区 |  |  |
| catalog | 目录 |  | Model and provider catalogues; not 清单. |
| RPC | RPC |  |  |
| credentials | 凭据 |  |  |
| locale | locale |  | Stays English in i18n contexts; product language resource files are written 语言资源. |
| inline | 内联 |  | As in 内联静态 HTML; not 嵌入式. |
| Knowledge Explorer | 知识探索 |  | The product capability name: keep it English as a proper name (package name, `/handoff` topic); write 知识探索 when naming the capability itself. |

## Bilingual documentation

| English | Chinese | First-occurrence gloss | Usage constraint |
|---|---|---|---|
| pair | 配对 |  | The three files `foo.md`, `foo.zh.md` and `foo.i18n.yaml`. |
| counterpart | 对侧文件 |  | The other side of a pair; when speaking generally write 另一侧. |
| consistency record | 一致性记录 |  | `foo.i18n.yaml`; not 同步记录. |
| section | 小节 |  | Records hash content per heading section; not 章节. |
| heading slug | 标题 slug |  | The unit of a record key, taken from the English heading; slug stays English. |
| language switcher | 语言切换行 |  | The cross-link line after the H1; not 语言切换按钮. |
| structure mirror | 结构镜像 |  | Headings, tables, lists and code blocks correspond item by item on both sides. |
| source of truth | 真源 |  | Not 事实来源 or 唯一来源. |
| terminology | 术语表 |  | When the file itself is meant, keep `terminology.md`. |
| first occurrence | 首次出现 |  | The gloss is written once and moves with the content. |
| patch update | 补丁式更新 |  | Minimal diff-based change to the counterpart; never re-translate the whole file. |
| fidelity | 忠实性 |  | Both sides state the same facts, caveats and tone. |
| naturalness | 自然度 |  | The target-language reader reads it as native technical writing. |
| review ownership | 评审责任 |  | Review owns the quality the gate does not cover. |
| pair state | 配对状态 |  | `ok`, `missing` and `out-of-sync` stay English. |

## Statistics and observation

| English | Chinese | First-occurrence gloss | Usage constraint |
|---|---|---|---|
| usage statistics | 使用统计 |  | How content is injected, read, searched, cited and edited; not 用量统计. |
| access layer | 使用层 |  | The collective name for attribution layers such as injected, read and cited; layer names stay English. |
| injection | 注入 |  | Resident content the Harness puts into context at session start or before a request; not 插入. |
| context tax | 常驻成本 |  | The context cost each session or request pays for resident content; not 上下文税. |
| behavioral proxy | 行为代理 |  | Indirectly reflect a content's influence through observable behaviour; no causal claim. |
| attribution | 归因 |  | Credit one read or citation to a specific content item; not 归属. |
| citation | 引用 |  | Model text names a path or title; weak evidence, listed separately. |
| hot content | 热门内容 |  | Content with explicit use and a top session count in the window; not a value judgement. |
| cold content | 冷门内容 |  | Content with zero explicit use in the window; a review clue, not permission to delete. |
| session log | 会话日志 |  | The event log under `$DSH_HOME/sessions`; not 会话记录. |
| worktree | 工作树 |  | A git worktree; distinct from 工作区 (the session cwd). |
| corpus | 语料 |  | The collective name for a set of session logs. |
| exposure | 暴露 |  | How content is represented in a request (injected, listed, searched, read and so on); the measure is 暴露量, distinct from 使用. |
| follow-through | 后续动作 |  | Observable behaviour after a read that points back at the content (such as a citation); no causal claim. |
| visitor | 来访 |  | A session that entered this repository from another one via `cd`; prose may write 来访会话. |
| evidence class | 证据类别 |  | The collective name for the three evidence strengths logged, parsed and inferred; the values stay English. |
| observed consumption | 观测到的消费 |  | A file was read, bash-read or loaded as a skill; excludes injection, search, citation and editing. |
| coverage | 覆盖率 |  | The counts of discovered, included, excluded, unresolved and incomplete sessions in a report. |
| unavailable | 不可用 |  | The metric state an adapter does not support; stays English, not 不可获得. |
| unknown | 未知 |  | The state when the evidence does not support a judgement; stays English. |
| eligible population | 合格总体 |  | The denominator source of each behavioural metric; not 合格人群. |
| capability flag | 能力标志 |  | A declaration by an adapter of which evidence and metrics it supports. |
| content revision | 内容修订 |  | One version of content at the same path; injected payloads are distinguished by content digest. |
| inventory | 清点 |  | A listing of sessions and content items; not 库存. |
| guidance content | 指导内容 |  | `AGENTS.md`, decision records, contracts and skill instructions. |
| support artifact | 支持产物 |  | Gate scripts, translation records and other files that do not directly guide behaviour. |
| content version | 内容版本 |  | A version of content identified by content digest; together with its path it forms the statistical identity. |
| digest | 内容摘要 |  | The hash identifier of content; code keeps the `digest` field name. |
| composition cohort | 组成队列 |  | A group of sessions with the same environment fingerprint; statistical rates are computed only within one cohort, and prose may shorten it to 队列. |
| environment fingerprint | 环境指纹 |  | The combined hash of the instruction digest set, the skill catalogue and the tool surface. |
| exposure window | 暴露窗口 |  | The session interval between a content version's first appearance and its replacement. |
| sample gate | 样本闸门 |  | The ladder that controls counts, provisional rates and reportable rates by eligible session count. |
| provisional | 暂定 |  | A report state; the value stays English, `provisional`. |
| reportable | 可报告 |  | A report state; the value stays English, `reportable`. |
| self-contained report | 自包含报告 |  | A single-file HTML report that references no external resource or network. |
| baseline cohort | 基线队列 |  | A session group defined by the environment observed before the first model call; later reads and loads do not change membership. |
| environment interval | 环境区间 |  | An interval within a session where the environment stays unchanged; a mid-session change opens a new interval. |
| digest provenance | 摘要来源 |  | Digest sources such as injected-descriptor, read-payload and skill-payload; they are not merged before validation. |
| canonicalizer | 规范化器 |  | A validated transformation that maps an observed payload to the canonical content representation. |
| capability matrix | 能力矩阵 |  | The fields and capabilities a query service must provide, with each fallback. |
| availability interval | 可用区间 |  | An interval in which a content version is proven available in a workspace; there may be several, non-contiguous. |
| opportunity denominator | 机会分母 |  | A readable-opportunity denominator that holds only when availability evidence exists. |
| display policy | 展示策略 |  | The convention controlling whether a percentage is shown; distinct from compliance or product-action thresholds. |
| counts-only | 仅计数 |  | The display state below the minimum observation count; the value stays English. |