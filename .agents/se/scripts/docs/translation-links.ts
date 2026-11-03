/**
 * Markdown 扫描与仓库根相对链接的 locale 解析，供双语配对门禁使用。
 *
 * 扫描器只覆盖本仓库文档实际使用的 Markdown 子集：ATX 标题、围栏代码块、
 * GFM 表格、列表与行内/引用式链接。围栏代码块与行内代码里的内容不参与
 * 链接、表格与列表的识别。
 */

/** 文档内一个链接目标出现的位置。 */
export interface MarkdownLink {
  /** 1 起始的行号。 */
  line: number
  /** 目标在整篇文档中的起始字符偏移（不含尖括号）。 */
  start: number
  /** 目标的结束字符偏移。 */
  end: number
  /** 去掉尖括号后的目标文本。 */
  destination: string
  /** 是否为图片（`![alt](src)`）；图片不参与配对链接的 locale 检查。 */
  image: boolean
}

/** 一篇文档的扫描结果。 */
export interface MarkdownScan {
  /** 按行索引：该行是否属于围栏代码块（含围栏标记行）。 */
  fenced: boolean[]
  /** 文档顺序的围栏代码块：开围栏行原文加内容行，带 0 起始行索引。 */
  codeBlocks: { lineIndex: number; text: string }[]
  /** 文档顺序的 ATX 标题。 */
  headings: MarkdownHeading[]
  /** 文档顺序的非图片链接。 */
  links: MarkdownLink[]
  /** 行内代码被空格替换后的行文本，长度与原文一致，偏移可直接复用。 */
  masked: string[]
  /** 让结构分析不可靠的问题（未闭合围栏、setext 标题）。 */
  problems: string[]
}

/** 一个 ATX 标题。 */
export interface MarkdownHeading {
  /** 0 起始的行索引。 */
  lineIndex: number
  depth: number
  /** 去掉结尾井号后的标题文本。 */
  text: string
}

/** 仓库根相对的成对文档链接目标。 */
export interface PairedLinkTarget {
  /** 英文锚点路径（`foo.md`）。 */
  anchor: string
  /** 目标里的 query/fragment 后缀，原样保留。 */
  suffix: string
  /** 解析后的仓库相对目标路径（可能是 `.md` 或 `.zh.md`）。 */
  destinationPath: string
}

/** 解析一个链接目标所需的上下文。 */
export interface LinkContext {
  /** 链接所在文档的仓库相对路径。 */
  sourcePath: string
  /** 该路径是否为在范围的成对文档英文锚点。 */
  isPairSource: (source: string) => boolean
}

/** 语言切换行的识别结果。 */
export interface LanguageSwitcher {
  /** 0 起始的行索引。 */
  lineIndex: number
  /** 整行原文。 */
  text: string
  /** 切换行里的目标路径。 */
  target: string
  /** 切换行的语言方向。 */
  locale: 'en' | 'zh'
}

const ATX_HEADING = /^(#{1,6})(?:[ \t]+(.*))?$/
const FENCE_OPEN = /^ {0,3}(`{3,}|~{3,})(.*)$/
const DEFINITION = /^ {0,3}\[([^\]]+)\]:[ \t]*(<[^>]*>|\S+)/

/**
 * 把一行中的行内代码替换为等长空格，使后续正则不会把代码里的示例当成
 * 链接、标题或表格。
 *
 * @param line - 一行原文。
 * @returns 等长、行内代码被空格覆盖后的行文本。
 */
export function maskInlineCode(line: string): string {
  const characters = [...line]
  let index = 0
  while (index < characters.length) {
    if (characters[index] !== '`') {
      index++
      continue
    }
    let run = 0
    while (characters[index + run] === '`') run++
    const opener = index
    let cursor = index + run
    let closed = false
    while (cursor < characters.length) {
      if (characters[cursor] !== '`') {
        cursor++
        continue
      }
      let closing = 0
      while (characters[cursor + closing] === '`') closing++
      if (closing === run) {
        for (let masked = opener; masked < cursor + closing; masked++) characters[masked] = ' '
        index = cursor + closing
        closed = true
        break
      }
      cursor += closing
    }
    if (!closed) index += run
  }
  return characters.join('')
}

/**
 * 把 HTML 注释替换为等长空格，并跨行维护注释状态。
 *
 * 输入已先做行内代码遮蔽，因此代码里的示例标记不会打开或关闭注释。
 *
 * @param line - 行内代码已遮蔽的一行文本。
 * @param state - 跨行注释状态，会被更新。
 * @returns 与输入等长的行文本。
 */
function maskHtmlCommentSpans(line: string, state: { open: boolean }): string {
  const characters = [...line]
  for (let index = 0; index < characters.length; index++) {
    if (state.open) {
      if (characters[index] === '-' && characters[index + 1] === '-' && characters[index + 2] === '>') {
        characters[index] = ' '
        characters[index + 1] = ' '
        characters[index + 2] = ' '
        index += 2
        state.open = false
        continue
      }
      characters[index] = ' '
      continue
    }
    if (characters[index] === '<' && characters[index + 1] === '!' && characters[index + 2] === '-'
      && characters[index + 3] === '-') {
      characters[index] = ' '
      characters[index + 1] = ' '
      characters[index + 2] = ' '
      characters[index + 3] = ' '
      index += 3
      state.open = true
    }
  }
  return characters.join('')
}

/**
 * 识别文档开头受支持的 YAML frontmatter 行范围。
 *
 * 第一行是 `---` 且其后存在一行 `---` 时，两条分隔线之间的行（含分隔线）属于
 * frontmatter；未闭合（找不到结束行）时返回 undefined，按普通文本处理，不报问题。
 *
 * @param rawLines - 按行切开的文档文本。
 * @returns 0 起始的行范围（含两端分隔线）；没有 frontmatter 时返回 undefined。
 */
export function leadingFrontmatter(rawLines: string[]): { start: number; end: number } | undefined {
  if ((rawLines[0] ?? '').trim() !== '---') return undefined
  for (let index = 1; index < rawLines.length; index++) {
    if ((rawLines[index] ?? '').trim() === '---') return { start: 0, end: index }
  }
  return undefined
}

/**
 * 扫描一篇 Markdown 文档，收集围栏代码块、标题与链接。
 *
 * @param content - 完整文档文本。
 * @returns 扫描结果；结构性无法分析的问题记入 `problems`。
 */
export function scanMarkdown(content: string): MarkdownScan {
  const rawLines = content.split('\n')
  const fenced = rawLines.map(() => false)
  const codeBlocks: { lineIndex: number; text: string }[] = []
  const problems: string[] = []
  const frontmatter = leadingFrontmatter(rawLines)
  if (frontmatter !== undefined) {
    // Frontmatter lines are opaque structure: marked fenced so headings, tables, lists,
    // links and section hashes ignore them, but kept out of codeBlocks because the two
    // sides may legitimately carry different frontmatter.
    for (let mark = frontmatter.start; mark <= frontmatter.end; mark++) fenced[mark] = true
  }
  let index = 0
  while (index < rawLines.length) {
    if (fenced[index] === true) {
      index++
      continue
    }
    const line = rawLines[index] ?? ''
    const open = FENCE_OPEN.exec(line)
    if (open === null) {
      index++
      continue
    }
    const marker = open[1] ?? ''
    const fenceCharacter = marker[0] === '~' ? '~' : '`'
    const closer = new RegExp(`^ {0,3}${fenceCharacter}{${marker.length},}[ \\t]*$`)
    let end = index + 1
    while (end < rawLines.length && !closer.test(rawLines[end] ?? '')) end++
    if (end >= rawLines.length) {
      problems.push(`第 ${index + 1} 行的围栏代码块没有闭合`)
      for (let mark = index; mark < rawLines.length; mark++) fenced[mark] = true
      codeBlocks.push({ lineIndex: index, text: rawLines.slice(index).join('\n') })
      index = rawLines.length
      break
    }
    for (let mark = index; mark <= end; mark++) fenced[mark] = true
    codeBlocks.push({ lineIndex: index, text: rawLines.slice(index, end + 1).join('\n') })
    index = end + 1
  }

  const masked: string[] = []
  const headings: MarkdownHeading[] = []
  const links: MarkdownLink[] = []
  let lineStart = 0
  const commentState = { open: false }
  for (const [lineIndex, line] of rawLines.entries()) {
    let maskedLine: string
    if (fenced[lineIndex] === true) {
      maskedLine = line.replace(/[^\n]/g, ' ')
      commentState.open = false
    } else {
      maskedLine = maskHtmlCommentSpans(maskInlineCode(line), commentState)
    }
    masked.push(maskedLine)
    if (fenced[lineIndex] !== true) {
      const heading = ATX_HEADING.exec(maskedLine)
      if (heading !== null) {
        const raw = rawLines[lineIndex] ?? ''
        const headingRaw = ATX_HEADING.exec(raw)
        const text = (headingRaw?.[2] ?? '').replace(/[ \t]+#+[ \t]*$/, '').trim()
        headings.push({ lineIndex, depth: (heading[1] ?? '#').length, text })
      }
      collectLineLinks(rawLines[lineIndex] ?? '', maskedLine, lineStart, lineIndex, links)
      const definition = DEFINITION.exec(maskedLine)
      if (definition !== null) {
        const destinationStart = definition.index + (definition[0]?.length ?? 0) - (definition[2]?.length ?? 0)
        const rawDestination = definition[2] ?? ''
        const unwrapped = rawDestination.startsWith('<') && rawDestination.endsWith('>')
          ? rawDestination.slice(1, -1)
          : rawDestination
        links.push({
          line: lineIndex + 1,
          start: lineStart + destinationStart,
          end: lineStart + destinationStart + rawDestination.length,
          destination: unwrapped,
          image: false,
        })
      }
    }
    lineStart += line.length + 1
  }

  const setext = /^ {0,3}(?:={3,}|-{3,})[ \t]*$/
  for (let lineIndex = 1; lineIndex < rawLines.length; lineIndex++) {
    if (fenced[lineIndex] === true || fenced[lineIndex - 1] === true) continue
    if (!setext.test(masked[lineIndex] ?? '')) continue
    const previous = (masked[lineIndex - 1] ?? '').trim()
    if (previous === '' || ATX_HEADING.test(masked[lineIndex - 1] ?? '')) continue
    if (listMarker(masked[lineIndex - 1] ?? '') === undefined) {
      problems.push(`第 ${lineIndex + 1} 行使用了不支持的 setext 标题`)
    }
  }

  return { fenced, codeBlocks, headings, links, masked, problems }
}

function collectLineLinks(
  line: string,
  maskedLine: string,
  lineStart: number,
  lineIndex: number,
  links: MarkdownLink[],
): void {
  const opener = /(!?)\[([^\]]*)\]\([ \t]*/g
  for (let match = opener.exec(maskedLine); match !== null; match = opener.exec(maskedLine)) {
    const afterParen = match.index + match[0].length
    let cursor = afterParen
    let destination: string
    if (line[cursor] === '<') {
      const close = line.indexOf('>', cursor + 1)
      if (close < 0) continue
      destination = line.slice(cursor + 1, close)
      links.push({
        line: lineIndex + 1,
        start: lineStart + cursor + 1,
        end: lineStart + close,
        destination,
        image: match[1] === '!',
      })
      opener.lastIndex = close + 1
      continue
    }
    while (cursor < line.length && !/[\s)]/.test(line[cursor] ?? '')) cursor++
    destination = line.slice(afterParen, cursor)
    if (destination === '') continue
    links.push({
      line: lineIndex + 1,
      start: lineStart + afterParen,
      end: lineStart + cursor,
      destination,
      image: match[1] === '!',
    })
    opener.lastIndex = cursor
  }
}

/**
 * 识别行首的列表标记。
 *
 * @param line - 一行文本（行内代码已遮蔽）。
 * @returns 匹配结果，含缩进与标记本身；不是列表项时返回 undefined。
 */
export function listMarker(line: string): RegExpExecArray | undefined {
  return /^([ \t]*)([-*+]|\d{1,9}[.)])(?:[ \t]+|$)/.exec(line) ?? undefined
}

/**
 * 判断一个链接目标是否为外部或锚点目标。
 *
 * @param destination - 链接目标原文。
 * @returns 外部 URL、协议相对 URL 与纯锚点返回 true。
 */
export function isExternalDestination(destination: string): boolean {
  return /^(?:[a-z][a-z0-9+.-]*:|\/\/|#)/i.test(destination)
}

/**
 * 把链接目标拆成路径与 query/fragment 后缀。
 *
 * @param destination - 链接目标原文（不带尖括号）。
 * @returns 路径部分与后缀；后缀含起始的 `?` 或 `#`。
 */
export function splitDestination(destination: string): { path: string; suffix: string } {
  const cut = destination.search(/[?#]/)
  if (cut < 0) return { path: destination, suffix: '' }
  return { path: destination.slice(0, cut), suffix: destination.slice(cut) }
}

function decodePath(path: string): string {
  try {
    return decodeURIComponent(path)
  } catch {
    return path
  }
}

/**
 * 把链接目标解析为仓库相对路径。
 *
 * @param destination - 链接目标原文。
 * @param sourcePath - 链接所在文档的仓库相对路径。
 * @returns 仓库相对路径；外部目标、逃出仓库根的目标返回 undefined。
 */
export function resolveDestination(destination: string, sourcePath: string): string | undefined {
  const { path } = splitDestination(destination)
  if (path === '' || isExternalDestination(destination)) return undefined
  const decoded = decodePath(path).replace(/\\/g, '/')
  const joined = decoded.startsWith('/')
    ? posixNormalize(decoded.slice(1))
    : posixNormalize(`${directoryOf(sourcePath)}/${decoded}`)
  if (joined === '' || joined === '.' || joined === '..' || joined.startsWith('../')) return undefined
  return joined
}

function directoryOf(path: string): string {
  const cut = path.lastIndexOf('/')
  return cut < 0 ? '' : path.slice(0, cut)
}

function posixNormalize(path: string): string {
  const segments: string[] = []
  for (const segment of path.split('/')) {
    if (segment === '' || segment === '.') continue
    if (segment === '..') {
      segments.pop()
      continue
    }
    segments.push(segment)
  }
  return segments.join('/')
}

/**
 * 判断一个解析后的目标是否指向在范围的成对文档，并给出其英文锚点。
 *
 * @param destination - 链接目标原文。
 * @param context - 链接所在文档与配对范围判定。
 * @returns 成对文档目标；目标不属于成对语料时返回 undefined。
 */
export function pairedLinkTarget(
  destination: string,
  context: LinkContext,
): PairedLinkTarget | undefined {
  const destinationPath = resolveDestination(destination, context.sourcePath)
  if (destinationPath === undefined) return undefined
  const anchor = destinationPath.endsWith('.zh.md')
    ? destinationPath.slice(0, -'.zh.md'.length) + '.md'
    : destinationPath.endsWith('.md') ? destinationPath : undefined
  if (anchor === undefined || !context.isPairSource(anchor)) return undefined
  const { suffix } = splitDestination(destination)
  return { anchor, suffix, destinationPath }
}

/** 一侧文档的预期本地化路径。 */
export function expectedLocalePath(anchor: string, locale: 'en' | 'zh'): string {
  return locale === 'zh' ? anchor.replace(/\.md$/, '.zh.md') : anchor
}

/**
 * 计算语言切换行的规范文本。
 *
 * @param locale - 该文件的语言方向。
 * @param counterpart - 对侧文档的仓库相对路径。
 * @returns 切换行原文。
 */
export function expectedSwitcher(locale: 'en' | 'zh', counterpart: string): string {
  return locale === 'en'
    ? `English | [中文](/${counterpart})`
    : `[English](/${counterpart}) | 中文`
}

/**
 * 识别 H1 之后第一段里的语言切换行。
 *
 * @param scan - 文档扫描结果。
 * @returns 切换行信息；缺失或位置不对时返回 undefined。
 */
export function detectLanguageSwitcher(scan: MarkdownScan): LanguageSwitcher | undefined {
  const h1 = scan.headings.find(heading => heading.depth === 1)
  if (h1 === undefined) return undefined
  for (let index = h1.lineIndex + 1; index < scan.masked.length; index++) {
    if (scan.fenced[index] === true) return undefined
    const text = (scan.masked[index] ?? '').trim()
    if (text === '') continue
    const en = /^English \| \[中文\]\(([^()\s]+)\)$/.exec(text)
    if (en?.[1] !== undefined) return { lineIndex: index, text, target: en[1], locale: 'en' }
    const zh = /^\[English\]\(([^()\s]+)\) \| 中文$/.exec(text)
    if (zh?.[1] !== undefined) return { lineIndex: index, text, target: zh[1], locale: 'zh' }
    return undefined
  }
  return undefined
}

/**
 * 把成对文档链接目标替换为 locale 中立的语义标记，用于小节哈希。
 *
 * @param content - 文档原文。
 * @param scan - 该文档的扫描结果。
 * @param context - 链接解析上下文。
 * @returns 替换后的文本；非成对链接与图片保持原样。
 */
export function normalizePairedLinkTargets(
  content: string,
  scan: MarkdownScan,
  context: LinkContext,
): string {
  const edits: { start: number; end: number; value: string }[] = []
  for (const link of scan.links) {
    if (link.image) continue
    const target = pairedLinkTarget(link.destination, context)
    if (target === undefined) continue
    edits.push({ start: link.start, end: link.end, value: `pair:/${target.anchor}${target.suffix}` })
  }
  let normalized = content
  for (const edit of edits.sort((left, right) => right.start - left.start)) {
    normalized = normalized.slice(0, edit.start) + edit.value + normalized.slice(edit.end)
  }
  return normalized
}
