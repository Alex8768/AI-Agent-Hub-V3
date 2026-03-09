import './App.css'
import { useEffect, useMemo, useState } from 'react'
import { API_BASE, getHealth } from './lib/apiClient'

function App() {
  const [healthStatus, setHealthStatus] = useState('checking')
  const [error, setError] = useState('')

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

  const cards = useMemo(
    () => [
      {
        title: 'Documents',
        text: 'Upload/list/delete flows will be connected in next patch.',
      },
      {
        title: 'Search',
        text: 'Vector and hybrid search UX wiring planned in A2.28.',
      },
      {
        title: 'Answer + Diagnostics',
        text: 'Reasoning answer panel and diagnostics explorer planned in A2.28.',
      },
    ],
    [],
  )

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

      <div className="grid">
        {cards.map((card) => (
          <article key={card.title} className="card">
            <h2>{card.title}</h2>
            <p>{card.text}</p>
          </article>
        ))}
      </div>
    </div>
  )
}

export default App
