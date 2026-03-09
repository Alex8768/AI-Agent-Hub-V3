import './App.css'
import { useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { API_BASE, deleteDocument, getHealth, listDocuments, searchDocuments, uploadDocument } from './lib/apiClient'
import type { DocumentItem, SearchResultDto } from './contracts/api'

function App() {
  const [healthStatus, setHealthStatus] = useState('checking')
  const [error, setError] = useState('')
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResultDto[]>([])
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let alive = true
    getHealth()
      .then((payload) => {
        if (!alive) return
        setHealthStatus(String(payload.status || 'unknown'))
      })
      .catch((err: unknown) => {
        if (!alive) return
        setHealthStatus('unreachable')
        setError(String(err))
      })
    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    let alive = true
    listDocuments()
      .then((items) => {
        if (!alive) return
        setDocuments(items)
      })
      .catch((err: unknown) => {
        if (!alive) return
        setError(String(err))
      })
    return () => {
      alive = false
    }
  }, [])

  const onFileSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.files?.[0] ?? null
    setSelectedFile(next)
  }

  const onUpload = async (event: FormEvent) => {
    event.preventDefault()
    if (!selectedFile) return
    setBusy(true)
    setError('')
    try {
      await uploadDocument(selectedFile)
      setSelectedFile(null)
      const items = await listDocuments()
      setDocuments(items)
    } catch (err: unknown) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  const onDelete = async (id: string) => {
    setBusy(true)
    setError('')
    try {
      await deleteDocument(id)
      setDocuments((prev) => prev.filter((item) => item.id !== id))
    } catch (err: unknown) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  const onSearch = async (event: FormEvent) => {
    event.preventDefault()
    if (!query.trim()) return
    setBusy(true)
    setError('')
    try {
      const rows = await searchDocuments({ query: query.trim(), k: 5 })
      setSearchResults(rows)
    } catch (err: unknown) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div>
          <h1>AI Agent Hub V3</h1>
          <p>Interface Foundation (MVP) - A2.28</p>
        </div>
        <div className="status-chip">
          <span>API:</span>
          <strong>{healthStatus}</strong>
        </div>
      </header>

      <section className="meta-panel">
        <div>
          <span className="label">Backend URL</span>
          <code>{API_BASE}</code>
        </div>
        {error ? (
          <div>
            <span className="label">Last error</span>
            <code>{error}</code>
          </div>
        ) : null}
      </section>

      <section className="grid two-columns">
        <article className="card">
          <h2>Documents</h2>
          <form className="inline-form" onSubmit={onUpload}>
            <input type="file" onChange={onFileSelected} />
            <button type="submit" disabled={!selectedFile || busy}>
              Upload
            </button>
          </form>
          <ul className="list">
            {documents.map((item) => (
              <li key={item.id} className="list-row">
                <div>
                  <strong>{item.filename}</strong>
                  <p>{item.status}</p>
                </div>
                <button type="button" onClick={() => void onDelete(item.id)} disabled={busy}>
                  Delete
                </button>
              </li>
            ))}
            {documents.length === 0 ? <li className="muted">No documents yet.</li> : null}
          </ul>
        </article>

        <article className="card">
          <h2>Search</h2>
          <form className="inline-form" onSubmit={onSearch}>
            <input
              type="text"
              value={query}
              placeholder="Search query"
              onChange={(event) => setQuery(event.target.value)}
            />
            <button type="submit" disabled={busy || !query.trim()}>
              Search
            </button>
          </form>
          <ul className="list">
            {searchResults.map((row) => (
              <li key={row.chunk_id} className="list-row">
                <div>
                  <strong>{row.source_document ?? row.document_id}</strong>
                  <p>{row.snippet}</p>
                </div>
              </li>
            ))}
            {searchResults.length === 0 ? <li className="muted">No search results yet.</li> : null}
          </ul>
        </article>
      </section>
    </div>
  )
}

export default App
