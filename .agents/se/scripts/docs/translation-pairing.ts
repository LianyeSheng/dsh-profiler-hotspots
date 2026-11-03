/**
 * 双语配对门禁的语料范围、清单、CLI 参数与 Markdown 结构签名。
 *
 * 结构签名只覆盖本仓库文档使用的 Markdown 子集：ATX 标题、围栏代码块、
 * GFM 表格、列表与链接；围栏代码块里的行不参与任何结构识别。
 */

import type { MarkdownLink, MarkdownScan } from './translation-links.ts'
import { listMarker } from './translation-links.ts'

/** `.agents/se/scripts/docs/translation-pairing.manifest.json` 的字段。 */
export interface TranslationPairingManifest {
  /** 显式排除的路径：目录项以 `/` 结尾覆盖整棵子树，其余为精确文件。 */
  excluded: string[]
}

/** 组成一对双语文档的三个仓库相对路径。 */
export interface TranslationPairPaths {
  /** 英文锚点文档。 */
  source: string
  /** 中文对侧文档。 */
  zh: string
  /** 一致性记录。 */
  meta: string
}

/** 依赖目录与产物目录，从不作为文档语料扫描。 */
export const NON_SOURCE_DIRECTORIES = new Set([
  'node_modules',
  '.git',
  'dist',
  'lib',
  '.pnpm-store',
  'coverage',
  '.cache',
  '.tmp',
])

const README_BASENAME = 'readme.md'

/**
 * 判断一个仓库相对路径是否是在范围的英文文档。
 *
 * 范围：任意目录下的 `README.md`（大小写不敏感）、`docs/` 下的所有 `.md`、
 * `.agents/notes/` 下的所有活跃 `.md`、`.agents/se/` 下的所有已安装 `.md`，
 * 以及 `components/` 下的所有 `.md`，但组件的 `agents.md` 片段是单语的。
 * `.zh.md` 与 `.i18n.yaml` 是对侧产物，不是英文源。
 *
 * @param file - 仓库相对路径（`/` 分隔）。
 * @returns 是否属于应配对的英文源文档。
 */
export function isTranslationScopeFile(file: string): boolean {
  const segments = file.split('/')
  if (segments.some(segment => NON_SOURCE_DIRECTORIES.has(segment))) return false
  const lower = file.toLowerCase()
  if (!lower.endsWith('.md') || lower.endsWith('.zh.md')) return false
  if (file.startsWith('.agents/notes/archived/')) return false
  const base = segments.at(-1)?.toLowerCase() ?? ''
  if (base === README_BASENAME) return true
  if (/^components\/[^/]+\/agents\.md$/.test(file)) return false
  return file.startsWith('docs/')
    || file.startsWith('.agents/notes/')
    || file.startsWith('.agents/se/')
    || file.startsWith('components/')
}

/**
 * 判断一个路径是否被清单显式排除。
 *
 * @param file - 仓库相对路径。
 * @param manifest - 已验证的排除清单。
 * @returns 命中排除项时返回 true。
 */
export function isTranslationPairingManifestExcluded(
  file: string,
  manifest: TranslationPairingManifest,
): boolean {
  return manifest.excluded.some(entry => (entry.endsWith('/') ? file.startsWith(entry) : file === entry))
}

/**
 * 解析并验证排除清单。
 *
 * @param content - 清单文件的完整 JSON 文本。
 * @returns 已验证的清单。
 * @throws Error 当 JSON 结构或字段不合法时。
 */
export function parseTranslationPairingManifest(content: string): TranslationPairingManifest {
  const value: unknown = JSON.parse(content)
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('translation-pairing.manifest.json: 期望一个对象')
  }
  const record = value as Record<string, unknown>
  const unsupported = Object.keys(record).filter(field => field !== 'excluded')
  if (unsupported.length > 0) {
    throw new Error(`translation-pairing.manifest.json: 不支持的字段：${unsupported.join('、')}；每个在范围文档都必须配对`)
  }
  const excluded = record.excluded
  if (!Array.isArray(excluded) || !excluded.every((entry): entry is string => typeof entry === 'string')) {
    throw new Error('translation-pairing.manifest.json: excluded 必须是字符串数组')
  }
  return { excluded }
}

/**
 * 由英文锚点推导三个配对路径。
 *
 * @param source - 英文 Markdown 仓库相对路径。
 * @returns 三件套路径。
 * @throws Error 当传入的不是 `.md` 锚点时。
 */
export function translationPairPaths(source: string): TranslationPairPaths {
  if (!source.toLowerCase().endsWith('.md') || source.toLowerCase().endsWith('.zh.md')) {
    throw new Error(`期望英文 Markdown 路径，收到 ${JSON.stringify(source)}`)
  }
  return {
    source,
    zh: source.replace(/\.md$/i, '.zh.md'),
    meta: source.replace(/\.md$/i, '.i18n.yaml'),
  }
}

/**
 * 把命令行里的一个配对参数归一到英文锚点路径。
 *
 * 三件套中的任一文件或去后缀的 stem 都指向同一对。
 *
 * @param argument - 命令行参数。
 * @returns 英文锚点路径。
 */
export function pairAnchorOfArgument(argument: string): string {
  const normalized = argument.split('\\').join('/').replace(/^\.\//, '')
  const lower = normalized.toLowerCase()
  if (lower.endsWith('.zh.md')) return `${normalized.slice(0, -'.zh.md'.length)}.md`
  if (lower.endsWith('.i18n.yaml')) return `${normalized.slice(0, -'.i18n.yaml'.length)}.md`
  if (lower.endsWith('.md')) return normalized
  return `${normalized}.md`
}

/** 一次门禁调用解析后的请求。 */
export interface TranslationPairingRequest {
  mode: 'check' | 'list' | 'write'
  /** `corpus` 扫描整棵语料；`pairs` 只处理被点名的配对。 */
  scope: 'corpus' | 'pairs'
  /** 被点名的英文锚点路径；`corpus` 范围下为空。 */
  anchors: string[]
}

/**
 * 解析并验证命令行参数。
 *
 * `--write` 必须点名配对或使用 `--all`，避免一次性确认从未审阅过的全仓内容。
 *
 * @param argv - 脚本名之后的参数。
 * @returns 已验证的请求。
 * @throws Error 当参数组合不合法时。
 */
export function parseTranslationPairingCliArgs(argv: string[]): TranslationPairingRequest {
  const flags = argv.filter(argument => argument.startsWith('--'))
  const anchors = [...new Set(argv.filter(argument => !argument.startsWith('--')).map(pairAnchorOfArgument))].sort()
  const unknown = flags.filter(flag => !['--list', '--write', '--all'].includes(flag))
  if (unknown.length > 0) throw new Error(`未知参数：${unknown.join('、')}`)
  const listMode = flags.includes('--list')
  const writeMode = flags.includes('--write')
  const allMode = flags.includes('--all')
  if (listMode && (writeMode || allMode || anchors.length > 0)) {
    throw new Error('--list 只报告全量语料状态，不能与其他参数或路径组合')
  }
  if (allMode && !writeMode) throw new Error('--all 只能与 --write 一起使用')
  if (writeMode) {
    if (anchors.length > 0 && allMode) throw new Error('--write 要么点名配对，要么 --all，不能同时使用')
    if (anchors.length === 0 && !allMode) {
      throw new Error('--write 需要点名你确认过的配对（三件套之一即可），或用 --all 重录全部完整对；未审阅的全量重录会把假一致性写进记录')
    }
    return { mode: 'write', scope: allMode ? 'corpus' : 'pairs', anchors }
  }
  if (listMode) return { mode: 'list', scope: 'corpus', anchors: [] }
  return { mode: 'check', scope: anchors.length > 0 ? 'pairs' : 'corpus', anchors }
}

/** 结构签名里的一项：值加 1 起始行号。 */
export interface StructureEntry {
  value: string
  line: number
}

/** 一对文档之间比较的结构签名。 */
export interface TranslationStructureSignature {
  headings: StructureEntry[]
  code: StructureEntry[]
  tables: StructureEntry[]
  lists: StructureEntry[]
  links: StructureEntry[]
}

/** 一处结构分歧。 */
export interface TranslationStructureDivergence {
  field: '标题层级' | '围栏代码块' | '表格' | '列表' | '链接'
  index: number
  en?: StructureEntry
  zh?: StructureEntry
}

interface TableStructure {
  entry: StructureEntry
  lines: number[]
}

function cellCount(line: string): number {
  const protectedPipes = line.replace(/\\\|/g, '\u0000')
  const trimmed = protectedPipes.trim().replace(/^\|/, '').replace(/\|$/, '')
  if (trimmed.trim() === '') return 0
  return trimmed.split('|').length
}

function isDelimiterRow(line: string): boolean {
  const trimmed = line.trim()
  if (!trimmed.includes('|') || !trimmed.includes('-')) return false
  if (!/^[\s|:-]+$/.test(trimmed)) return false
  const cells = trimmed.replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim())
  return cells.length >= 1 && cells.every(cell => /^:?-+:?$/.test(cell))
}

function tables(scan: MarkdownScan): TableStructure[] {
  const found: TableStructure[] = []
  let index = 0
  while (index < scan.masked.length - 1) {
    if (scan.fenced[index] === true) {
      index++
      continue
    }
    const header = scan.masked[index] ?? ''
    const delimiter = scan.masked[index + 1] ?? ''
    if (!header.includes('|') || scan.fenced[index + 1] === true || !isDelimiterRow(delimiter)
      || cellCount(delimiter) !== cellCount(header)) {
      index++
      continue
    }
    const lines = [index + 1]
    let rows = 1
    let cursor = index + 2
    while (cursor < scan.masked.length) {
      const line = scan.masked[cursor] ?? ''
      if (scan.fenced[cursor] === true || line.trim() === '' || !line.includes('|')) break
      if (/^#{1,6}(?:[ \t]+|$)/.test(line)) break
      rows++
      lines.push(cursor + 1)
      cursor++
    }
    found.push({ entry: { value: `${rows}x${cellCount(header)}`, line: index + 1 }, lines })
    index = cursor
  }
  return found
}

function isThematicBreak(line: string): boolean {
  return /^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$/.test(line)
}

function indentWidth(whitespace: string): number {
  return [...whitespace].reduce((width, character) => width + (character === '\t' ? 4 : 1), 0)
}

interface ListLevel {
  indent: number
  ordered: boolean
  start: number
  count: number
  line: number
  entryIndex: number
}

/**
 * 逐层统计列表块：类型、有序起始与条目数。空行不结束松散列表，只有后续非列表块才结束它。
 *
 * 英文文档的硬换行续行不匹配列表标记，因而不改变条目数。
 *
 * @param scan - 文档扫描结果。
 * @returns 每个列表层级一项，父列表先于其嵌套列表。
 */
function lists(scan: MarkdownScan): StructureEntry[] {
  const tableLines = new Set<number>()
  for (const table of tables(scan)) for (const line of table.lines) tableLines.add(line)
  const headingLines = new Set(scan.headings.map(heading => heading.lineIndex + 1))
  const entries: StructureEntry[] = []
  const flush = (region: number[]): void => {
    const stack: ListLevel[] = []
    for (const lineNumber of region) {
      const line = scan.masked[lineNumber - 1] ?? ''
      if (isThematicBreak(line)) continue
      const marker = listMarker(line)
      if (marker === undefined) continue
      const indent = indentWidth(marker[1] ?? '')
      const ordered = /\d/.test(marker[2] ?? '')
      const start = ordered ? Number.parseInt(marker[2] ?? '1', 10) : 1
      while (stack.length > 0 && indent < (stack.at(-1)?.indent ?? 0)) stack.pop()
      const top = stack.at(-1)
      if (top === undefined || indent > top.indent || top.ordered !== ordered) {
        if (top !== undefined) stack.pop()
        const level: ListLevel = { indent, ordered, start, count: 1, line: lineNumber, entryIndex: entries.length }
        stack.push(level)
        entries.push({ value: renderListValue(level), line: lineNumber })
        continue
      }
      top.count++
      entries[top.entryIndex] = { value: renderListValue(top), line: top.line }
    }
  }
  let region: number[] = []
  for (let lineIndex = 0; lineIndex < scan.masked.length; lineIndex++) {
    const lineNumber = lineIndex + 1
    const line = scan.masked[lineIndex] ?? ''
    const hardBoundary = scan.fenced[lineIndex] === true
      || headingLines.has(lineNumber)
      || tableLines.has(lineNumber)
    if (hardBoundary) {
      if (region.length > 0) flush(region)
      region = []
      continue
    }
    if (line.trim() === '') {
      // A blank line between list items keeps the list loose; only a following
      // non-list block ends it.
      let lookahead = lineIndex + 1
      while (lookahead < scan.masked.length && (scan.masked[lookahead] ?? '').trim() === ''
        && scan.fenced[lookahead] !== true) lookahead++
      const next = scan.masked[lookahead] ?? ''
      const continuesList = region.length > 0
        && lookahead < scan.masked.length
        && scan.fenced[lookahead] !== true
        && !headingLines.has(lookahead + 1)
        && !tableLines.has(lookahead + 1)
        && listMarker(next) !== undefined
      if (!continuesList) {
        if (region.length > 0) flush(region)
        region = []
      }
      continue
    }
    region.push(lineNumber)
  }
  if (region.length > 0) flush(region)
  return entries
}

function renderListValue(level: ListLevel): string {
  return level.ordered ? `ordered:start=${level.start}:items=${level.count}` : `bullet:items=${level.count}`
}

/**
 * 计算一对文档之间的结构签名。
 *
 * @param scan - 该侧文档的扫描结果。
 * @param semanticLinkTarget - 把链接目标映射为可比较语义标记的函数。
 * @param switcherLineIndex - 语言切换行（0 起始行索引），该行链接不参与比较。
 * @returns 结构签名。
 */
export function translationStructureSignature(
  scan: MarkdownScan,
  semanticLinkTarget: (link: MarkdownLink) => string,
  switcherLineIndex: number | undefined,
): TranslationStructureSignature {
  return {
    headings: scan.headings.map(heading => ({ value: String(heading.depth), line: heading.lineIndex + 1 })),
    code: scan.codeBlocks.map(block => ({ value: block.text, line: block.lineIndex + 1 })),
    tables: tables(scan).map(table => table.entry),
    lists: lists(scan),
    links: scan.links
      .filter(link => link.line !== (switcherLineIndex === undefined ? -1 : switcherLineIndex + 1))
      .map(link => ({ value: link.image ? `image:${link.destination}` : semanticLinkTarget(link), line: link.line })),
  }
}

const STRUCTURE_FIELDS: readonly [TranslationStructureDivergence['field'], keyof TranslationStructureSignature][] = [
  ['标题层级', 'headings'],
  ['围栏代码块', 'code'],
  ['表格', 'tables'],
  ['列表', 'lists'],
  ['链接', 'links'],
]

/**
 * 逐字段比较两侧结构签名，返回每个字段的第一处分歧。
 *
 * @param en - 英文侧签名。
 * @param zh - 中文侧签名。
 * @returns 分歧列表；两侧完全一致时为空。
 */
export function translationStructureDiff(
  en: TranslationStructureSignature,
  zh: TranslationStructureSignature,
): TranslationStructureDivergence[] {
  const out: TranslationStructureDivergence[] = []
  for (const [field, key] of STRUCTURE_FIELDS) {
    const enEntries = en[key]
    const zhEntries = zh[key]
    const length = Math.max(enEntries.length, zhEntries.length)
    for (let index = 0; index < length; index++) {
      const enEntry = enEntries[index]
      const zhEntry = zhEntries[index]
      if (enEntry?.value === zhEntry?.value) continue
      out.push({ field, index: index + 1, ...(enEntry === undefined ? {} : { en: enEntry }), ...(zhEntry === undefined ? {} : { zh: zhEntry }) })
      break
    }
  }
  return out
}
