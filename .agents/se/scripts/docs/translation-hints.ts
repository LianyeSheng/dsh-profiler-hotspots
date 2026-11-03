#!/usr/bin/env node
/**
 * CLI for the translation hints tool (read-only).
 *
 * Prints only changed sections and scoped terminology for a drifted pair.
 *
 * Usage:
 *   node .agents/se/scripts/docs/translation-hints.ts <one of the pair files | stem> [--json]
 *   node .agents/se/scripts/docs/translation-hints.ts --term <english term> [--json]
 *
 * The usage and output contract live in `translation-hints-report.ts`; this file
 * only prints the result and sets the exit code. Any of the three pair files, or the
 * suffix-less stem, names the pair; `--json` emits machine-readable data and
 * `--term <english term>` searches the whole corpus for precedents.
 */

import { resolve } from 'node:path'
import { collectTranslationHints, formatTranslationHints } from './translation-hints-report.ts'

const root = resolve(import.meta.dirname, '../../../..')
const report = collectTranslationHints(root, process.argv.slice(2))
if (report.mode === 'usage') {
  process.stdout.write(`${report.summary}\n`)
} else if (report.json) {
  const payload = report.mode === 'term' ? report.termSearch : report.data
  process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`)
} else {
  process.stdout.write(`${formatTranslationHints(report)}\n`)
}
process.exit(report.exitCode)
