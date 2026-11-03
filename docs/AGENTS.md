# AGENTS.md — docs 写作指令

本文件是 `docs/` 与包 README 的写作指令，只以中文维护；`docs/AGENTS.md` 由双语配对清单排除，不参与配对。

- 项目目标与职责以[项目宪章](/docs/agent-profiler.zh.md)为准；同一事实只写一处，其他位置链接过去。
- `docs/` 下的成对文档按[双语契约](/.agents/se/contracts/i18n/README.zh.md)维护三件套；修改任一侧时同次更新对侧，并用 `.agents/se/scripts/docs/verify-translation-pairing.ts --write <pair>` 重录配对。
- 翻译规则与术语见[翻译规则](/.agents/se/contracts/i18n/translation-rules.zh.md)与[术语表](/.agents/se/contracts/i18n/terminology.zh.md)。
- 一个段落一个物理行；标识符、命令、路径、包名不译；中文标点与中英混排按翻译规则。
