import { useState, useEffect } from 'react';
import './App.css';
import AppLayout from './components/AppLayout';
import ChatTabs from './components/ChatTabs';
import RightPanel from './components/RightPanel';
import { getHealth } from './lib/apiClient';

function App() {
  const [healthStatus, setHealthStatus] = useState('checking');
  const [leftVisible, setLeftVisible] = useState(() => {
    const saved = localStorage.getItem('leftPanelVisible');
    return saved !== null ? JSON.parse(saved) : true;
  });
  const [rightVisible, setRightVisible] = useState(() => {
    const saved = localStorage.getItem('rightPanelVisible');
    return saved !== null ? JSON.parse(saved) : true;
  });
  const [workspaceId, setWorkspaceId] = useState('default');
  const [sessionId, setSessionId] = useState('default');

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
        <label>Workspace:</label>
        <input 
          type="text" 
          value={workspaceId} 
          onChange={(e) => setWorkspaceId(e.target.value)}
          style={{ marginLeft: '0.5rem' }}
        />
      </div>
      <div style={{ marginTop: '0.5rem' }}>
        <label>Session:</label>
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

  const chatContent = (
    <div>
      <h2>Chat</h2>
      <p>Question form will be here</p>
      <p>Answer area with streaming</p>
    </div>
  );

  const canvasContent = (
    <div>
      <h2>Canvas</h2>
      <p>Graph visualization placeholder</p>
    </div>
  );

  const metaContent = (
    <div>
      <h2>Meta / Self-Evolution</h2>
      <p>Optimization proposals, gaps, etc.</p>
    </div>
  );

  const centerPanel = (
    <ChatTabs chatContent={chatContent} canvasContent={canvasContent} metaContent={metaContent} />
  );

  return (
    <div>
      <div style={{ padding: '0.5rem 1rem', borderBottom: '1px solid #ccc', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <span>API Status: {healthStatus}</span>
        <button onClick={() => setLeftVisible(!leftVisible)}>Toggle Left</button>
        <button onClick={() => setRightVisible(!rightVisible)}>Toggle Right</button>
      </div>
      <AppLayout
        leftPanel={leftPanel}
        centerPanel={centerPanel}
        rightPanel={<RightPanel workspaceId={workspaceId} />}
        leftVisible={leftVisible}
        rightVisible={rightVisible}
      />
    </div>
  );
}

export default App;
