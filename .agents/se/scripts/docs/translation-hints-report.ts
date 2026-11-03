/**
 * Translation sync hints (read-only).
 *
 * For a pair whose two sides drifted, print exactly two things:
 * 1. changed sections, so the counterpart can be patched minimally;
 * 2. terminology hits and missing translations for those sections only.
 *
 * The changed-surface baseline prefers the consistency record (so an uncommitted working
 * tree can still be localized) and falls back to git diff when no record exists. Workflow
 * guidance lives in the skill, not in this tool.
 */

import { execFileSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { scanMarkdown } from './translation-links.ts'
import { checkTranslationPairing } from './translation-pairing-check.ts'
import {
  isTranslationScopeFile,
  isTranslationPairingManifestExcluded,
  pairAnchorOfArgument,
  parseTranslationPairingManifest,
  translationPairPaths,
  type TranslationPairPaths,
} from './translation-pairing.ts'
import {
  computeTranslationPairingRecord,
  parseTranslationPairingRecord,
  translationPairingRecordDiff,
  translationSideSections,
  type TranslationPairingRecord,
  type TranslationPairingRecordContext,
  type TranslationSectionEntry,
} from './translation-pairing-record.ts'

const USAGE = [
  'Usage:',
  '  node .agents/se/scripts/docs/translation-hints.ts <one of the pair files | stem> [--json]',
  '  node .agents/se/scripts/docs/translation-hints.ts --term <english term> [--json]',
].join('\n')

const MANIFEST = '.agents/se/scripts/docs/translation-pairing.manifest.json'
const TERMINOLOGY = '.agents/se/contracts/i18n/terminology.md'
const MAX_ITEMS = 20

/** Pair state determined by the hints tool. */
export type HintsState = 'ok' | 'out-of-sync' | 'missing' | 'usage'

/** A section that needs translation or re-translation. */
export interface HintsChangedSection {
  /** English heading slug path; on the Chinese side without a record key it looks like `zh#3`. */
  key: string
  side: 'en' | 'zh' | 'both'
  kind: 'added' | 'changed' | 'removed' | 'unknown'
  /** 1-based line number. */
  line?: number
}

/** One glossary term matched on the source side. */
export interface HintsTermHit {
  term: string
  translation: string
  /** First matching line on the source side. */
  line?: number
  /** Number of matches on the source side. */
  count: number
}

/** A term present on the source side but missing its translation on the target side. */
export interface HintsMissingTerm {
  term: string
  translation: string
  direction: 'en-to-zh' | 'zh-to-en'
  line?: number
}

/** Full data emitted by `--json`. */
export interface HintsData {
  source: string
  zh: string
  meta: string
  state: Exclude<HintsState, 'usage'>
  sectionCounts: { en: number; zh: number; recorded: number }
  changedSections: HintsChangedSection[]
  directions: ('en-to-zh' | 'zh-to-en')[]
  termHits: HintsTermHit[]
  missingTerms: HintsMissingTerm[]
}

/** Result of the `--term` corpus search. */
export interface HintsTermSearch {
  term: string
  glossary?: { translation: string; line: number }
  en: { path: string; line: number; text: string }[]
  zh: { path: string; line: number; text: string }[]
}

/** Result of one hints run. */
export interface HintsReport {
  exitCode: 0 | 2
  mode: 'brief' | 'term' | 'usage'
  summary: string
  data?: HintsData
  termSearch?: HintsTermSearch
  json: boolean
}

interface CliRequest {
  json: boolean
  anchor?: string
  term?: string
}

interface GlossaryRow {
  en: string
  zh: string
  /** 1-based line number in terminology.md. */
  line: number
}

interface GitFileChange {
  tracked: boolean
  /** Changed line ranges on the new-file side; a pure deletion has count 0. */
  ranges: { start: number; end: number }[]
}

interface LineRange {
  start: number
  end: number
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function readIfExists(root: string, file: string): string | undefined {
  const absolute = join(root, file)
  if (!existsSync(absolute)) return undefined
  try {
    return readFileSync(absolute, 'utf8')
  } catch {
    return undefined
  }
}

function snippet(text: string, max = 160): string {
  const compact = text.trim().replace(/\s+/g, ' ')
  return compact.length > max ? `${compact.slice(0, max - 1)}…` : compact
}

function parseCliArguments(argv: string[]): CliRequest {
  const request: CliRequest = { json: false }
  for (let index = 0; index < argv.length; index++) {
    const argument = argv[index]
    if (argument === undefined) continue
    if (argument === '--json') {
      request.json = true
      continue
    }
    if (argument === '--term') {
      const value = argv[++index]
      if (value === undefined || value.startsWith('--')) throw new Error('--term needs an English term')
      if (request.term !== undefined) throw new Error('--term may be given once')
      request.term = value
      continue
    }
    if (argument.startsWith('--')) throw new Error(`unknown argument: ${argument}`)
    if (request.anchor !== undefined) throw new Error(`pass exactly one pair; got extra argument: ${argument}`)
    request.anchor = argument
  }
  if (request.term === undefined && request.anchor === undefined) {
    throw new Error('usage: node .agents/se/scripts/docs/translation-hints.ts <one of the pair files | stem> [--json], or --term <english term>')
  }
  if (request.term !== undefined && request.anchor !== undefined) {
    throw new Error('--term searches the corpus for precedents and takes no pair argument')
  }
  return request
}

function loadPairingContext(root: string): TranslationPairingRecordContext {
  const content = readIfExists(root, MANIFEST)
  const manifest = content === undefined
    ? { excluded: [] as string[] }
    : parseTranslationPairingManifest(content)
  return {
    isPairSource: source => isTranslationScopeFile(source) && !isTranslationPairingManifestExcluded(source, manifest),
  }
}

function glossary(root: string): GlossaryRow[] {
  const content = readIfExists(root, TERMINOLOGY)
  if (content === undefined) return []
  const rows: GlossaryRow[] = []
  const lines = content.split('\n')
  for (const [index, line] of lines.entries()) {
    const trimmed = line.trim()
    if (!trimmed.startsWith('|')) continue
    const cells = trimmed.replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim())
    if (cells.length < 4) continue
    const en = (cells[0] ?? '').replace(/`/g, '')
    const zh = (cells[1] ?? '').replace(/`/g, '')
    if (en === '' || en === 'English' || /^-+$/.test(en)) continue
    rows.push({ en, zh, line: index + 1 })
  }
  return rows
}

/** Term matching: allow common plural/past/progressive suffixes so singular-only matches are avoided. */
function termPattern(term: string): RegExp {
  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const lead = /^[A-Za-z0-9]/.test(term) ? '(?<![A-Za-z0-9_-])' : ''
  const trail = /[A-Za-z0-9]$/.test(term) ? '(?![A-Za-z0-9_-])' : ''
  return new RegExp(`${lead}${escaped}(?:s|es|ed|ing)?${trail}`, 'gi')
}

function matchingLines(content: string, pattern: RegExp): number[] {
  const scan = scanMarkdown(content)
  const lines = content.split('\n')
  const out: number[] = []
  for (let index = 0; index < lines.length; index++) {
    if (scan.fenced[index] === true) continue
    pattern.lastIndex = 0
    if (pattern.test(lines[index] ?? '')) out.push(index + 1)
  }
  return out
}

function collectTerminology(
  sourceContent: string,
  targetContent: string | undefined,
  rows: GlossaryRow[],
  direction: 'en-to-zh' | 'zh-to-en',
  includeLine?: (line: number) => boolean,
): { hits: HintsTermHit[]; missing: HintsMissingTerm[] } {
  const hits: HintsTermHit[] = []
  const missing: HintsMissingTerm[] = []
  for (const row of rows) {
    if (direction === 'en-to-zh') {
      const all = matchingLines(sourceContent, termPattern(row.en))
      const lines = includeLine === undefined ? all : all.filter(includeLine)
      if (lines.length === 0) continue
      hits.push({ term: row.en, translation: row.zh, line: lines[0], count: lines.length })
      if (targetContent !== undefined && row.zh !== '' && !targetContent.includes(row.zh)) {
        missing.push({ term: row.en, translation: row.zh, direction, line: lines[0] })
      }
    } else {
      if (row.zh === '') continue
      const all = matchingLines(sourceContent, termPattern(row.zh))
      const lines = includeLine === undefined ? all : all.filter(includeLine)
      if (lines.length === 0) continue
      hits.push({ term: row.zh, translation: row.en, line: lines[0], count: lines.length })
      if (targetContent !== undefined && !termPattern(row.en).test(targetContent)) {
        missing.push({ term: row.zh, translation: row.en, direction, line: lines[0] })
      }
    }
  }
  return { hits, missing }
}

function computeGitFileChange(root: string, file: string): GitFileChange | undefined {
  try {
    execFileSync('git', ['-C', root, 'rev-parse', '--is-inside-work-tree'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
  } catch {
    return undefined
  }
  let tracked = true
  try {
    execFileSync('git', ['-C', root, 'ls-files', '--error-unmatch', '--', file], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
  } catch {
    tracked = false
  }
  if (!tracked) return { tracked, ranges: [] }
  let output = ''
  try {
    output = execFileSync('git', ['-C', root, 'diff', '--no-color', '--unified=0', 'HEAD', '--', file], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
  } catch {
    try {
      output = execFileSync('git', ['-C', root, 'diff', '--no-color', '--unified=0', '--', file], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
    } catch {
      return { tracked, ranges: [] }
    }
  }
  const ranges: { start: number; end: number }[] = []
  for (const line of output.split('\n')) {
    const match = /^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@/.exec(line)
    if (match === null) continue
    const start = Number(match[2])
    const count = match[3] === undefined ? 1 : Number(match[3])
    ranges.push({ start, end: count === 0 ? start - 1 : start + count - 1 })
  }
  return { tracked, ranges }
}

function sectionAt(sections: TranslationSectionEntry[], line: number): number {
  let found = 0
  for (const [index, section] of sections.entries()) {
    if (section.line <= line) found = index
    else break
  }
  return found
}

function changedFromGit(
  ranges: { start: number; end: number }[],
  sections: TranslationSectionEntry[],
  side: 'en' | 'zh',
): HintsChangedSection[] {
  const out: HintsChangedSection[] = []
  const seen = new Set<string>()
  for (const range of ranges) {
    const from = sectionAt(sections, Math.max(1, range.start))
    const to = sectionAt(sections, Math.max(1, range.end))
    for (let index = from; index <= to; index++) {
      const section = sections[index]
      if (section === undefined) continue
      const key = side === 'en' ? section.key : `zh#${index + 1}`
      if (seen.has(key)) continue
      seen.add(key)
      out.push({ key, side, kind: 'changed', line: section.line })
    }
  }
  return out
}

function bestEffortRecordDiff(
  recorded: TranslationPairingRecord,
  enSections: TranslationSectionEntry[],
  zhSections: TranslationSectionEntry[],
): HintsChangedSection[] {
  const out: HintsChangedSection[] = []
  const enKeys = new Set(enSections.map(section => section.key))
  for (const section of enSections) {
    const confirmed = recorded.get(section.key)
    if (confirmed === undefined) {
      if (!section.empty) out.push({ key: section.key, side: 'en', kind: 'added', line: section.line })
    } else if (confirmed.en !== section.hash) {
      out.push({ key: section.key, side: 'en', kind: 'changed', line: section.line })
    }
  }
  const recordedKeys = [...recorded.keys()]
  // The record omits sections that are empty on both sides; skip those when aligning the Chinese side by recorded-key order.
  let zhIndex = 0
  for (const key of recordedKeys) {
    if (!enKeys.has(key)) out.push({ key, side: 'en', kind: 'removed' })
    while (zhIndex < zhSections.length && (zhSections[zhIndex]?.empty ?? false)) zhIndex += 1
    const zhSection = zhSections[zhIndex]
    zhIndex += 1
    const confirmed = recorded.get(key)
    if (zhSection !== undefined && confirmed !== undefined && zhSection.hash !== confirmed.zh) {
      out.push({ key, side: 'zh', kind: 'changed', line: zhSection.line })
    }
  }
  while (zhIndex < zhSections.length && (zhSections[zhIndex]?.empty ?? false)) zhIndex += 1
  for (let index = zhIndex; index < zhSections.length; index++) {
    const section = zhSections[index]
    if (section !== undefined && !section.empty) out.push({ key: `zh#${index + 1}`, side: 'zh', kind: 'added', line: section.line })
  }
  return out
}

function recordDiff(
  recorded: TranslationPairingRecord,
  current: TranslationPairingRecord,
  enSections: TranslationSectionEntry[],
  zhSections: TranslationSectionEntry[],
): HintsChangedSection[] {
  const out: HintsChangedSection[] = []
  const indexByKey = new Map(enSections.map((section, index) => [section.key, index]))
  for (const diff of translationPairingRecordDiff(recorded, current)) {
    const index = indexByKey.get(diff.key)
    const enSection = index === undefined ? undefined : enSections[index]
    const zhSection = index === undefined ? undefined : zhSections[index]
    if (diff.kind === 'unconfirmed') {
      out.push({ key: diff.key, side: 'en', kind: 'added', line: enSection?.line })
      continue
    }
    if (diff.kind === 'stale') {
      out.push({ key: diff.key, side: 'en', kind: 'removed' })
      continue
    }
    const side = diff.sides.length === 2 ? 'both' : (diff.sides[0] ?? 'en')
    out.push({ key: diff.key, side, kind: 'changed', line: side === 'zh' ? zhSection?.line ?? enSection?.line : enSection?.line })
  }
  return out
}

function baselineSections(
  root: string,
  paths: TranslationPairPaths,
  en: string,
  zh: string,
  context: TranslationPairingRecordContext,
  recorded: TranslationPairingRecord | undefined,
  enSections: TranslationSectionEntry[],
  zhSections: TranslationSectionEntry[],
): { baseline: 'record' | 'git-diff' | 'none'; changed: HintsChangedSection[] } {
  if (recorded !== undefined) {
    try {
      const current = computeTranslationPairingRecord(paths, en, zh, context)
      return { baseline: 'record', changed: recordDiff(recorded, current, enSections, zhSections) }
    } catch {
      return { baseline: 'record', changed: bestEffortRecordDiff(recorded, enSections, zhSections) }
    }
  }
  const enChange = computeGitFileChange(root, paths.source)
  const zhChange = computeGitFileChange(root, paths.zh)
  const changed: HintsChangedSection[] = []
  if (enChange !== undefined && enChange.ranges.length > 0) changed.push(...changedFromGit(enChange.ranges, enSections, 'en'))
  if (zhChange !== undefined && zhChange.ranges.length > 0) changed.push(...changedFromGit(zhChange.ranges, zhSections, 'zh'))
  return { baseline: changed.length > 0 ? 'git-diff' : 'none', changed }
}

function assembleChangedList(
  state: HintsState,
  enSections: TranslationSectionEntry[],
  zhSections: TranslationSectionEntry[],
  baseline: HintsChangedSection[],
): HintsChangedSection[] {
  if (state !== 'missing') return baseline
  if (zhSections.length === 0) {
    return enSections.filter(section => !section.empty).map(section => ({ key: section.key, side: 'en' as const, kind: 'added' as const, line: section.line }))
  }
  if (enSections.length === 0) {
    return zhSections
      .map((section, index) => ({ key: `zh#${index + 1}`, side: 'zh' as const, kind: 'added' as const, line: section.line }))
      .filter((_, index) => !(zhSections[index]?.empty ?? false))
  }
  return baseline
}

function sectionRanges(sections: TranslationSectionEntry[]): LineRange[] {
  return sections.map((section, index) => ({
    start: section.line,
    end: (sections[index + 1]?.line ?? Number.MAX_SAFE_INTEGER) - 1,
  }))
}

function rangesForChanged(
  changedSections: HintsChangedSection[],
  sections: TranslationSectionEntry[],
  side: 'en' | 'zh',
): LineRange[] {
  const all = sectionRanges(sections)
  const out: LineRange[] = []
  for (const section of changedSections) {
    if (section.kind === 'removed') continue
    if (side === 'en' && section.side === 'zh') continue
    if (side === 'zh' && section.side === 'en') continue
    const index = side === 'en'
      ? sections.findIndex(candidate => candidate.key === section.key)
      : sections.findIndex(candidate => candidate.line === section.line)
    const range = index < 0 ? undefined : all[index]
    if (range !== undefined) out.push(range)
  }
  return out
}

function includeLineFilter(ranges: LineRange[]): ((line: number) => boolean) | undefined {
  if (ranges.length === 0) return undefined
  return line => ranges.some(range => line >= range.start && line <= range.end)
}

function buildData(
  root: string,
  paths: TranslationPairPaths,
  en: string | undefined,
  zh: string | undefined,
  meta: string | undefined,
): HintsData {
  const context = loadPairingContext(root)
  const enSections = en === undefined ? [] : translationSideSections(en, paths.source, context)
  const zhSections = zh === undefined ? [] : translationSideSections(zh, paths.zh, context)
  const recorded = meta === undefined ? undefined : parseTranslationPairingRecord(meta)
  const state: Exclude<HintsState, 'usage'> = en === undefined || zh === undefined ? 'missing' : 'out-of-sync'
  const baseline = state === 'missing'
    ? { baseline: 'none' as const, changed: [] as HintsChangedSection[] }
    : baselineSections(root, paths, en ?? '', zh ?? '', context, recorded, enSections, zhSections)
  const changedSections = assembleChangedList(state, enSections, zhSections, baseline.changed)
  const isOk = state === 'out-of-sync' && recorded !== undefined && enSections.length === zhSections.length && changedSections.length === 0
  if (isOk) {
    return {
      source: paths.source,
      zh: paths.zh,
      meta: paths.meta,
      state: 'ok',
      sectionCounts: { en: enSections.length, zh: zhSections.length, recorded: recorded.size },
      changedSections: [],
      directions: [],
      termHits: [],
      missingTerms: [],
    }
  }
  const directions: ('en-to-zh' | 'zh-to-en')[] = []
  if (state === 'missing') {
    directions.push(zh === undefined ? 'en-to-zh' : 'zh-to-en')
  } else {
    const enChanged = changedSections.some(section => section.side === 'en' || section.side === 'both')
    const zhChanged = changedSections.some(section => section.side === 'zh' || section.side === 'both')
    if (enChanged || !zhChanged) directions.push('en-to-zh')
    if (zhChanged || !enChanged) directions.push('zh-to-en')
  }
  const rows = glossary(root)
  const hits: HintsTermHit[] = []
  const missingTerms: HintsMissingTerm[] = []
  const enFilter = includeLineFilter(rangesForChanged(changedSections, enSections, 'en'))
  const zhFilter = includeLineFilter(rangesForChanged(changedSections, zhSections, 'zh'))
  if (directions.includes('en-to-zh') && en !== undefined) {
    const result = collectTerminology(en, zh, rows, 'en-to-zh', enFilter)
    hits.push(...result.hits)
    missingTerms.push(...result.missing)
  }
  if (directions.includes('zh-to-en') && zh !== undefined) {
    const result = collectTerminology(zh, en, rows, 'zh-to-en', zhFilter)
    hits.push(...result.hits)
    missingTerms.push(...result.missing)
  }
  const dedupedHits = [...new Map(hits.map(hit => [`${hit.term}|${hit.translation}`, hit])).values()]
  return {
    source: paths.source,
    zh: paths.zh,
    meta: paths.meta,
    state,
    sectionCounts: { en: enSections.length, zh: zhSections.length, recorded: recorded?.size ?? 0 },
    changedSections,
    directions,
    termHits: dedupedHits,
    missingTerms,
  }
}

function renderChangedSections(data: HintsData): string[] {
  if (data.changedSections.length === 0) return []
  const counts = { added: 0, changed: 0, removed: 0, unknown: 0 }
  for (const section of data.changedSections) counts[section.kind] += 1
  const lines = [`changed sections (+${counts.added} ~${counts.changed} -${counts.removed}):`]
  for (const section of data.changedSections.slice(0, MAX_ITEMS)) {
    const marker = section.kind === 'added' ? '+' : section.kind === 'changed' ? '~' : section.kind === 'removed' ? '-' : '?'
    const where = section.side === 'zh' || section.key.startsWith('zh#') ? 'zh' : 'en'
    lines.push(`  ${marker} ${section.key}${section.line === undefined ? '' : `   ${where} L${section.line}`}`)
  }
  if (data.changedSections.length > MAX_ITEMS) lines.push(`  ... (${data.changedSections.length - MAX_ITEMS} more)`)
  return lines
}

function renderTerminology(data: HintsData): string[] {
  if (data.termHits.length === 0 && data.missingTerms.length === 0) return []
  // One line per glossary term: a term that is also missing on the target side is marked
  // inline instead of being listed twice (hits once, missing once).
  const missing = new Set(data.missingTerms.map(term => `${term.term}|${term.translation}`))
  const entries: { term: string; translation: string; line?: number; missing: boolean }[] = []
  const seen = new Set<string>()
  for (const hit of data.termHits) {
    const key = `${hit.term}|${hit.translation}`
    if (seen.has(key)) continue
    seen.add(key)
    entries.push({ term: hit.term, translation: hit.translation, line: hit.line, missing: missing.has(key) })
  }
  for (const term of data.missingTerms) {
    const key = `${term.term}|${term.translation}`
    if (seen.has(key)) continue
    seen.add(key)
    entries.push({ term: term.term, translation: term.translation, line: term.line, missing: true })
  }
  entries.sort((left, right) => Number(right.missing) - Number(left.missing))
  const label = data.directions.length === 2 ? 'both directions' : data.directions[0] === 'zh-to-en' ? 'zh→en' : 'en→zh'
  const hitCount = data.termHits.length
  const missingCount = data.missingTerms.length
  const lines = [`terminology (${label}: ${hitCount} ${hitCount === 1 ? 'hit' : 'hits'}${missingCount === 0 ? '' : `, ${missingCount} missing`}):`]
  for (const entry of entries.slice(0, MAX_ITEMS)) {
    lines.push(`  ${entry.term} → ${entry.translation}${entry.line === undefined ? '' : `   L${entry.line}`}${entry.missing ? '   [MISSING]' : ''}`)
  }
  if (entries.length > MAX_ITEMS) lines.push(`  ... (${entries.length - MAX_ITEMS} more)`)
  return lines
}

/** Render the two hint blocks. */
export function formatTranslationHints(report: HintsReport): string {
  if (report.mode === 'usage') return report.summary
  if (report.mode === 'term') {
    const search = report.termSearch
    if (search === undefined) return report.summary
    const lines = [`term: ${search.term}`]
    lines.push(`glossary: ${search.glossary === undefined ? 'not listed' : `${search.glossary.translation} (terminology.md L${search.glossary.line})`}`)
    lines.push(`en: ${search.en.length}`)
    for (const hit of search.en.slice(0, 10)) lines.push(`  ${hit.path}:${hit.line}  ${hit.text}`)
    lines.push(`zh: ${search.zh.length}`)
    for (const hit of search.zh.slice(0, 10)) lines.push(`  ${hit.path}:${hit.line}  ${hit.text}`)
    return lines.join('\n')
  }
  const data = report.data
  if (data === undefined) return report.summary
  const lines = [`${data.source}  ${data.state}  (en ${data.sectionCounts.en} / zh ${data.sectionCounts.zh} sections)`]
  if (data.state === 'ok') return lines.join('\n')
  lines.push(...renderChangedSections(data))
  lines.push(...renderTerminology(data))
  return lines.join('\n')
}

function searchCorpusTerm(root: string, term: string): HintsTermSearch {
  const search: HintsTermSearch = { term, en: [], zh: [] }
  const glossaryRows = glossary(root)
  const row = glossaryRows.find(item => item.en.toLowerCase() === term.toLowerCase())
  if (row !== undefined) search.glossary = { translation: row.zh, line: row.line }
  const listing = checkTranslationPairing(root, ['--list'])
  if (listing.exitCode === 2) throw new Error(listing.summary)
  for (const state of listing.states) {
    const paths = translationPairPaths(state.source)
    const en = readIfExists(root, paths.source)
    if (en !== undefined) {
      const pattern = termPattern(term)
      for (const [index, line] of en.split('\n').entries()) {
        pattern.lastIndex = 0
        if (pattern.test(line)) search.en.push({ path: paths.source, line: index + 1, text: snippet(line) })
      }
    }
    const zh = readIfExists(root, paths.zh)
    if (zh !== undefined) {
      const needle = term.toLowerCase()
      for (const [index, line] of zh.split('\n').entries()) {
        if (line.toLowerCase().includes(needle)) search.zh.push({ path: paths.zh, line: index + 1, text: snippet(line) })
      }
    }
  }
  return search
}

function usageReport(message: string, json: boolean): HintsReport {
  return { exitCode: 2, mode: 'usage', summary: `translation-hints: ${message}`, json }
}

/**
 * Collect one hints run.
 *
 * @param root - Absolute repository root.
 * @param argv - Command-line arguments after the script name.
 * @returns Structured result for the caller to print.
 */
export function collectTranslationHints(root: string, argv: string[]): HintsReport {
  if (argv.length === 1 && (argv[0] === '--help' || argv[0] === '-h')) {
    return { exitCode: 0, mode: 'usage', summary: USAGE, json: false }
  }
  let request: CliRequest
  try {
    request = parseCliArguments(argv)
  } catch (error) {
    return usageReport(errorMessage(error), argv.includes('--json'))
  }
  if (request.term !== undefined) {
    try {
      return { exitCode: 0, mode: 'term', summary: `translation-hints: term ${request.term}`, termSearch: searchCorpusTerm(root, request.term), json: request.json }
    } catch (error) {
      return usageReport(errorMessage(error), request.json)
    }
  }
  const anchor = pairAnchorOfArgument(request.anchor ?? '')
  let listing
  try {
    listing = checkTranslationPairing(root, ['--list'])
  } catch (error) {
    return usageReport(errorMessage(error), request.json)
  }
  if (listing.exitCode === 2) return usageReport(listing.summary, request.json)
  const state = listing.states.find(item => item.source === anchor)
    ?? listing.states.find(item => item.source.toLowerCase() === anchor.toLowerCase())
  if (state === undefined) return usageReport(`not an in-scope, non-excluded pair: ${anchor} (see .agents/se/contracts/i18n/README.md)`, request.json)
  const paths = translationPairPaths(state.source)
  const en = readIfExists(root, paths.source)
  const zh = readIfExists(root, paths.zh)
  const meta = readIfExists(root, paths.meta)
  if (en === undefined && zh === undefined) return usageReport(`none of the three pair files exists on disk: ${paths.source}`, request.json)
  try {
    const data = buildData(root, paths, en, zh, meta)
    const summary = `translation-hints: ${state.source} (${data.state})`
    return { exitCode: 0, mode: 'brief', summary, data, json: request.json }
  } catch (error) {
    return usageReport(errorMessage(error), request.json)
  }
}
