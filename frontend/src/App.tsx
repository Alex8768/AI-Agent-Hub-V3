import { useEffect, useMemo, useState } from 'react';
import './App.css';
import AppLayout from './components/AppLayout';
import ChatTabs from './components/ChatTabs';
import RightPanel from './components/RightPanel';
import ChatPanel from './components/ChatPanel';
import GraphCanvas from './components/GraphCanvas';
import MetaPanel from './components/MetaPanel';
import { AppProvider, useAppContext } from './context/AppContext';
import { getHealth } from './lib/apiClient';

type HealthState = 'checking' | 'healthy' | 'unreachable';

function AppContent() {
  const [healthStatus, setHealthStatus] = useState<HealthState>('checking');
  const [leftVisible, setLeftVisible] = useState(false);
  const [rightVisible, setRightVisible] = useState(false);
  const [workspaceId, setWorkspaceId] = useState('default');
  const [sessionId, setSessionId] = useState('default');
  const [lastUsedSession, setLastUsedSession] = useState('No requests yet');

  const { lastGraph, lastAnswer } = useAppContext();

  useEffect(() => {
    getHealth()
      .then(() => setHealthStatus('healthy'))
      .catch(() => setHealthStatus('unreachable'));
  }, []);

  const onSessionUsed = (ws: string, sid: string) => {
    const normalizedWorkspace = ws.trim() || 'default';
    const normalizedSession = sid.trim() || 'default';
    setLastUsedSession(`${normalizedWorkspace}:${normalizedSession}`);
  };

  const healthLabel = useMemo(() => {
    if (healthStatus === 'healthy') return 'Healthy';
    if (healthStatus === 'unreachable') return 'Unreachable';
    return 'Checking';
  }, [healthStatus]);

  const leftPanel = (
    <div className="panel-body shell-sidebar">
      <div className="sidebar-section">
        <div className="sidebar-eyebrow">Agent Workspace</div>
        <h2 className="sidebar-title">Session Context</h2>
        <p className="sidebar-copy">
          Scope the chat, graph and tool activity to a specific workspace/session pair.
        </p>
      </div>

      <div className="sidebar-section">
        <label className="field-label" htmlFor="workspace-input">
          Workspace
        </label>
        <input
          id="workspace-input"
          className="field-input"
          value={workspaceId}
          onChange={(e) => setWorkspaceId(e.target.value)}
          placeholder="default"
        />

        <label className="field-label" htmlFor="session-input">
          Session
        </label>
        <input
          id="session-input"
          className="field-input"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="default"
        />
      </div>

      <div className="sidebar-section sidebar-info-card">
        <div className="section-title">Current Scope</div>
        <div className="scope-grid">
          <div className="scope-item">
            <span className="scope-key">Workspace</span>
            <strong>{workspaceId.trim() || 'default'}</strong>
          </div>
          <div className="scope-item">
            <span className="scope-key">Session</span>
            <strong>{sessionId.trim() || 'default'}</strong>
          </div>
        </div>
      </div>

      <div className="sidebar-section sidebar-info-card">
        <div className="section-title">Last Active Channel</div>
        <div className="sidebar-copy sidebar-copy-tight">{lastUsedSession}</div>
      </div>
    </div>
  );

  return (
    <div className="app-root">
      <main className="app-content">
        <AppLayout
          leftVisible={leftVisible}
          rightVisible={rightVisible}
          onToggleLeft={() => setLeftVisible((v) => !v)}
          onToggleRight={() => setRightVisible((v) => !v)}
          leftPanel={leftPanel}
          centerPanel={
            <ChatTabs
              chatContent={
                <ChatPanel
                  workspaceId={workspaceId}
                  sessionId={sessionId}
                  onSessionUsed={onSessionUsed}
                />
              }
              canvasContent={<GraphCanvas nodes={lastGraph?.nodes} edges={lastGraph?.edges} />}
              metaContent={<MetaPanel diagnostics={lastAnswer?.diagnostics || null} />}
            />
          }
          rightPanel={<RightPanel workspaceId={workspaceId} />}
        />
      </main>

      <footer className="status-bar">
        <div className="status-section">
          <div className="status-indicator">
            Scope: {(workspaceId.trim() || 'default')} / {(sessionId.trim() || 'default')}
          </div>
        </div>

        <div className="status-section">
          <div className={`status-indicator ${healthStatus}`}>
            ● {healthLabel}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
