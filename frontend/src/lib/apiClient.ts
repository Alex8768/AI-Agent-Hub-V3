import type {
  AnswerRequestDto,
  AnswerResponseDto,
  DeleteDocumentResponseDto,
  DocumentItem,
  HealthDto,
  SearchRequestDto,
  SearchResultDto,
  ToolDiscoveryDto,
  ToolInvokeResponseDto,
} from '../contracts/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface RequestContext {
  workspaceId?: string
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return (await response.json()) as T
}

function buildWorkspaceHeaders(workspaceId?: string): Record<string, string> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const normalized = (workspaceId ?? '').trim()
  if (normalized.length > 0) {
    headers['X-Workspace-Id'] = normalized
  }
  return headers
}

export async function getHealth(): Promise<HealthDto> {
  const response = await fetch(`${API_BASE}/health`, {
    headers: { Accept: 'application/json' },
  })
  return parseJson<HealthDto>(response)
}

export async function listDocuments(ctx: RequestContext = {}): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE}/api/v1/documents`, {
    headers: buildWorkspaceHeaders(ctx.workspaceId),
  })
  return parseJson<DocumentItem[]>(response)
}

export async function uploadDocument(file: File, ctx: RequestContext = {}): Promise<DocumentItem> {
  const body = new FormData()
  body.append('file', file)
  const response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
    method: 'POST',
    headers: buildWorkspaceHeaders(ctx.workspaceId),
    body,
  })
  return parseJson<DocumentItem>(response)
}

export async function deleteDocument(documentId: string, ctx: RequestContext = {}): Promise<DeleteDocumentResponseDto> {
  const response = await fetch(`${API_BASE}/api/v1/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
    headers: buildWorkspaceHeaders(ctx.workspaceId),
  })
  return parseJson<DeleteDocumentResponseDto>(response)
}

export async function searchDocuments(payload: SearchRequestDto, ctx: RequestContext = {}): Promise<SearchResultDto[]> {
  const headers = buildWorkspaceHeaders(ctx.workspaceId)
  headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE}/api/v1/search`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      query: payload.query,
      k: payload.k ?? 5,
      include_content: payload.include_content ?? false,
      include_metadata: payload.include_metadata ?? true,
    }),
  })
  return parseJson<SearchResultDto[]>(response)
}

export async function askAnswer(payload: AnswerRequestDto, ctx: RequestContext = {}): Promise<AnswerResponseDto> {
  const headers = buildWorkspaceHeaders(ctx.workspaceId)
  headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE}/api/v1/answer`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      query: payload.query,
      k: payload.k ?? 8,
      graph_depth: payload.graph_depth ?? 1,
      session_id: payload.session_id ?? 'default',
    }),
  })
  return parseJson<AnswerResponseDto>(response)
}

export async function listTools(ctx: RequestContext = {}): Promise<ToolDiscoveryDto> {
  const response = await fetch(`${API_BASE}/api/v1/tools`, {
    headers: buildWorkspaceHeaders(ctx.workspaceId),
  })
  return parseJson<ToolDiscoveryDto>(response)
}

export async function invokeTool(
  toolName: string,
  argumentsPayload: Record<string, unknown>,
  ctx: RequestContext = {},
): Promise<ToolInvokeResponseDto> {
  const headers = buildWorkspaceHeaders(ctx.workspaceId)
  headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE}/api/v1/tools/${encodeURIComponent(toolName)}/invoke`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ arguments: argumentsPayload }),
  })
  return parseJson<ToolInvokeResponseDto>(response)
}

export { API_BASE }

