# 术语表

[English](/.agents/se/contracts/i18n/terminology.md) | 中文

本表是本仓库中英双语文档的术语真源，本身也是配对文档：两侧行一一对应，「中文」列在两侧都给出中文术语。配对约定见 [README.zh.md](/.agents/se/contracts/i18n/README.zh.md)。

**通用规则：**

- 「中文」列是中文正文的默认用词。该列写英文时，中文正文保留英文不翻译。
- 「首现括注」列非空时，只在全文首次出现处按该列书写，之后只写「中文」列的主词，不再重复括注。
- 「用法约束」列是词条的一部分：同一概念在产品文案、代码标识符与叙述文字中的写法可能不同，不能只改其中一处。
- 未收录的术语按 [translation-rules.zh.md](/.agents/se/contracts/i18n/translation-rules.zh.md) 处理：保留英文，或采用有出处的中文通行译法，不得即兴造词。

## 决策与门禁

| English | 中文 | 首现括注 | 用法约束 |
|---|---|---|---|
| decision | 决策 | | 一条必须一直满足的约束及其理由；不译作「决定」。 |
| decision record | 决策记录 | | 决策树下的一篇记录；不译作「决策日志」「决策文档」。 |
| decision audit | 决策审计 | | 只读巡检技能；不写成「决策检查」（后者是 `decision-check` 的三态建议）。 |
| gate | 门禁 | | 由机器执行、会阻断的检查；不译作「关卡」「校验器」。 |
| rule ID | 规则 ID | | 门禁输出里的 `[P1]`、`[S7]` 标记；前缀与数字不译。 |
| anchor | 锚点 | | 代码或文档中指向决策记录的索引注释；不指双语切换行。 |
| anchor convention | 锚点约定 | | `anchor-convention.md` 的 A/L 组规则：代码锚点与链接。 |
| scope | 作用域 | | 决策记录的一节，界定约束管到哪；需求字段 `scope` 写「适用范围」。 |
| lifecycle | 生命周期 | | 决策记录 `proposed`／`implemented`／`rejected`／`archived` 四段；不译作「生命周期阶段」。 |
| proposed | 提案 | | 正文写「提案」；目录名 `proposed/` 保留英文。 |
| implemented | 已落地 | | 状态行写「已落地」；目录名 `implemented/` 保留英文。 |
| rejected | 已否决 | | 状态行写「已否决」；目录名 `rejected/` 保留英文。 |
| archived | 已归档 | | 冻结保存，不再修改；目录名 `archived/` 保留英文。 |
| contract | 契约 | | 可执行、可被门禁检查的约束；不译作「合同」「协议」。 |
| unchecked items | 未自动检查 | | 门禁固定的结尾段；不译作「未检查项」。 |
| review | 评审 | | 机器查不了的部分由评审负责；不译作「复审」。门禁「未自动检查」固定段保留 `需 review` 字样，属固定产品文案。 |

## 需求与 ReqIR

| English | 中文 | 首现括注 | 用法约束 |
|---|---|---|---|
| requirement | 需求 | | 一条结构化需求；不译作「要求」。 |
| requirement spec | 需求 spec | | 字段名 `spec` 保留英文；正文写「需求 spec」。 |
| requirement record | 需求记录 | | 「中文」列用于正文；类型名 `RequirementRecord` 保留英文。 |
| semantic IR | 语义 IR | | 需求以结构化 IR 存储，而非 EARS 句子；IR 不译。 |
| EARS | EARS | EARS（Easy Approach to Requirements Syntax） | 需求语法缩写保留；不展开意译。 |
| preconditions | 前置条件 | | EARS `WHILE` 的载体；多个条件为合取。 |
| stimulus | 刺激 | | EARS 术语；不译作「触发器」。 |
| trigger | 触发 | | 指 `stimulus` 内的 actor/action/object；与 stimulus 分开用词。 |
| subject | 主体 | | EARS 的 `SHALL` 执行者。 |
| responses | 响应 | | 一条或多条 `SHALL` 内容。 |
| candidate | 候选 | | 新建需求的默认状态。 |
| confirmed | 已确认 | | 需用户证据；不译作「确认过」。 |
| deprecated | 已弃用 | | 不可变且 ID 不复用；不译作「废弃」。 |
| confirmation | 确认 | | 专用动作；不译作「审批」。 |
| deprecation | 弃用 | | 动作名；状态写「已弃用」。 |
| tag | 标签 | | 正文写「标签」；`tag` 字段、参数名与集合 ID 保留英文。 |
| collection | 集合 | | 一个命名需求集；不译作「库」。 |
| ID | ID | | 程序分配、单调递增、不复用；不译作「编号」。 |
| port | 端口 | port | 领域模型只依赖的持久化抽象；不译作「接口」。 |
| adapter | 适配器 | | 实现端口或集成外部系统的包。 |
| store | 存储 | | 不译作「仓库」。 |
| render | 渲染 | | 把语义 IR 呈现为文本；不译作「生成」。 |
| classify | 分类 | | `classifyRequirement` 是代码名，正文写「分类」。 |
| EARS pattern | EARS 模式 | | 由 IR 派生，不持久化。 |
| evidence | 证据 | | 用户确认或转移理由的凭据；`evidence[]` 与 `reference` 字段保留英文。 |

## 工作流活动

| English | 中文 | 首现括注 | 用法约束 |
|---|---|---|---|
| workflow | 工作流 | | 需求分析的活动状态机；不译作「流程」。 |
| activity | 活动 | | 工作流的一个状态；大写常量如 `REQUIREMENT_ANALYZING` 保留英文。 |
| transition | 转移 | | 活动之间的移动；不译作「跳转」。 |
| transit | transit | | 唯一触发转移的工具名，中文正文保留英文。 |
| trace | 轨迹 | | 转移记录 `{ from, target, reason, evidence, turn, step }`；不译作「追踪」。 |
| user story | 用户故事 | | 需求发现阶段确认的行为需求单元。 |
| example mapping | 示例映射 | | 四色卡片讨论方法，方法名 `Example Mapping` 保留英文。 |
| four-color card | 四色卡片 | | 故事、规则、示例、问题四类卡片的统称。 |
| reason | 理由 | | `transit` 的必填参数，说明转移为何成立。 |
| exit criteria | 退出条件 | | 建议性的阶段完成条件；不译作「退出标准」。 |
| tool surface | 工具面 | | 某活动可见的工具集合；不译作「工具界面」。 |

## 插件与运行时

| English | 中文 | 首现括注 | 用法约束 |
|---|---|---|---|
| plugin | 插件 | | Cordis 插件实现；不译作「扩展」。 |
| bundle | bundle | | 保留英文；不译作「捆绑包」「组合包」。 |
| host half | 宿主半边 | | `src/index.ts` 一侧；不译作「宿主端」。 |
| client half | 客户端半边 | | 浏览器一侧；不译作「前端」。 |
| session | 会话 | | 不译作「对话」（对话是 `conversation`）。 |
| conversation | 对话 | | 用户与 agent 的往复内容；不译作「会话」。 |
| handoff | 交接 | | `/handoff` 命令名与标记保留英文；不译作「切换」。 |
| handback | 带回 | | 探索结论带回源会话；不译作「归还」。 |
| tool call | 工具调用 | | 不译作「工具请求」。 |
| card | 卡片 | | 回复末尾的内联示意卡；不译作「图卡」。 |
| divider card | 分隔卡片 | | 对话记录里标识命令的分隔卡。 |
| transcript | 文本记录 | | 会话渲染出的完整文本，区别于事件日志。 |
| turn | 轮次 | | 不译作「回合」。 |
| reply | 回复 | | 不译作「响应」（那是 ReqIR 的 responses）。 |
| composer | 输入区 | | 指输入组件；按钮类控件写「输入框」。 |
| draft | 草稿 | | 可编辑、发送前不生效的内容。 |
| preset | 预设 | | 「Agent 预设」整体保留 Agent 英文。 |
| profile | 配置档 | | DSH 的 profile；不译作「配置文件」。 |
| provider | 提供方 | | 泛指提供方时用「提供方」；模型厂商或网关写「提供商」。 |
| model | 模型 | | |
| reasoning effort | 推理强度 | | |
| settings | 设置 | | |
| sidebar | 侧边栏 | | |
| workspace | 工作区 | | |
| catalog | 目录 | | 模型目录、提供方目录；不译作「清单」。 |
| RPC | RPC | | |
| credentials | 凭据 | | |
| locale | locale | | i18n 语境保留英文；产品语言资源文件写「语言资源」。 |
| inline | 内联 | | 如「内联静态 HTML」；不译作「嵌入式」。 |
| Knowledge Explorer | 知识探索 | | 产品能力名：作为专名（包名、`/handoff` 话题）保留英文，指能力本身时写「知识探索」。 |

## 双语文档

| English | 中文 | 首现括注 | 用法约束 |
|---|---|---|---|
| pair | 配对 | | 指 `foo.md`、`foo.zh.md`、`foo.i18n.yaml` 三个文件。 |
| counterpart | 对侧文件 | | 配对中的另一侧；泛指「另一侧」时写「另一侧」。 |
| consistency record | 一致性记录 | | `foo.i18n.yaml`；不译作「同步记录」。 |
| section | 小节 | | 记录按标题小节计算 hash；不译作「章节」。 |
| heading slug | 标题 slug | | 记录键的组成单位，取自英文标题；slug 不译。 |
| language switcher | 语言切换行 | | H1 后的互链行；不译作「语言切换按钮」。 |
| structure mirror | 结构镜像 | | 两侧标题、表格、列表、代码块逐项对应。 |
| source of truth | 真源 | | 不译作「事实来源」「唯一来源」。 |
| terminology | 术语表 | | 指文件本身时保留 `terminology.md`。 |
| first occurrence | 首次出现 | | 括注只写一次，随内容移动。 |
| patch update | 补丁式更新 | | 按 diff 最小改动对侧；禁止整篇重译。 |
| fidelity | 忠实性 | | 两侧表达相同事实、告诫与语气。 |
| naturalness | 自然度 | | 目标语言读者读起来像母语技术写作。 |
| review ownership | 评审责任 | | 门禁未覆盖的质量由评审负责。 |
| pair state | 配对状态 | | `ok`、`missing`、`out-of-sync` 保留英文。 |

## 统计与观测

| English | 中文 | 首现括注 | 用法约束 |
|---|---|---|---|
| usage statistics | 使用统计 | | 统计内容被注入、读取、搜索、引用、编辑的情况；不译作「用量统计」。 |
| access layer | 使用层 | | injected、read、cited 等归因层的统称；层名保留英文。 |
| injection | 注入 | | Harness 在会话开始或请求前自动放入上下文的常驻内容；不译作「插入」。 |
| context tax | 常驻成本 | | 每个会话或每次请求为常驻内容支付的上下文开销；不译作「上下文税」。 |
| behavioral proxy | 行为代理 | | 用可观测行为间接反映内容影响；不声称因果。 |
| attribution | 归因 | | 把一次读取或引用归到具体内容项；不译作「归属」。 |
| citation | 引用 | | 模型文本点名路径或标题；属弱证据，单列。 |
| hot content | 热门内容 | | 窗口内有显式使用且会话数靠前的内容；不是价值判断。 |
| cold content | 冷门内容 | | 窗口内零显式使用的内容；是复查线索，不是删除授权。 |
| session log | 会话日志 | | `$DSH_HOME/sessions` 下的事件日志；不译作「会话记录」。 |
| worktree | 工作树 | | git worktree；与「工作区」（会话 cwd）区分。 |
| corpus | 语料 | | 一组会话日志的统称。 |
| exposure | 暴露 | | 内容在请求中被表示的情况（注入、列出、搜索、读取等）；计量写「暴露量」，与「使用」区分。 |
| follow-through | 后续动作 | | 读取之后可观测到、指向该内容的后续行为（如引用）；不声称因果。 |
| visitor | 来访 | | 从其他仓库经 `cd` 进入本仓库的会话；正文可写「来访会话」。 |
| evidence class | 证据类别 | | logged、parsed、inferred 三种证据强度的统称；取值保留英文。 |
| observed consumption | 观测到的消费 | | 文件被 read、bash-read 或作为技能加载；不含注入、搜索、引用与编辑。 |
| coverage | 覆盖率 | | 报告中已发现、纳入、排除、未解析与不完整会话的计数。 |
| unavailable | 不可用 | | 适配器不支持的指标状态；保留英文，不写成「不可获得」。 |
| unknown | 未知 | | 证据不支持判定时的状态；保留英文。 |
| eligible population | 合格总体 | | 每个行为指标的分母来源；不译作「合格人群」。 |
| capability flag | 能力标志 | | 适配器声明自己支持哪些证据与指标。 |
| content revision | 内容修订 | | 同一路径下内容的一版；注入载荷按内容摘要区分。 |
| inventory | 清点 | | 会话与内容项的清单；不译作「库存」。 |
| guidance content | 指导内容 | | `AGENTS.md`、决策记录、契约与技能说明。 |
| support artifact | 支持产物 | | 门禁脚本、翻译记录等不直接指导行为的文件。 |
| content version | 内容版本 | | 由内容摘要标识的一版内容；与路径一起构成统计身份。 |
| digest | 内容摘要 | | 内容的哈希标识；代码里保留 `digest` 字段名。 |
| composition cohort | 组成队列 | | 环境指纹相同的会话群；统计比率只在单个队列内计算，正文可简写「队列」。 |
| environment fingerprint | 环境指纹 | | 指令摘要集合、技能目录与工具面的组合哈希。 |
| exposure window | 暴露窗口 | | 内容版本从首次出现到被替换之间的会话区间。 |
| sample gate | 样本闸门 | | 按合格会话数控制计数、暂定比率与可报告比率的阶梯。 |
| provisional | 暂定 | | 报告状态；取值保留英文 `provisional`。 |
| reportable | 可报告 | | 报告状态；取值保留英文 `reportable`。 |
| self-contained report | 自包含报告 | | 不引用外部资源与网络的单文件 HTML 报告。 |
| baseline cohort | 基线队列 | | 由首次模型调用之前获得的环境定义的会话群；后续读取与加载不改变成员。 |
| environment interval | 环境区间 | | 会话内环境保持不变的区间；中途变化开启新区间。 |
| digest provenance | 摘要来源 | | injected-descriptor、read-payload、skill-payload 等摘要来源；验证前互不合并。 |
| canonicalizer | 规范化器 | | 把观测载荷映射到规范内容表示的、经过验证的转换。 |
| capability matrix | 能力矩阵 | | 查询服务必须提供的字段与能力清单及各自回退。 |
| availability interval | 可用区间 | | 某工作区内内容版本被证实可用的区间，可为多个且不连续。 |
| opportunity denominator | 机会分母 | | 只有存在可用性证据时才成立的可读机会分母。 |
| display policy | 展示策略 | | 控制百分比是否展示的约定；与合规或产品动作阈值区分。 |
| counts-only | 仅计数 | | 低于最小观测数时的展示状态；取值保留英文。 |
