#!/usr/bin/env node
/**
 * 中英文档配对门禁 CLI。
 *
 * 用法、规则与记录格式由 `.agents/se/contracts/i18n/README.md` 定义；检查逻辑在
 * `translation-pairing-check.ts`，本文件只负责打印结果与设置退出码。
 */

import { resolve } from 'node:path'
import { checkTranslationPairing, formatPairingReport } from './translation-pairing-check.ts'

const root = resolve(import.meta.dirname, '../../../..')
const report = checkTranslationPairing(root, process.argv.slice(2))
process.stdout.write(`${formatPairingReport(report)}\n`)
process.exit(report.exitCode)
