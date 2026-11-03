# 工具包采用指南

[English](/.agents/se/README.md) | 中文

本工具包是一套用于 DeepSeek Harness（DSH）上 agent 辅助开发的可复用工作流：开发约定、应用这些约定的技能，以及校验产物是否合规的校验器。它以安装后的 `.agents/` 树加上仓库 `AGENTS.md` 中每个已选组件一个标记块的形式交付；工具包自身的源码从不被安装，任何出厂文件都不引用工具包作者的决策历史，安装完成后应用工作流不需要 `.agents/` 之外的任何路径。

采用是一条带 manifest 的本地克隆复制流程，不是发布安装产品。安装器离线运行、只用 Python 标准库；除显式应用外每个子命令都是 dry run；每个已安装文件都记录内容摘要；更新是从固定 kit 修订生成的可评审 diff。

## 工具包是什么

工具包交付三样东西：定义合规交付以及人工裁决权归属的约定；帮助 agent 应用这些约定的技能；以及校验产物中机器可查部分的校验器。契约规定可执行流程、记录格式、锚点约定与复查清单；技能按需应用它们；门禁校验器按固定顺序运行，并在结束时声明它没有检查什么。

工具包交付方法学，不交付项目内容。采用方的业务逻辑、项目指令与决策记录树仍归采用仓库所有：工具包不安装任何决策记录，也不导入任何决策历史。保留自有 `AGENTS.md` 的仓库保留其原文；安装器只追加自己的标记块。

已安装的载荷取决于所选组件：

| 已安装路径 | 内容 | 组件 |
| --- | --- | --- |
| `.agents/se/contracts/` | 工作流契约：可执行流程、记录格式、锚点约定与复查清单。 | `workflow` |
| `.agents/se/templates/` | 提案、讨论与回复的记录模板。 | `workflow` |
| `.agents/skills/<name>/` | 所选技能。 | `workflow` |
| `.agents/se/scripts/decisions/` | 决策、链接与锚点校验器。 | `workflow` |
| `.agents/se/contracts/i18n/` | 双语配对契约、翻译规则与术语表。 | `bilingual-docs` |
| `.agents/se/scripts/docs/` | 可选的双语配对门禁。 | `bilingual-docs` |
| `.agents/se/scripts/kit/install.py` 与 `.agents/se/README.md` | 安装器副本与本采用指南。 | `kit` |
| `AGENTS.md` 块 | 每个所选组件一个标记块。 | 所有所选组件 |

安装后的树是生成的。作者编辑工具包源码并重新生成；对安装副本的手工修改会被下一次渲染覆盖，并被作为漂移捕获。

指令、校验器根路径、示例与模板占位符中的 `.agents/notes/` 路径描述采用仓库自己的记录树，允许使用；工具包不复制记录，也不得依赖 se-tools 的开发历史。组件源码保留开发决策锚点，渲染时从已安装代码中移除。闭合检查在写入前拒绝指向记录树的具体 Markdown 链接及仍然指向该树的代码锚点。评审仍须检查正文是否依赖作者的历史。自安装与消费者安装渲染相同的组件字节与标记块；se-tools 开发者通过组件源码追溯开发决策。

## 必需核心与可选组件

必需核心是 `workflow`。它把契约、模板、决策技能、校验器及其测试作为一个完整功能来拥有。安装该组件即可交付完整的决策工作流。

`bilingual-docs` 与 `kit` 是可选组件。双语组件加入配对契约，并使采用仓库为其自有在范围文档配对；它的门禁需要 Node 24+，不装它时工作流其余部分照常运行。kit 组件把安装器副本与本指南安装到目标仓库，使目标仓库保留安装器与本指南；移除可在目标上执行，更新仍需从 kit checkout 运行。两个可选组件都不改变工作流的保证。

## 组件

每个功能组件拥有自己的 `components/<id>/registry.json`，声明后果、前置条件、片段及从组件目录解析的源码到安装路径映射。这些本地注册表是唯一选择来源，不设中央注册表。安装器发现组件后按依赖排序，同时就绪的组件按 id 排序。工具包修订只在 `components/kit/registry.json` 中声明。安装器在写入前打印每个所选组件的后果与前置条件，并拒绝前置条件不满足的选择。

| 组件 | 状态 | 后果 | 前置条件 |
| --- | --- | --- | --- |
| `workflow` | 必需核心 | 完整的决策驱动工作流：契约、模板、决策技能、校验器与证据链工具。 | 无 |
| `bilingual-docs` | 可选 | 双语配对契约、翻译规则、术语表，以及带 Node 要求的可选配对门禁。 | `workflow` |
| `kit` | 可选 | 安装器、安装 manifest 协议，以及面向安装树的采用指南。 | 无 |

## 前置条件

| 前置条件 | 用于 |
| --- | --- |
| Python 3 | 安装器，以及决策、链接与锚点校验器。安装器只用标准库，不发任何网络请求。 |
| Git | 在仓库历史中记录安装树与 manifest；采用与更新都是可评审的 diff。 |
| DSH 及其 base 配置档 | 运行工作流的 agent。契约、技能与门禁都通过普通仓库工具工作，工具包不需要任何插件。 |
| Node 24+ | 仅可选的双语配对门禁。不装 `bilingual-docs` 时，工作流其余部分不使用 Node。 |

插件还带来一条额外前置条件：`dsh plugin` 转发给 pnpm，因此安装与移除插件的环境里 pnpm 必须在 `PATH` 上。安装、更新或移除工具包不需要它。

## 从 kit checkout 安装

从固定版本的 kit checkout 对目标仓库运行[安装器](/.agents/se/scripts/kit/install.py)。checkout 根部的 `install.py` 是指向安装器源码的符号链接并解析到它；`.agents/se/scripts/kit/` 下的安装副本是同一份代码。安装器拒绝符号链接的安装路径与解析到目标之外的路径，且不在目标之外留下任何状态。

除给出 `--apply` 外，每个子命令都是 dry run。dry run 执行与应用运行相同的校验，打印所选组件的后果、前置条件与计划变更，并在冲突时以非零退出。安装只在文件缺失或逐字节相同时写入；存在内容不同的文件时以非零退出并停止，不写入任何内容。

```bash
# dry run: prints consequences, prerequisites and planned changes only
python3 install.py install --target ../svc

# install the required core
python3 install.py install --target ../svc --components workflow --apply

# install every component, tracked mode by default
python3 install.py install --target ../svc --apply
```

`--components` 接收逗号分隔的组件 id 列表；安装器按依赖规范化其顺序。在 `install` 上省略它表示选择所有组件，在 `uninstall` 与 `upgrade` 上表示选择 manifest 中记录的所有组件。所选组件的前置条件必须已安装或在同一次运行中被选中。只有所选组件才贡献文件与一个 `AGENTS.md` 块；未选组件不贡献任何内容，因此常驻指引不会指向仓库并不具备的契约或门禁。

### AGENTS.md 块

安装器按确定性依赖顺序为每个所选组件在 `AGENTS.md` 中组合一个标记块，块之外的每个字节保持不动：

```
<!-- se-tools:begin component=workflow -->
...
<!-- se-tools:end component=workflow -->
```

每个块是单语英语指引，只链接该组件或已声明前置条件安装的路径。安装器在写入前对所选集合运行该链接闭合检查；引用指向未选组件时以非零退出并且不写入。已存在的不同块、重复标记或未注册块都是冲突，以非零退出并且不写入。

### 技能名冲突

写入前，若所选组件的技能会遮蔽 `.agents/skills/<name>/` 下已存在的不同文件，安装器会报告技能冲突并拒绝覆盖。在仓库自身一侧解决冲突：给仓库的技能加项目短名前缀（例如目录与技能 frontmatter 的 `name` 都写 `svc-decision-check`），然后重新运行。绝不要重命名或编辑已安装的工具包技能：manifest 记录其路径与内容摘要，升级或移除会拒绝被改动的文件。

## 走查：新建仓库

新建仓库从空开始，因此一次安装就在同一个可评审变更中创建跟踪树、`AGENTS.md` 块与 manifest。在 kit checkout 中执行：

```bash
# create the repository, then install the required core from the kit checkout
mkdir ../svc && git -C ../svc init
python3 install.py install --target ../svc --components workflow --apply

# commit the adoption change in the new repository
git -C ../svc add .agents AGENTS.md
git -C ../svc commit -m "chore: adopt the development workflow kit"
```

1. 阅读 dry run 输出：必需核心的后果与前置条件、计划文件与 `AGENTS.md` 块。
2. 应用安装；安装器写入载荷与 `.agents/se/install-manifest.json`，并因仓库没有 `AGENTS.md` 而创建它。
3. 把安装树、`AGENTS.md` 块与 manifest 一起提交，使采用成为一个可评审变更。
4. 用安装的模板创建仓库自己的决策树，从 proposed 生命周期开始；工具包不导入任何决策历史。
5. 按 `workflow` 块声明的门禁顺序把安装的校验器接入仓库的 hook 或 CI，并提交该接线。
6. 在后续安装运行中加入可选组件，在 DSH 配置档而非仓库中加入可选插件。

## 走查：既有仓库

既有仓库保留其指令。安装器追加自己的标记块，绝不改写块外的文本；遇到冲突块或已存在的不同文件时，它选择拒绝而不是覆盖。当既有指引与工具包重复或矛盾时，由仓库所有者裁决：保留仓库规则并调整或省略工具包块，或采用工具包规则并退役重复内容。把冲突暴露出来，而不是静默合并。

1. 对既有仓库运行安装 dry run，阅读计划的块追加、后果与前置条件。
2. 通过编辑仓库自己的指令或减少所选组件来消解冲突；安装器不在两条矛盾指令之间做选择。
3. 应用安装；manifest 记录安装器加入的文件与块，因此之后的升级与移除只触碰这些内容。
4. 创建仓库自己的空决策树；工具包不安装任何记录，也不导入任何历史。
5. 按门禁顺序对采用变更运行安装的校验器，并在合并前修复发现；全绿既不证明人工批准，也不证明评审者同意。
6. 保持插件可选：需要内联卡片时在 DSH 配置档中安装，移除它不改变任何已安装的仓库文件。

## 安装 manifest

`.agents/se/install-manifest.json` 中的 manifest 精确记录安装：来自 kit 组件注册表的 `kit_revision`、按确定性依赖顺序排列的 `components`、取值为 `tracked` 或 `untracked` 的 `mode`、`agents_md_created`（安装器是否创建了 `AGENTS.md`）、每个已安装文件 `{path, sha256, component}`（按确定性依赖顺序再按路径排序），以及 `blocks`：把每个组件 id 映射到其块从 begin 标记行到 end 标记行、去掉末尾换行后的字节的 SHA-256。

```json
{
  "kit_revision": "2026-11-03.1",
  "components": ["workflow"],
  "mode": "tracked",
  "agents_md_created": true,
  "files": [
    {"path": ".agents/se/contracts/workflow.md", "sha256": "…", "component": "workflow"}
  ],
  "blocks": {"workflow": "…"}
}
```

manifest 是采用方自有的安装状态。它永远不是决策证据、批准记录，也不能替代仓库的 Git 历史；升级与移除会读取它，manifest 缺失或损坏是错误，且不做任何删除。

### 安装模式

安装默认是跟踪模式。仓库提交安装树、`AGENTS.md` 块与 manifest，因此新克隆无需运行安装器即可让 agent 读取方法学，漂移门禁把一次全新安装与跟踪树比较。

非跟踪模式让生成文件不进入历史。把 `.agents/se/` 与 `.agents/skills/` 加入仓库的 `.gitignore`——安装器只检查该列表，不编辑它——并以 `--mode untracked` 安装。manifest 记录该模式；从固定修订运行安装器 dry run 会把全新渲染与工作树比较，任何差异都以非零退出。此模式下的仓库必须在其 agent 读取方法学之前运行安装器：在此之前，`AGENTS.md` 块指向磁盘上不存在的文件。

## 更新

工具包没有已发布的包，也没有稳定接口；更新到新的固定 kit 修订并从该 checkout 重新运行安装器。先阅读修订之间的 diff，对仓库 dry run 升级，在应用前评审计划的移除与重装。

```bash
# dry run first, then apply
python3 install.py upgrade --target ../svc
python3 install.py upgrade --target ../svc --apply
```

旧安装若仍以独立的 `skills` 与 `gate` 记录归属，必须不带 `--components` 升级全部组件。安装器根据当前注册表声明的安装文件路径推导替代归属，校验每个旧文件与标记块的摘要，并在移除任何内容之前预检新安装。不保留永久选择别名。没有替代归属的旧组件须先显式移除；卸载仍可选择旧 manifest 中记录的归属。

`upgrade` 先为所选组件校验一次移除 dry run。只有移除与重装预检都无冲突才会继续，之后才从新修订重装这些组件；未选组件不受影响。跟踪模式下安装树与 manifest 的 diff 就是可评审变更；非跟踪模式下在应用前评审工作树。所有前置条件都会重新检查。

## 移除

移除按所选组件进行且全有或全无。文件缺失、块缺失或重复、内容摘要不匹配都是提示：安装器报告它、以非零退出并且不删除任何内容。干净运行精确删除记录的文件与块；其他组件的文件与块，以及块之外的全部内容，都不受影响。只有安装器创建了 `AGENTS.md` 且其中只剩空白时，才删除 `AGENTS.md` 本身。manifest 缺失或损坏是错误，且不做任何删除。

```bash
# dry run first, then apply
python3 install.py uninstall --target ../svc --components bilingual-docs
python3 install.py uninstall --target ../svc --components bilingual-docs --apply
```

省略 `--components` 会移除 manifest 中记录的所有组件。移除可选的 kit 组件会从目标中移除安装器副本与本指南，之后的升级需再次从 kit checkout 发起；最终的移除仍可在目标内用安装副本执行。被移除组件的文件与块消失；其他组件不受影响。

## 自安装与漂移门禁

se-tools 把自己的工具包安装进自身，因此发布工具包的仓库走的是与采用方相同的路径。其跟踪的 `.agents/` 树与 `AGENTS.md` 块由源码渲染而来，安装副本绝不手工编辑：下一次渲染会覆盖它，漂移门禁也会失败。编辑源码后，用升级从 checkout 重新生成，因为 `install` 按设计拒绝内容不同的文件。

```bash
python3 install.py upgrade --target . --self --confirm-self --apply
```

`--self` 是 se-tools 内部的，需要 `--confirm-self`，在其他任何目标上都会被拒绝。漂移门禁把一次全新安装渲染到临时目录，并比较文件、manifest 与 `AGENTS.md` 块和跟踪树；任何差异都会让它失败，它作为完整检查的一部分运行（`pnpm run check`，或单独运行门禁的 `pnpm run verify:install`）。

## 可选 DSH 插件：dsh-se-cards

`dsh-se-cards` 是工具包可选的 DSH bundle：它在回复中写入 `dsh-card` 围栏的位置就地渲染内联静态 HTML 卡片与 mermaid 图。插件在安装器与 manifest 之外。它是 DSH 配置档中的用户级步骤，不改变任何仓库文件，移除它后安装树不变、所有出厂校验器仍绿。采用仓库的持续集成运行已安装的门禁；它既不安装工具包组件，也不安装插件。

### 验证范围与降级

已验证的 DSH 范围只有单个版本 `0.2.2-alpha.2`，测试于提交 `ce7073d51254c26cd63b22a60835b8f948deb447`；在重新测试 DOM 钩子之前，其他任何版本都在范围之外。渲染器是 DOM 装饰，不是受支持的渲染钩子：它观察渲染后的对话并就地替换已稳定的 `dsh-card` 代码块，因此依赖 DSH 并未承诺为插件 API 的 DOM 钩子。

钩子变化时，围栏静默地保持为普通代码块：回复文本与会话数据不变，重放与导出保留围栏，没有该 bundle 的客户端始终显示为代码块。移除插件并在重载后恢复普通代码块，且不改变任何已安装的仓库文件与校验器结果。

### 安装与移除插件

把来源固定为安装 manifest 中 `kit_revision` 记录的 kit 修订。从该 checkout 构建并打包 bundle tarball；tarball 携带包所声明的已构建 `dist/` 产物，因此配置档安装的是预构建代码，不需要构建脚本。包在 `./cordis.patch.yml` 声明 `dsh.bundle.patch`，因此 `dsh plugin add` 也会把它的层追加到配置档的 `dsh.profile.bundles`。

```bash
# from the pinned kit checkout: build and pack the bundle
pnpm install
pnpm --filter dsh-se-cards run build
pnpm --filter dsh-se-cards pack --pack-destination ./.tmp

# install into a DSH profile, then verify the layer
dsh plugin --profile <name> add ./.tmp/dsh-se-cards-0.2.0.tgz
dsh --profile <name> --dump-config

# remove it again
dsh plugin --profile <name> remove dsh-se-cards
```

打包出的 tarball 就是固定来源：不要从会移动的目录链接或未固定版本的 git 引用安装，因为二者都可能在未经评审的 kit 修订下改变配置档里运行的代码。在依赖该插件之前，`--dump-config` 应显示 `dsh-se-cards` 层。移除依赖会一并移除该层；重启或重载客户端即回到普通代码块。
