import { useState, useEffect } from 'react';
import './App.css';
import AppLayout from './components/AppLayout';
import ChatTabs from './components/ChatTabs';
import RightPanel from './components/RightPanel';
import ChatPanel from './components/ChatPanel';
import GraphCanvas from './components/GraphCanvas';
import { AppProvider, useAppContext } from './context/AppContext';
import { getHealth } from './lib/apiClient';

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

function AppContent() {
  const [healthStatus, setHealthStatus] = useState('checking');
  const [leftVisible, setLeftVisible] = useState(() => readStoredBoolean('leftPanelVisible', true));
  const [rightVisible, setRightVisible] = useState(() => readStoredBoolean('rightPanelVisible', true));
  const [workspaceId, setWorkspaceId] = useState('default');
  const [sessionId, setSessionId] = useState('default');
  const { lastGraph } = useAppContext();

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
      <button onClick={() => setLeftVisible(false)} style={{ marginTop: '1rem' }}>Hide</button>
    </div>
  );

  const canvasContent = (
    <GraphCanvas nodes={lastGraph?.nodes} edges={lastGraph?.edges} />
  );

  const metaContent = (
    <div style={{ padding: '1rem' }}>
      <h2>Meta / Self-Evolution</h2>
      <p>Optimization proposals, gaps, etc.</p>
    </div>
  );

  const centerPanel = (
    <ChatTabs
      chatContent={<ChatPanel workspaceId={workspaceId} sessionId={sessionId} />}
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
