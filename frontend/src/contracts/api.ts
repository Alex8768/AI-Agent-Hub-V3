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
  query: string
  k?: number
  graph_depth?: number
  session_id?: string
}

export interface AnswerResponseDto {
  answer: string
  confidence: number
  context_preview: string
  provenance: Array<Record<string, unknown>>
  used_chunks: string[]
  used_nodes: string[]
  used_edges: string[]
  request_id: string
  workspace_id: string
  timings: Record<string, number>
  warnings: string[]
  diagnostics: Record<string, unknown>
}

export interface HealthDto {
  status: string
  service?: string
  version?: string
}

export interface DeleteDocumentResponseDto {
  status: string
  document_id: string
}

