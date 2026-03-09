import type { HealthDto } from '../contracts/api'

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

export { API_BASE }

