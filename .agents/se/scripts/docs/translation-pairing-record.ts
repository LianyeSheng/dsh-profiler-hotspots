/**
 * Paths, section hashes, parsing, and rendering for bilingual consistency records.
 *
 * Records split a document into sections keyed by the English heading slug path: edits to
 * independent sections land on different record lines, which Git's default text merge can
 * combine; only edits to the same section on both sides conflict.
 */

import { createHash } from 'node:crypto'
import type { MarkdownHeading } from './translation-links.ts'
import {
  detectLanguageSwitcher,
  normalizePairedLinkTargets,
  scanMarkdown,
} from './translation-links.ts'
import type { TranslationPairPaths } from './translation-pairing.ts'

/** Hashes of one section's content on both sides. */
export interface TranslationSectionHashes {
  en: string
  zh: string
}

/** English heading slug path → section hashes on both sides, in document order. */
export type TranslationPairingRecord = ReadonlyMap<string, TranslationSectionHashes>

/** Link-resolution context needed to compute a record. */
export interface TranslationPairingRecordContext {
  /** Whether the path is an in-scope paired-document English anchor. */
  isPairSource: (source: string) => boolean
}

/** One divergence between the record and current content. */
export interface TranslationPairingRecordDiff {
  key: string
  kind: 'changed' | 'unconfirmed' | 'stale'
  /** The side(s) that changed, for `changed`. */
  sides: ('en' | 'zh')[]
}

const KEY_LINE = /^(\/.*):$/
const HASH_LINE = /^ {2}(en|zh): ([0-9a-f]{16})$/

/** One section of one side, split by headings. */
interface RawSection {
  heading?: MarkdownHeading
  lines: string[]
  /** 1-based start line of the section; the leading part starts at 1. */
  line: number
}

/**
 * Split one side into a leading part plus one section per heading; fenced code blocks and
 * the language-switcher line are excluded as a whole.
 *
 * The switcher target legitimately differs between a pair's source layout and its rendered
 * installed copy, so leaving it in the hash would make the same pair hash differently at the
 * two locations. Fenced code is already required byte-identical by P4, so it is excluded too.
 *
 * @param normalized - One side's text with paired link targets normalized.
 * @returns Section list (heading line included, leading/trailing blank lines trimmed)
 *   with each section's start line.
 */
function rawSections(normalized: string): RawSection[] {
  const scan = scanMarkdown(normalized)
  const switcherLine = detectLanguageSwitcher(scan)?.lineIndex
  const lines = normalized.split('\n')
  const headingAt = new Map(scan.headings.map(heading => [heading.lineIndex, heading]))
  const result: RawSection[] = [{ lines: [], line: 1 }]
  for (let index = 0; index < lines.length; index++) {
    if (scan.fenced[index] === true || index === switcherLine) continue
    const heading = headingAt.get(index)
    if (heading !== undefined) {
      result.push({ heading, lines: [lines[index] ?? ''], line: index + 1 })
      continue
    }
    result.at(-1)?.lines.push(lines[index] ?? '')
  }
  for (const section of result) {
    while (section.lines.length > 0 && (section.lines.at(-1) ?? '').trim() === '') section.lines.pop()
    while (section.lines.length > 0 && (section.lines[0] ?? '').trim() === '') section.lines.shift()
  }
  return result
}

/**
 * Build record keys for sections from the English heading slug path.
 *
 * @param sections - Section list of one side.
 * @returns Keys of the same length as the input, in document order.
 */
function sectionKeys(sections: RawSection[]): string[] {
  const ancestors: { depth: number; slug: string }[] = []
  const keys = new Set<string>()
  return sections.map(section => {
    let path = '/'
    if (section.heading !== undefined) {
      const depth = section.heading.depth
      while ((ancestors.at(-1)?.depth ?? 0) >= depth) ancestors.pop()
      ancestors.push({ depth, slug: slug(section.heading.text) })
      path = `/${ancestors.map(ancestor => ancestor.slug).join('/')}`
    }
    let key = path
    for (let repeat = 2; keys.has(key); repeat++) key = `${path}~${repeat}`
    keys.add(key)
    return key
  })
}

function slug(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'section'
}

function sectionHash(lines: string[]): string {
  return createHash('sha256').update(lines.join('\n')).digest('hex').slice(0, 16)
}

/**
 * Compute the consistency record for a pair's current content.
 *
 * Both sides are split by heading; section i pairs with section i. Keys use the English
 * heading slug path, with `~2`, `~3` appended to duplicate paths. Hashes cover lines
 * outside fenced code blocks within a section; paired-document link targets are replaced
 * with a locale-neutral marker first; sections empty on both sides produce no entry.
 *
 * @param paths - The three pair paths.
 * @param en - English source text.
 * @param zh - Chinese counterpart text.
 * @param context - Paired-document scope predicate.
 * @returns Record in document order.
 * @throws Error When the two sides have different section counts or a fence is unclosed.
 */
export function computeTranslationPairingRecord(
  paths: TranslationPairPaths,
  en: string,
  zh: string,
  context: TranslationPairingRecordContext,
): TranslationPairingRecord {
  const normalizedEn = normalizePairedLinkTargets(en, scanMarkdown(en), { ...context, sourcePath: paths.source })
  const normalizedZh = normalizePairedLinkTargets(zh, scanMarkdown(zh), { ...context, sourcePath: paths.zh })
  const enSections = rawSections(normalizedEn)
  const zhSections = rawSections(normalizedZh)
  if (enSections.length !== zhSections.length) {
    throw new Error(`${paths.source} 有 ${enSections.length - 1} 个标题节，${paths.zh} 有 ${zhSections.length - 1} 个`)
  }
  const keys = sectionKeys(enSections)
  const record = new Map<string, TranslationSectionHashes>()
  for (const [index, enSection] of enSections.entries()) {
    const zhSection = zhSections[index]
    if (zhSection === undefined) throw new Error('小节对齐丢失了对侧')
    if (enSection.lines.length === 0 && zhSection.lines.length === 0) continue
    record.set(keys[index] ?? '/', { en: sectionHash(enSection.lines), zh: sectionHash(zhSection.lines) })
  }
  return record
}

/** One section of one side; a Chinese-side key is only for order alignment, not a record key. */
export interface TranslationSectionEntry {
  /** Slug path of that side's heading; when called on the English side this is the record key. */
  key: string
  /** 1-based line of the section heading (or of the leading part). */
  line: number
  /** Content hash produced by the same algorithm as the consistency record. */
  hash: string
  /** No content outside fenced code blocks. */
  empty: boolean
}

/**
 * Compute one side's section list and hashes without requiring the counterpart.
 *
 * @param content - One side's text.
 * @param sourcePath - Repository-relative path of that side (for paired-link normalization).
 * @param context - Paired-document scope predicate.
 * @returns Sections in document order.
 */
export function translationSideSections(
  content: string,
  sourcePath: string,
  context: TranslationPairingRecordContext,
): TranslationSectionEntry[] {
  const normalized = normalizePairedLinkTargets(content, scanMarkdown(content), { ...context, sourcePath })
  const sections = rawSections(normalized)
  const keys = sectionKeys(sections)
  return sections.map((section, index) => ({
    key: keys[index] ?? '/',
    line: section.line,
    hash: sectionHash(section.lines),
    empty: section.lines.length === 0,
  }))
}

/**
 * Parse a consistency record.
 *
 * @param content - Full record file text.
 * @returns Record in file order; undefined when the format is invalid or a key repeats.
 */
export function parseTranslationPairingRecord(content: string): TranslationPairingRecord | undefined {
  const record = new Map<string, TranslationSectionHashes>()
  const lines = content.split('\n').filter(line => line !== '' && !line.startsWith('#'))
  for (let index = 0; index < lines.length; index += 3) {
    const key = KEY_LINE.exec(lines[index] ?? '')?.[1]
    const en = HASH_LINE.exec(lines[index + 1] ?? '')
    const zh = HASH_LINE.exec(lines[index + 2] ?? '')
    if (key === undefined || record.has(key) || en?.[1] !== 'en' || zh?.[1] !== 'zh' || en[2] === undefined || zh[2] === undefined) {
      return undefined
    }
    record.set(key, { en: en[2], zh: zh[2] })
  }
  return record
}

/**
 * Render the canonical text of a consistency record.
 *
 * The text names no pair path: the same bytes are valid beside the pair's source and beside
 * its installed copy, and the re-record command is fixed to the installed CLI.
 *
 * @param record - Confirmed section hashes.
 * @returns Canonical text ending with exactly one newline.
 */
export function renderTranslationPairingRecord(
  record: TranslationPairingRecord,
): string {
  return [
    '# Bilingual-pair consistency record (sections keyed by the English heading slug path):',
    '# one entry per heading section, hashing each side\'s lines outside fenced code',
    '# blocks and excluding the language-switcher line, with paired-document link',
    '# targets normalized to a locale-neutral form. The header names no path, so the',
    '# same record is valid beside a pair\'s source and beside its installed copy.',
    '# After editing either side, re-record the pair:',
    '#   node .agents/se/scripts/docs/verify-translation-pairing.ts --write <pair>',
    ...[...record].flatMap(([key, hashes]) => [`${key}:`, `  en: ${hashes.en}`, `  zh: ${hashes.zh}`]),
    '',
  ].join('\n')
}

/**
 * Compare a confirmed record with the record of the current content.
 *
 * @param recorded - Confirmed record.
 * @param current - Record computed from current content.
 * @returns One item per change, in current-record order followed by stale keys.
 */
export function translationPairingRecordDiff(
  recorded: TranslationPairingRecord,
  current: TranslationPairingRecord,
): TranslationPairingRecordDiff[] {
  const out: TranslationPairingRecordDiff[] = []
  for (const [key, hashes] of current) {
    const confirmed = recorded.get(key)
    if (confirmed === undefined) {
      out.push({ key, kind: 'unconfirmed', sides: [] })
      continue
    }
    const sides = (['en', 'zh'] as const).filter(side => confirmed[side] !== hashes[side])
    if (sides.length > 0) out.push({ key, kind: 'changed', sides: [...sides] })
  }
  for (const key of recorded.keys()) {
    if (!current.has(key)) out.push({ key, kind: 'stale', sides: [] })
  }
  return out
}
