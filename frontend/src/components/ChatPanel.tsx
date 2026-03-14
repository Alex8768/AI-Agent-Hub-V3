import React, { useState, useRef, useEffect } from 'react';
import { askAnswer, API_BASE } from '../lib/apiClient';
import type { AnswerResponseDto } from '../contracts/api';

interface ChatPanelProps {
  workspaceId: string;
  sessionId: string;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ workspaceId, sessionId }) => {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<AnswerResponseDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [streamEvents, setStreamEvents] = useState<string[]>([]);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Cleanup SSE on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    setAnswer(null);
    setStreamEvents([]);

    // Connect to SSE stream for this session
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    const es = new EventSource(`${API_BASE}/api/v1/stream/${sessionId}?once=0`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'thought') {
          setStreamEvents(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${data.data.content}`]);
        }
      } catch {
        // ignore non-JSON or keepalive
      }
    };

    es.onerror = () => {
      // will reconnect automatically, but we can show a warning
    };

    try {
      const resp = await askAnswer(
        { query: query.trim(), k: 8, graph_depth: 1, session_id: sessionId },
        { workspaceId }
      );
      setAnswer(resp);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
      // Close SSE after answer is complete (or keep open for future)
      // We can keep it open, but for simplicity close after answer
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <form onSubmit={handleSubmit} style={{ padding: '1rem', borderBottom: '1px solid #ccc' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            style={{ flex: 1, padding: '0.5rem' }}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Asking...' : 'Ask'}
          </button>
        </div>
        <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
          Workspace: {workspaceId} | Session: {sessionId}
        </div>
      </form>

      {error && (
        <div style={{ padding: '1rem', color: 'red' }}>
          Error: {error}
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {/* Streaming thoughts */}
        {streamEvents.length > 0 && (
          <div style={{ background: '#f5f5f5', padding: '0.5rem', borderRadius: '4px' }}>
            <h4>Agent thoughts</h4>
            <div style={{ maxHeight: '200px', overflow: 'auto', fontSize: '0.9rem' }}>
              {streamEvents.map((ev, idx) => (
                <div key={idx} style={{ marginBottom: '0.25rem' }}>{ev}</div>
              ))}
            </div>
          </div>
        )}

        {/* Answer */}
        {answer && (
          <div style={{ background: '#e3f2fd', padding: '1rem', borderRadius: '4px' }}>
            <h3>Answer</h3>
            <p style={{ whiteSpace: 'pre-wrap' }}>{answer.answer}</p>
            <div style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
              <strong>Confidence:</strong> {answer.confidence.toFixed(2)}
            </div>
            <button onClick={() => setShowDiagnostics(!showDiagnostics)} style={{ marginTop: '0.5rem' }}>
              {showDiagnostics ? 'Hide' : 'Show'} Diagnostics
            </button>
            {showDiagnostics && (
              <pre style={{ background: '#fff', padding: '0.5rem', marginTop: '0.5rem', overflow: 'auto' }}>
                {JSON.stringify(answer.diagnostics, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPanel;
