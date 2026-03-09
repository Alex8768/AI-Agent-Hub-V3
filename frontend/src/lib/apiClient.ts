import type {
  DeleteDocumentResponseDto,
  DocumentItem,
  HealthDto,
  SearchRequestDto,
  SearchResultDto,
} from '../contracts/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }
  return (await response.json()) as T
}

export async function getHealth(): Promise<HealthDto> {
  const response = await fetch(`${API_BASE}/health`, {
    headers: { Accept: 'application/json' },
  })
  return parseJson<HealthDto>(response)
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE}/api/v1/documents`, {
    headers: { Accept: 'application/json' },
  })
  return parseJson<DocumentItem[]>(response)
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const body = new FormData()
  body.append('file', file)
  const response = await fetch(`${API_BASE}/api/v1/documents/upload`, {
    method: 'POST',
    body,
  })
  return parseJson<DocumentItem>(response)
}

export async function deleteDocument(documentId: string): Promise<DeleteDocumentResponseDto> {
  const response = await fetch(`${API_BASE}/api/v1/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  })
  return parseJson<DeleteDocumentResponseDto>(response)
}

export async function searchDocuments(payload: SearchRequestDto): Promise<SearchResultDto[]> {
  const response = await fetch(`${API_BASE}/api/v1/search`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: payload.query,
      k: payload.k ?? 5,
      include_content: payload.include_content ?? false,
      include_metadata: payload.include_metadata ?? true,
    }),
  })
  return parseJson<SearchResultDto[]>(response)
}

export { API_BASE }

