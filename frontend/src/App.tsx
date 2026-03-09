import './App.css'
import { useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import {
  API_BASE,
  askAnswer,
  deleteDocument,
  getHealth,
  listDocuments,
  searchDocuments,
  uploadDocument,
} from './lib/apiClient'
import type { AnswerResponseDto, DocumentItem, SearchResultDto } from './contracts/api'

const WORKSPACE_STORAGE_KEY = 'ai-agent-hub.workspace-id'
const SESSION_STORAGE_KEY = 'ai-agent-hub.session-id'

function normalizeContextId(raw: string, fallback: string): string {
  const next = raw.trim()
  return next.length > 0 ? next : fallback
}

function App() {
  const [healthStatus, setHealthStatus] = useState('checking')
  const [error, setError] = useState('')
  const [workspaceId, setWorkspaceId] = useState(() => localStorage.getItem(WORKSPACE_STORAGE_KEY) ?? 'default')
  const [sessionId, setSessionId] = useState(() => localStorage.getItem(SESSION_STORAGE_KEY) ?? 'default')
  const [workspaceDraft, setWorkspaceDraft] = useState(workspaceId)
  const [sessionDraft, setSessionDraft] = useState(sessionId)
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResultDto[]>([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<AnswerResponseDto | null>(null)
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [answerLoading, setAnswerLoading] = useState(false)

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
    localStorage.setItem(WORKSPACE_STORAGE_KEY, workspaceId)
  }, [workspaceId])

  useEffect(() => {
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId)
  }, [sessionId])

  useEffect(() => {
    let alive = true
    setDocumentsLoading(true)
    listDocuments({ workspaceId })
      .then((items) => {
        if (!alive) return
        setDocuments(items)
      })
      .catch((err: unknown) => {
        if (!alive) return
        setError(String(err))
      })
      .finally(() => {
        if (!alive) return
        setDocumentsLoading(false)
      })

    setSearchResults([])
    setAnswer(null)
    return () => {
      alive = false
    }
  }, [workspaceId])

  const onFileSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.files?.[0] ?? null
    setSelectedFile(next)
  }

  const onUpload = async (event: FormEvent) => {
    event.preventDefault()
    if (!selectedFile) return
    setDocumentsLoading(true)
    setError('')
    try {
      await uploadDocument(selectedFile, { workspaceId })
      setSelectedFile(null)
      const items = await listDocuments({ workspaceId })
      setDocuments(items)
    } catch (err: unknown) {
      setError(String(err))
    } finally {
      setDocumentsLoading(false)
    }
  }

  const onDelete = async (id: string) => {
    setDocumentsLoading(true)
    setError('')
    try {
      await deleteDocument(id, { workspaceId })
      setDocuments((prev) => prev.filter((item) => item.id !== id))
    } catch (err: unknown) {
      setError(String(err))
    } finally {
      setDocumentsLoading(false)
    }
  }

  const onSearch = async (event: FormEvent) => {
    event.preventDefault()
    if (!query.trim()) return
    setSearchLoading(true)
    setError('')
    try {
      const rows = await searchDocuments({ query: query.trim(), k: 5 }, { workspaceId })
      setSearchResults(rows)
    } catch (err: unknown) {
      setError(String(err))
    } finally {
      setSearchLoading(false)
    }
  }

  const onAsk = async (event: FormEvent) => {
    event.preventDefault()
    if (!question.trim()) return
    setAnswerLoading(true)
    setError('')
    try {
      const payload = await askAnswer(
        { query: question.trim(), k: 8, graph_depth: 1, session_id: sessionId },
        { workspaceId },
      )
      setAnswer(payload)
    } catch (err: unknown) {
      setError(String(err))
    } finally {
      setAnswerLoading(false)
    }
  }

  const onApplyContext = (event: FormEvent) => {
    event.preventDefault()
    const nextWorkspace = normalizeContextId(workspaceDraft, 'default')
    const nextSession = normalizeContextId(sessionDraft, 'default')
    setWorkspaceDraft(nextWorkspace)
    setSessionDraft(nextSession)
    setWorkspaceId(nextWorkspace)
    setSessionId(nextSession)
    setError('')
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
        <form className="context-grid" onSubmit={onApplyContext}>
          <label>
            <span className="label">Workspace ID</span>
            <input value={workspaceDraft} onChange={(event) => setWorkspaceDraft(event.target.value)} />
          </label>
          <label>
            <span className="label">Session ID</span>
            <input value={sessionDraft} onChange={(event) => setSessionDraft(event.target.value)} />
          </label>
          <button type="submit">Apply context</button>
        </form>
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
            <button type="submit" disabled={!selectedFile || documentsLoading}>
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
                <button type="button" onClick={() => void onDelete(item.id)} disabled={documentsLoading}>
                  Delete
                </button>
              </li>
            ))}
            {documentsLoading ? <li className="muted">Loading documents...</li> : null}
            {!documentsLoading && documents.length === 0 ? <li className="muted">No documents yet.</li> : null}
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
            <button type="submit" disabled={searchLoading || !query.trim()}>
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
            {searchLoading ? <li className="muted">Searching...</li> : null}
            {!searchLoading && searchResults.length === 0 ? <li className="muted">No search results yet.</li> : null}
          </ul>
        </article>
      </section>

      <section className="card">
        <h2>Answer + Diagnostics</h2>
        <form className="inline-form" onSubmit={onAsk}>
          <input
            type="text"
            value={question}
            placeholder="Ask a question"
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button type="submit" disabled={answerLoading || !question.trim()}>
            Ask
          </button>
        </form>
        {answerLoading ? <p className="muted">Generating answer...</p> : null}
        {answer && !answerLoading ? (
          <div className="answer-block">
            <p className="answer-text">{answer.answer}</p>
            <div className="meta-inline">
              <span>confidence: {answer.confidence.toFixed(2)}</span>
              <span>warnings: {answer.warnings.length}</span>
            </div>
            <details>
              <summary>Diagnostics JSON</summary>
              <pre>{JSON.stringify(answer.diagnostics, null, 2)}</pre>
            </details>
          </div>
        ) : (
          !answerLoading ? <p className="muted">No answer yet.</p> : null
        )}
      </section>
    </div>
  )
}

export default App
