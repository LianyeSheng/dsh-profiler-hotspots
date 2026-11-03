/**
 * `verify-translation-pairing` 的检查、报告与记录写入引擎。
 *
 * 门禁输出遵循本仓库的制度：每条发现给出「发现 / 期望 / 修复 / 契约」四段，
 * 每次运行（含全绿）都以「未自动检查」段收尾。
 */

import { existsSync, mkdirSync, readFileSync, readdirSync, renameSync, unlinkSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import type { MarkdownLink, MarkdownScan } from './translation-links.ts'
import {
  detectLanguageSwitcher,
  expectedLocalePath,
  expectedSwitcher,
  isExternalDestination,
  pairedLinkTarget,
  scanMarkdown,
  splitDestination,
} from './translation-links.ts'
import type {
  TranslationPairingManifest,
  TranslationPairingRequest,
  TranslationPairPaths,
  TranslationStructureDivergence,
} from './translation-pairing.ts'
import {
  isTranslationPairingManifestExcluded,
  isTranslationScopeFile,
  NON_SOURCE_DIRECTORIES,
  parseTranslationPairingCliArgs,
  parseTranslationPairingManifest,
  translationPairPaths,
  translationStructureDiff,
  translationStructureSignature,
} from './translation-pairing.ts'
import type { TranslationPairingRecord } from './translation-pairing-record.ts'
import {
  computeTranslationPairingRecord,
  parseTranslationPairingRecord,
  renderTranslationPairingRecord,
  translationPairingRecordDiff,
} from './translation-pairing-record.ts'

/** 门禁规则编号。 */
export type PairingRule = 'P1' | 'P2' | 'P3' | 'P4' | 'P5'

/** 一条可执行的发现。 */
export interface PairingFinding {
  rule: PairingRule
  path: string
  line: number
  found: string
  expect: string
  fix: string
}

/** `--list` 报告的单篇状态。 */
export interface PairingState {
  source: string
  state: 'ok' | 'missing' | 'out-of-sync'
}

/** 一次门禁运行的完整结果。 */
export interface PairingReport {
  exitCode: 0 | 1 | 2
  mode: 'check' | 'list' | 'write' | 'usage'
  findings: PairingFinding[]
  states: PairingState[]
  messages: string[]
  summary: string
}

/** 门禁无法自动判断、必须留给 review 的项。 */
export const UNCHECKED_DECLARATION = [
  '未自动检查（4 项，需 review）',
  '  R1 译文忠实性   R2 术语一致性   R3 中文自然度',
  '  R4 行内代码、列表与表格顺序、图片替代文本与呈现、强调',
  '  清单：.agents/se/contracts/i18n/translation-rules.md',
].join('\n')

const CONTRACT = '.agents/se/contracts/i18n/README.md'
const MANIFEST = '.agents/se/scripts/docs/translation-pairing.manifest.json'

interface Corpus {
  root: string
  manifest: TranslationPairingManifest
  files: Set<string>
  /** 小写路径 → 磁盘实际路径，用于大小写不敏感的扩展名锚点。 */
  actualByLower: Map<string, string>
  /** 在范围、未被排除的英文锚点（可能只有对侧产物留在盘上）。 */
  sources: string[]
  /** 被排除路径下遗留的配对产物。 */
  excludedArtifacts: string[]
  isPairSource: (source: string) => boolean
}

function walk(root: string): string[] {
  const out: string[] = []
  const visit = (relative: string): void => {
    const absolute = relative === '' ? root : join(root, relative)
    let entries
    try {
      entries = readdirSync(absolute, { withFileTypes: true })
    } catch {
      return
    }
    for (const entry of entries) {
      const child = relative === '' ? entry.name : `${relative}/${entry.name}`
      if (entry.isDirectory()) {
        if (NON_SOURCE_DIRECTORIES.has(entry.name)) continue
        visit(child)
        continue
      }
      if (!entry.isFile()) continue
      const lowerChild = child.toLowerCase()
      if (lowerChild.endsWith('.md') || lowerChild.endsWith('.i18n.yaml')) out.push(child)
    }
  }
  visit('')
  return out.sort()
}

function stripArtifact(artifact: string): string {
  const lower = artifact.toLowerCase()
  if (lower.endsWith('.zh.md')) return `${artifact.slice(0, -'.zh.md'.length)}.md`
  return `${artifact.slice(0, -'.i18n.yaml'.length)}.md`
}

function readManifest(root: string): TranslationPairingManifest {
  const path = join(root, MANIFEST)
  if (!existsSync(path)) throw new Error(`缺少 ${MANIFEST}`)
  return parseTranslationPairingManifest(readFileSync(path, 'utf8'))
}

function buildCorpus(root: string): Corpus {
  const manifest = readManifest(root)
  const files = new Set(walk(root))
  const actualByLower = new Map<string, string>()
  for (const file of files) actualByLower.set(file.toLowerCase(), file)
  const excludedArtifacts: string[] = []
  const sourceSet = new Set<string>()
  /** Frozen archived decision records keep their triplet; links into them still normalize to a locale-neutral anchor. */
  const archivedAnchors = new Set<string>()
  for (const file of files) {
    if (isTranslationScopeFile(file) && !isTranslationPairingManifestExcluded(file, manifest)) sourceSet.add(file)
    const lowerFile = file.toLowerCase()
    if (file.startsWith('.agents/notes/archived/') && lowerFile.endsWith('.md') && !lowerFile.endsWith('.zh.md')) {
      archivedAnchors.add(file)
    }
    if (!lowerFile.endsWith('.zh.md') && !lowerFile.endsWith('.i18n.yaml')) continue
    const candidate = stripArtifact(file)
    const anchor = actualByLower.get(candidate.toLowerCase()) ?? candidate
    if (isTranslationPairingManifestExcluded(anchor, manifest)) {
      excludedArtifacts.push(file)
      continue
    }
    if (isTranslationScopeFile(anchor)) sourceSet.add(anchor)
  }
  const sources = [...sourceSet].sort()
  return {
    root,
    manifest,
    files,
    actualByLower,
    sources,
    excludedArtifacts,
    // Scope is a path rule, not a file list: a link into an in-scope document normalizes to
    // its locale-neutral anchor even when the installed counterpart is not on disk yet. The
    // same pair therefore hashes identically in its source layout and in its installed copy.
    isPairSource: source =>
      (isTranslationScopeFile(source) && !isTranslationPairingManifestExcluded(source, manifest))
      || archivedAnchors.has(source),
  }
}

function readRepositoryFile(root: string, file: string): string {
  return readFileSync(join(root, file), 'utf8')
}

function finding(
  rule: PairingRule,
  path: string,
  line: number,
  found: string,
  expect: string,
  fix: string,
): PairingFinding {
  return { rule, path, line, found, expect, fix }
}

function show(value: string | undefined): string {
  if (value === undefined) return '（缺失）'
  const text = JSON.stringify(value)
  return text.length > 72 ? `${text.slice(0, 72)}…` : text
}

function structureFinding(
  source: string,
  sidePath: string,
  divergence: TranslationStructureDivergence,
): PairingFinding {
  const en = show(divergence.en?.value)
  const zh = show(divergence.zh?.value)
  return finding(
    'P4',
    sidePath,
    divergence.zh?.line ?? divergence.en?.line ?? 1,
    `第 ${divergence.index} 个${divergence.field}两侧不一致：英文侧 ${en}，中文侧 ${zh}`,
    `两侧第 ${divergence.index} 个${divergence.field}逐项一致`,
    `让 ${sidePath} 的${divergence.field}与 ${source} 对齐；围栏代码块必须逐字相同，标题层级与顺序、表格行列数、列表类型与条目数、链接语义目标都要一一对应`,
  )
}

function switcherFinding(paths: TranslationPairPaths, scan: MarkdownScan, side: 'en' | 'zh'): PairingFinding | undefined {
  const path = side === 'en' ? paths.source : paths.zh
  const counterpart = side === 'en' ? paths.zh : paths.source
  const expected = expectedSwitcher(side, counterpart)
  const h1 = scan.headings.find(heading => heading.depth === 1)
  const line = h1 === undefined ? 1 : h1.lineIndex + 1
  const detected = detectLanguageSwitcher(scan)
  if (detected === undefined) {
    return finding(
      'P3',
      path,
      line,
      'H1 后的第一段不是规范的语言切换行',
      expected,
      `在 H1 之后空一行写入 ${expected}`,
    )
  }
  if (h1 !== undefined && detected.lineIndex !== h1.lineIndex + 2) {
    return finding(
      'P3',
      path,
      detected.lineIndex + 1,
      `语言切换行与 H1 之间隔了 ${Math.max(0, detected.lineIndex - h1.lineIndex - 2)} 个多余空行`,
      `H1 后恰好一个空行，切换行紧随其后（第 ${h1.lineIndex + 3} 行）`,
      `把切换行移到第 ${h1.lineIndex + 3} 行`,
    )
  }
  if (detected.text !== expected) {
    return finding(
      'P3',
      path,
      detected.lineIndex + 1,
      `语言切换行为 ${detected.text}（目标 ${detected.target}）`,
      expected,
      `把该行改为 ${expected}`,
    )
  }
  return undefined
}

function semanticLinkTarget(
  link: MarkdownLink,
  sidePath: string,
  corpus: Corpus,
): string {
  const target = pairedLinkTarget(link.destination, { sourcePath: sidePath, isPairSource: corpus.isPairSource })
  return target === undefined ? link.destination : `pair:/${target.anchor}${target.suffix}`
}

function localeFindings(paths: TranslationPairPaths, side: 'en' | 'zh', scan: MarkdownScan, corpus: Corpus): PairingFinding[] {
  const path = side === 'en' ? paths.source : paths.zh
  const switcher = detectLanguageSwitcher(scan)
  const out: PairingFinding[] = []
  for (const link of scan.links) {
    if (link.image) continue
    if (switcher !== undefined && link.line === switcher.lineIndex + 1) continue
    if (isExternalDestination(link.destination)) continue
    const target = pairedLinkTarget(link.destination, { sourcePath: path, isPairSource: corpus.isPairSource })
    if (target === undefined) continue
    const expected = expectedLocalePath(target.anchor, side)
    const authoredPath = splitDestination(link.destination).path
    if (target.destinationPath !== expected) {
      out.push(finding(
        'P5',
        path,
        link.line,
        `成对文档链接指向了 ${authoredPath}`,
        `/${expected}`,
        `把目标改为 /${expected}`,
      ))
      continue
    }
    if (!authoredPath.startsWith('/')) {
      out.push(finding(
        'P5',
        path,
        link.line,
        `成对文档链接 ${authoredPath} 没有按仓库根解析`,
        `/${expected}`,
        `改写为 /${expected}`,
      ))
    }
  }
  return out
}

function recordLine(content: string, key: string): number {
  const lines = content.split('\n')
  const index = lines.indexOf(`${key}:`)
  return index < 0 ? 1 : index + 1
}

function recordFindings(
  paths: TranslationPairPaths,
  metaContent: string,
  en: string,
  zh: string,
  context: { isPairSource: (source: string) => boolean },
): PairingFinding[] {
  const recorded = parseTranslationPairingRecord(metaContent)
  if (recorded === undefined) {
    return [finding(
      'P2',
      paths.meta,
      1,
      '一致性记录格式不合法（应为文件头注释 + 每小节三行：键、en、zh）',
      '规范的一致性记录',
      `重录该对：node .agents/se/scripts/docs/verify-translation-pairing.ts --write ${paths.source}`,
    )]
  }
  const current = computeTranslationPairingRecord(paths, en, zh, context)
  const diff = translationPairingRecordDiff(recorded, current)
  if (diff.length === 0) {
    if (metaContent === renderTranslationPairingRecord(current)) return []
    return [finding(
      'P2',
      paths.meta,
      1,
      '一致性记录的内容正确但不是规范格式',
      '按当前内容渲染出的规范记录',
      `重录该对：node .agents/se/scripts/docs/verify-translation-pairing.ts --write ${paths.source}`,
    )]
  }
  return diff.map((entry) => {
    const found = entry.kind === 'unconfirmed'
      ? `小节 ${entry.key} 有未确认的内容`
      : entry.kind === 'stale'
        ? `小节 ${entry.key} 已记录但不再有内容`
        : `小节 ${entry.key} 自确认后已变更（${entry.sides.join('、')}）`
    return finding(
      'P2',
      paths.meta,
      recordLine(metaContent, entry.key),
      found,
      '记录中的每个小节哈希都等于两侧当前内容的哈希',
      `先让两侧内容一致，再重录该对：node .agents/se/scripts/docs/verify-translation-pairing.ts --write ${paths.source}`,
    )
  })
}

interface PairTexts {
  en: string
  zh: string
}

function pairTexts(root: string, paths: TranslationPairPaths): PairTexts {
  return { en: readRepositoryFile(root, paths.source), zh: readRepositoryFile(root, paths.zh) }
}

/** 检查一对（P3/P4/P2/P5）；完整性由调用方按 P1 处理。 */
function inspectPair(corpus: Corpus, paths: TranslationPairPaths, metaContent?: string): PairingFinding[] {
  const findings: PairingFinding[] = []
  const texts = pairTexts(corpus.root, paths)
  const scanEn = scanMarkdown(texts.en)
  const scanZh = scanMarkdown(texts.zh)
  for (const [path, scan] of [[paths.source, scanEn], [paths.zh, scanZh]] as const) {
    for (const problem of scan.problems) {
      findings.push(finding('P4', path, 1, problem, '可被结构签名完整分析的 Markdown', '改用 ATX 标题并闭合每个围栏代码块'))
    }
  }
  const enSwitcher = switcherFinding(paths, scanEn, 'en')
  if (enSwitcher !== undefined) findings.push(enSwitcher)
  const zhSwitcher = switcherFinding(paths, scanZh, 'zh')
  if (zhSwitcher !== undefined) findings.push(zhSwitcher)

  const signatureEn = translationStructureSignature(
    scanEn,
    link => semanticLinkTarget(link, paths.source, corpus),
    detectLanguageSwitcher(scanEn)?.lineIndex,
  )
  const signatureZh = translationStructureSignature(
    scanZh,
    link => semanticLinkTarget(link, paths.zh, corpus),
    detectLanguageSwitcher(scanZh)?.lineIndex,
  )
  for (const divergence of translationStructureDiff(signatureEn, signatureZh)) {
    findings.push(structureFinding(paths.source, paths.zh, divergence))
  }

  findings.push(...localeFindings(paths, 'en', scanEn, corpus))
  findings.push(...localeFindings(paths, 'zh', scanZh, corpus))

  if (metaContent !== undefined) {
    try {
      findings.push(...recordFindings(paths, metaContent, texts.en, texts.zh, { isPairSource: corpus.isPairSource }))
    } catch (error) {
      findings.push(finding(
        'P2',
        paths.meta,
        1,
        `无法计算一致性记录：${error instanceof Error ? error.message : String(error)}`,
        '两侧分节结构可以被记录',
        `先修复两侧的标题结构，再运行 node .agents/se/scripts/docs/verify-translation-pairing.ts --write ${paths.source}`,
      ))
    }
  }
  return findings
}

function completenessFindings(corpus: Corpus, source: string): PairingFinding[] {
  const paths = translationPairPaths(source)
  const hasSource = corpus.files.has(paths.source)
  const hasZh = corpus.files.has(paths.zh)
  const hasMeta = corpus.files.has(paths.meta)
  const findings: PairingFinding[] = []
  if (!hasSource) {
    findings.push(finding(
      'P1',
      hasZh ? paths.zh : paths.meta,
      1,
      `存在配对产物但缺少英文锚点 ${paths.source}`,
      '三件套齐全',
      `补写 ${paths.source}，或删除残留的 ${hasZh ? paths.zh : paths.meta}`,
    ))
    return findings
  }
  if (!hasZh) {
    findings.push(finding(
      'P1',
      paths.source,
      1,
      `缺少中文对侧 ${paths.zh}`,
      '在范围文档必须成对合并',
      `创建 ${paths.zh}（参照 .agents/se/contracts/i18n/translation-rules.md），再运行 node .agents/se/scripts/docs/verify-translation-pairing.ts --write ${paths.source}`,
    ))
  }
  if (!hasMeta && hasZh) {
    findings.push(finding(
      'P1',
      paths.source,
      1,
      `缺少一致性记录 ${paths.meta}`,
      '每个完整配对都有一份规范记录',
      `运行 node .agents/se/scripts/docs/verify-translation-pairing.ts --write ${paths.source}`,
    ))
  }
  return findings
}

function pairState(corpus: Corpus, source: string): PairingState {
  const paths = translationPairPaths(source)
  if (!corpus.files.has(paths.source) || !corpus.files.has(paths.zh) || !corpus.files.has(paths.meta)) {
    return { source, state: 'missing' }
  }
  try {
    const meta = readRepositoryFile(corpus.root, paths.meta)
    const findings = inspectPair(corpus, paths, meta)
    return { source, state: findings.length === 0 ? 'ok' : 'out-of-sync' }
  } catch {
    return { source, state: 'out-of-sync' }
  }
}

function validateNamedAnchors(corpus: Corpus, anchors: string[]): PairingFinding[] {
  const findings: PairingFinding[] = []
  for (const anchor of anchors) {
    if (!isTranslationScopeFile(anchor) || isTranslationPairingManifestExcluded(anchor, corpus.manifest)) {
      findings.push(finding(
        'P1',
        anchor,
        1,
        '不是在范围、未被排除的配对',
        '.agents/se/contracts/i18n/README.md 定义的在范围文档（任取三件套之一或去后缀 stem）',
        '改传一个在范围配对路径',
      ))
      continue
    }
    const paths = translationPairPaths(anchor)
    if (![paths.source, paths.zh, paths.meta].some(file => corpus.files.has(file))) {
      findings.push(finding(
        'P1',
        anchor,
        1,
        '磁盘上没有任何该配对的三个文件',
        '至少存在英文源、中文对侧或记录之一',
        `确认路径，或先创建 ${paths.source}`,
      ))
    }
  }
  return findings
}

/**
 * 运行一次配对门禁。
 *
 * @param root - 仓库根绝对路径。
 * @param argv - 脚本名之后的命令行参数。
 * @returns 结构化结果，由调用方负责打印。
 */
export function checkTranslationPairing(root: string, argv: string[]): PairingReport {
  let request: TranslationPairingRequest
  try {
    request = parseTranslationPairingCliArgs(argv)
  } catch (error) {
    return {
      exitCode: 2,
      mode: 'usage',
      findings: [],
      states: [],
      messages: [],
      summary: `verify-translation-pairing: ${error instanceof Error ? error.message : String(error)}`,
    }
  }

  let corpus: Corpus
  try {
    corpus = buildCorpus(root)
  } catch (error) {
    return {
      exitCode: 2,
      mode: 'usage',
      findings: [],
      states: [],
      messages: [],
      summary: `verify-translation-pairing: ${error instanceof Error ? error.message : String(error)}`,
    }
  }

  request = {
    ...request,
    anchors: request.anchors.map(anchor => (corpus.files.has(anchor) ? anchor : corpus.actualByLower.get(anchor.toLowerCase()) ?? anchor)),
  }

  if (request.mode === 'list') {
    const states = corpus.sources.map(source => pairState(corpus, source))
    const counts = { ok: 0, missing: 0, 'out-of-sync': 0 }
    for (const state of states) counts[state.state] += 1
    const artifactLines = corpus.excludedArtifacts.map(artifact => `excluded-artifact  ${artifact}`)
    return {
      exitCode: 0,
      mode: 'list',
      findings: [],
      states,
      messages: [...states.map(state => `${state.state}  ${state.source}`), ...artifactLines],
      summary: `verify-translation-pairing: ${states.length} 对文档（ok ${counts.ok}，missing ${counts.missing}，out-of-sync ${counts['out-of-sync']}）`
        + (artifactLines.length > 0 ? `，${artifactLines.length} 个被排除路径产物` : ''),
    }
  }

  if (request.mode === 'write') {
    const anchors = request.anchors
    const invalid = validateNamedAnchors(corpus, anchors)
    if (invalid.length > 0) {
      return {
        exitCode: 2,
        mode: 'usage',
        findings: invalid,
        states: [],
        messages: [],
        summary: 'verify-translation-pairing: 点名了不可重录的配对',
      }
    }
    const targets = request.scope === 'pairs' ? anchors : corpus.sources
    const pending: { source: string; meta: string; content: string }[] = []
    let recorded = 0
    let skipped = 0
    for (const source of targets) {
      const paths = translationPairPaths(source)
      if (!corpus.files.has(paths.source) || !corpus.files.has(paths.zh)) {
        if (request.scope === 'pairs') {
          return {
            exitCode: 2,
            mode: 'usage',
            findings: [],
            states: [],
            messages: [],
            summary: `verify-translation-pairing: 无法重录 ${source}：缺少${corpus.files.has(paths.source) ? ` ${paths.zh}` : ` ${paths.source}`}`,
          }
        }
        skipped += 1
        continue
      }
      try {
        const texts = pairTexts(root, paths)
        const content = renderTranslationPairingRecord(computeTranslationPairingRecord(paths, texts.en, texts.zh, {
          isPairSource: corpus.isPairSource,
        }))
        recorded += 1
        pending.push({ source, meta: paths.meta, content })
      } catch (error) {
        return {
          exitCode: 2,
          mode: 'usage',
          findings: [],
          states: [],
          messages: [],
          summary: `verify-translation-pairing: 无法重录 ${source}：${error instanceof Error ? error.message : String(error)}`,
        }
      }
    }
    const messages: string[] = []
    const staged: { metaPath: string; tempPath: string; meta: string }[] = []
    for (const item of pending) {
      const metaPath = join(root, item.meta)
      if (existsSync(metaPath) && readFileSync(metaPath, 'utf8') === item.content) continue
      const tempPath = `${metaPath}.tmp-pairing-${process.pid}`
      try {
        mkdirSync(dirname(metaPath), { recursive: true })
        writeFileSync(tempPath, item.content)
        staged.push({ metaPath, tempPath, meta: item.meta })
      } catch (error) {
        for (const entry of [...staged, { tempPath }]) {
          try {
            unlinkSync(entry.tempPath)
          } catch {
            // 临时文件可能已被移除；真正的失败在下面报告。
          }
        }
        return {
          exitCode: 2,
          mode: 'usage',
          findings: [],
          states: [],
          messages,
          summary: `verify-translation-pairing: 无法写入 ${item.meta}：${error instanceof Error ? error.message : String(error)}`,
        }
      }
    }
    for (const entry of staged) {
      renameSync(entry.tempPath, entry.metaPath)
      messages.push(`verify-translation-pairing: 已重录 ${entry.meta}`)
    }
    const written = staged.length
    return {
      exitCode: 0,
      mode: 'write',
      findings: [],
      states: [],
      messages,
      summary: `verify-translation-pairing: 写入 ${written} 个记录（处理 ${recorded} 对，跳过 ${skipped} 对不完整配对）；运行检查验证配对。`,
    }
  }

  const anchors = request.scope === 'pairs' ? request.anchors : corpus.sources
  const findings: PairingFinding[] = []
  if (request.scope === 'pairs') {
    const invalid = validateNamedAnchors(corpus, anchors)
    if (invalid.length > 0) {
      return {
        exitCode: 2,
        mode: 'usage',
        findings: invalid,
        states: [],
        messages: [],
        summary: 'verify-translation-pairing: 点名了不在范围的配对',
      }
    }
  }
  if (request.scope === 'corpus') {
    for (const artifact of corpus.excludedArtifacts) {
      findings.push(finding(
        'P1',
        artifact,
        1,
        '被排除路径带有配对产物',
        '被排除路径不得有 .zh.md 与 .i18n.yaml',
        `删除 ${artifact}`,
      ))
    }
  }
  for (const source of anchors) {
    try {
      findings.push(...completenessFindings(corpus, source))
      const paths = translationPairPaths(source)
      if (corpus.files.has(paths.source) && corpus.files.has(paths.zh)) {
        const meta = corpus.files.has(paths.meta) ? readRepositoryFile(root, paths.meta) : undefined
        findings.push(...inspectPair(corpus, paths, meta))
      }
    } catch (error) {
      findings.push(finding(
        'P1',
        source,
        1,
        `无法读取或解析配对：${error instanceof Error ? error.message : String(error)}`,
        '配对文件可读、为 UTF-8，且 Markdown 可分析',
        '修复文件权限/编码或结构问题后重跑',
      ))
    }
  }
  const summary = findings.length === 0
    ? `verify-translation-pairing: 通过（检查 ${anchors.length} 对文档，0 处错误）`
    : `verify-translation-pairing: 失败（检查 ${anchors.length} 对文档，${findings.length} 处错误）`
  return {
    exitCode: findings.length === 0 ? 0 : 1,
    mode: 'check',
    findings,
    states: [],
    messages: [],
    summary,
  }
}

function renderFinding(item: PairingFinding): string {
  return [
    `✗ ${item.path}:${item.line}  [${item.rule}]`,
    `  发现：${item.found}`,
    `  期望：${item.expect}`,
    `  修复：${item.fix}`,
    `  契约：${CONTRACT}#${item.rule.toLowerCase()}`,
  ].join('\n')
}

/**
 * 把一次运行结果渲染为门禁输出文本。
 *
 * @param report - 引擎结果。
 * @returns 完整输出，含未自动检查段；usage 模式只输出错误行。
 */
export function formatPairingReport(report: PairingReport): string {
  if (report.mode === 'usage') {
    const usageBlocks = report.findings.map(renderFinding)
    if (usageBlocks.length > 0) usageBlocks.push('')
    for (const message of report.messages) usageBlocks.push(message)
    usageBlocks.push(report.summary)
    usageBlocks.push('')
    usageBlocks.push(UNCHECKED_DECLARATION)
    return usageBlocks.join('\n')
  }
  const blocks: string[] = []
  for (const item of report.findings) blocks.push(renderFinding(item))
  if (report.findings.length > 0) blocks.push('')
  for (const message of report.messages) blocks.push(message)
  blocks.push(report.summary)
  blocks.push('')
  blocks.push(UNCHECKED_DECLARATION)
  return blocks.join('\n')
}
