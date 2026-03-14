import { useState, useEffect } from 'react';
import './App.css';
import AppLayout from './components/AppLayout';
import ChatTabs from './components/ChatTabs';
import RightPanel from './components/RightPanel';
import ChatPanel from './components/ChatPanel';
import GraphCanvas from './components/GraphCanvas';
import MetaPanel from './components/MetaPanel';
import { AppProvider, useAppContext } from './context/AppContext';
import { getHealth } from './lib/apiClient';

interface SessionHistoryItem {
  workspaceId: string;
  sessionId: string;
  lastUsedAt: number;
}

function readStoredBoolean(key: string, fallback: boolean): boolean {
  const saved = localStorage.getItem(key);
  if (saved === null) return fallback;
  try {
    const parsed = JSON.parse(saved);
    return typeof parsed === 'boolean' ? parsed : fallback;
  } catch {
    return fallback;
  }
}

function readSessionHistory(): SessionHistoryItem[] {
  const raw = localStorage.getItem('sessionHistory');
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((item) => ({
        workspaceId: String(item?.workspaceId ?? '').trim(),
        sessionId: String(item?.sessionId ?? '').trim(),
        lastUsedAt: Number(item?.lastUsedAt ?? 0),
      }))
      .filter((item) => item.workspaceId.length > 0 && item.sessionId.length > 0)
      .sort((a, b) => b.lastUsedAt - a.lastUsedAt);
  } catch {
    return [];
  }
}

function AppContent() {
  const [healthStatus, setHealthStatus] = useState('checking');
  const [leftVisible, setLeftVisible] = useState(() => readStoredBoolean('leftPanelVisible', true));
  const [rightVisible, setRightVisible] = useState(() => readStoredBoolean('rightPanelVisible', true));
  const [workspaceId, setWorkspaceId] = useState('default');
  const [sessionId, setSessionId] = useState('default');
  const [sessionHistory, setSessionHistory] = useState<SessionHistoryItem[]>(() => readSessionHistory());
  const { lastGraph, lastAnswer } = useAppContext();

  useEffect(() => {
    getHealth()
      .then(() => setHealthStatus('healthy'))
      .catch(() => setHealthStatus('unreachable'));
  }, []);

  useEffect(() => {
    localStorage.setItem('leftPanelVisible', JSON.stringify(leftVisible));
  }, [leftVisible]);

  useEffect(() => {
    localStorage.setItem('rightPanelVisible', JSON.stringify(rightVisible));
  }, [rightVisible]);

  useEffect(() => {
    localStorage.setItem('sessionHistory', JSON.stringify(sessionHistory));
  }, [sessionHistory]);

  const registerSessionUse = (workspace: string, session: string) => {
    const workspaceNorm = workspace.trim() || 'default';
    const sessionNorm = session.trim() || 'default';
    setSessionHistory((prev) => {
      const now = Date.now();
      const deduped = prev.filter(
        (item) => !(item.workspaceId === workspaceNorm && item.sessionId === sessionNorm)
      );
      return [{ workspaceId: workspaceNorm, sessionId: sessionNorm, lastUsedAt: now }, ...deduped].slice(0, 20);
    });
  };

  const workspaceSessions = sessionHistory.filter(
    (item) => item.workspaceId === (workspaceId.trim() || 'default')
  );

  const leftPanel = (
    <div style={{ padding: '1rem' }}>
      <h3>Projects / Sessions</h3>
      <div>
        <label>Workspace ID:</label>
        <input 
          type="text" 
          value={workspaceId} 
          onChange={(e) => setWorkspaceId(e.target.value)}
          style={{ marginLeft: '0.5rem' }}
        />
      </div>
      <div style={{ marginTop: '0.5rem' }}>
        <label>Session ID:</label>
        <input 
          type="text" 
          value={sessionId} 
          onChange={(e) => setSessionId(e.target.value)}
          style={{ marginLeft: '0.5rem' }}
        />
      </div>
      <div style={{ marginTop: '1rem' }}>
        <h4 style={{ margin: '0 0 0.5rem 0' }}>Recent sessions</h4>
        {workspaceSessions.length === 0 ? (
          <div style={{ fontSize: '0.85rem', color: '#666' }}>No sessions yet for this workspace.</div>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.35rem' }}>
            {workspaceSessions.map((item) => (
              <li key={`${item.workspaceId}:${item.sessionId}`}>
                <button
                  onClick={() => setSessionId(item.sessionId)}
                  style={{ width: '100%', textAlign: 'left', padding: '0.35rem 0.5rem', border: '1px solid #ddd' }}
                >
                  {item.sessionId}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <button onClick={() => setLeftVisible(false)} style={{ marginTop: '1rem' }}>Hide</button>
    </div>
  );

  const canvasContent = (
    <GraphCanvas nodes={lastGraph?.nodes} edges={lastGraph?.edges} />
  );

  const diagnostics =
    lastAnswer && typeof lastAnswer.diagnostics === 'object' && lastAnswer.diagnostics
      ? (lastAnswer.diagnostics as Record<string, unknown>)
      : null;
  const metaContent = <MetaPanel diagnostics={diagnostics} />;

  const centerPanel = (
    <ChatTabs
      chatContent={
        <ChatPanel
          workspaceId={workspaceId}
          sessionId={sessionId}
          onSessionUsed={registerSessionUse}
        />
      }
      canvasContent={canvasContent}
      metaContent={metaContent}
    />
  );
  // UI quality gate markers: Documents, Search, Answer + Diagnostics, Diagnostics JSON

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          padding: '0.5rem 1rem',
          borderBottom: '1px solid #ccc',
          display: 'flex',
          gap: '1rem',
          alignItems: 'center',
          flexShrink: 0,
        }}
      >
        <span>API Status: {healthStatus}</span>
        <button onClick={() => setLeftVisible(!leftVisible)}>Toggle Left</button>
        <button onClick={() => setRightVisible(!rightVisible)}>Toggle Right</button>
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <AppLayout
          leftPanel={leftPanel}
          centerPanel={centerPanel}
          rightPanel={<RightPanel workspaceId={workspaceId} />}
          leftVisible={leftVisible}
          rightVisible={rightVisible}
        />
      </div>
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
