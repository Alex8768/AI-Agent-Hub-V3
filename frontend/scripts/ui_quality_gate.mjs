import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function assertIncludes(label, source, needles) {
  const missing = needles.filter((needle) => !source.includes(needle))
  if (missing.length > 0) {
    throw new Error(`${label} is missing required markers: ${missing.join(', ')}`)
  }
}

function run() {
  const contracts = readFileSync(resolve('src/contracts/api.ts'), 'utf-8')
  const client = readFileSync(resolve('src/lib/apiClient.ts'), 'utf-8')
  const app = readFileSync(resolve('src/App.tsx'), 'utf-8')

  assertIncludes('contracts', contracts, [
    'export interface DocumentItem',
    'export interface SearchResultDto',
    'export interface AnswerRequestDto',
    'session_id?: string',
    'export interface AnswerResponseDto',
    'diagnostics: Record<string, unknown>',
    'warnings: string[]',
  ])

  assertIncludes('api client', client, [
    "X-Workspace-Id",
    '/api/v1/documents',
    '/api/v1/search',
    '/api/v1/answer',
    'session_id: payload.session_id ?? \'default\'',
  ])

  assertIncludes('app shell', app, [
    'Documents',
    'Search',
    'Answer + Diagnostics',
    'Workspace ID',
    'Session ID',
    'Diagnostics JSON',
  ])

  process.stdout.write('UI quality gate passed.\n')
}

run()
