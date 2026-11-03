# dsh-profiler-hotspots

[English](/plugins/dsh-profiler-hotspots/README.md) | 中文

`dsh-profiler-hotspots` 是一个 DSH Web UI 插件包，为 Web 客户端提供「执行热点分析」页面：一个可以搜索工作区与会话的浏览器。宿主半边不注册任何内容，全部行为位于客户端半边。本仓库的目标与职责边界见[项目宪章](/docs/agent-profiler.zh.md)。

## 插件提供的能力

客户端半边在左侧边栏的面板列表中新增一项：柱状图图标与「执行热点分析」标签。选中该项后，主栏中会打开该页面。页面没有标题：顶部第一个元素是全宽的搜索框。

## 搜索

在搜索框中输入会实时过滤分组的工作区与会话列表：不需要按回车，输入时也不与 Host 通信。过滤不区分大小写，匹配元数据：会话标题、工作区标题，以及会话 id 的子串。匹配结果仍按所属工作区分组：在「搜索结果」标签和结果数下方，每个匹配的工作区显示为一行表头（打开状态的文件夹图标与工作区名称），其匹配会话列在下方。工作区标题匹配时，该工作区下的所有会话都会纳入结果。同一工作区内的匹配按最近更新在前排列，结果没有上限。临时的空白会话没有持久标题，永远不会被匹配。客户端半边只过滤它已经持有的元数据。

## 工作区与会话列表

查询为空时，页面在「工作区」区块标签下显示与侧边栏「工作区」区域相同的分组工作区与会话列表。每个工作区行是一个按钮，用于展开或收起其会话：展开时显示与宿主界面一致的打开文件夹图标，收起时显示与宿主界面一致的闭合文件夹图标；在支持悬停的设备上，悬停时该图标会变为展开箭头。包含当前会话的工作区会以品牌色为其文件夹着色，当前会话行会高亮显示。普通会话行显示状态点、会话标题和相对更新时间；临时的空白会话显示为「新会话」且只显示标题。已归档会话与 subagent 来源的会话会隐藏，不属于任何工作区的会话归入「未分组」。选中会话会在对话中打开它。

## 包布局

| 路径 | 职责 |
|---|---|
| `package.json` | 包元数据、导出，以及 `dsh.bundle` 与 `dsh.client` 声明 |
| `cordis.patch.yml` | 插入本插件的 bundle patch 条目 |
| `index.js` | 宿主半边；导出一个空的 `apply()` |
| `client.js` | 客户端半边；新增侧边栏入口并渲染页面 |
| `icon.svg` | 柱状图包图标 |
| `locale/en.json` | 英文插件元数据：`meta.title` 与 `meta.description` |
| `locale/zh.json` | 中文插件元数据：`meta.title` 与 `meta.description` |

`package.json` 将宿主半边导出为包入口（`./index.js`），将客户端半边导出为 `./client`（`./client.js`），将语言资源导出为 `./locale/*.json`，将图标导出为 `./icon`（`icon.svg`）。

## 标识符

| 标识符 | 值 | 作用 |
|---|---|---|
| 包名 | `dsh-profiler-hotspots` | 命名包及其 bundle patch 条目 |
| bundle patch 条目 id | `dsh-profiler-hotspots` | `cordis.patch.yml` 插入的条目，`config` 为空 |
| 主面板 id | `hotspots` | 客户端半边注册侧边栏入口与页面所用的 id |
| locale 命名空间 | `dsh-profiler-hotspots` | 客户端半边注册界面文案所用的命名空间 |

## 配置

本包不接受配置；bundle patch 条目以 `config: {}` 插入本插件。`dsh.client` 声明 `platform: "web"` 与 `immediately: true`，并列出客户端半边注入的包：`@deepseek-ai/dsh-client-locale`、`@deepseek-ai/dsh-client-ui-layout`、`@deepseek-ai/dsh-client-ui-session`、`@deepseek-ai/dsh-client-ui-sidebar` 与 `@deepseek-ai/dsh-client-ui-workspace`。

## 限制

- **仅限元数据搜索**：搜索只覆盖会话标题、工作区标题与会话 id 子串，不搜索会话内容。
- **没有工作区或会话管理**：页面不提供添加、重命名或删除工作区的操作，也不提供置顶或归档会话的操作。
- **没有归档筛选**：已归档会话始终隐藏，页面没有显示它们的控件。
