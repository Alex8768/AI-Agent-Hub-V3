export interface DocumentItem {
  id: string
  filename: string
  size_bytes: number
  status: string
  workspace_id: string
  metadata: Record<string, unknown>
}

export interface SearchRequestDto {
  query: string
  k?: number
  include_content?: boolean
  include_metadata?: boolean
}

export interface SearchResultDto {
  document_id: string
  chunk_id: string
  score: number
  snippet: string
  content?: string | null
  source_document?: string | null
  metadata: Record<string, unknown>
}

export interface AnswerRequestDto {
  question: string
  top_k?: number
}

export interface AnswerResponseDto {
  answer: string
  sources: Array<Record<string, unknown>>
  diagnostics: Record<string, unknown>
}

export interface HealthDto {
  status: string
  service?: string
  version?: string
}

