import React, { useState, useEffect } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { listDocuments, uploadDocument, deleteDocument, API_BASE } from '../lib/apiClient';
import type { DocumentItem } from '../contracts/api';

interface RightPanelProps {
  workspaceId: string;
}

const RightPanel: React.FC<RightPanelProps> = ({ workspaceId }) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [tools, setTools] = useState<any[]>([]);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load documents on mount and workspace change
  useEffect(() => {
    let alive = true;
    setDocumentsLoading(true);
    listDocuments({ workspaceId })
      .then(items => {
        if (alive) setDocuments(items);
      })
      .catch(err => setError(String(err)))
      .finally(() => {
        if (alive) setDocumentsLoading(false);
      });
    return () => { alive = false; };
  }, [workspaceId]);

  // Load tools on mount
  useEffect(() => {
    let alive = true;
    setToolsLoading(true);
    fetch(`${API_BASE}/api/v1/tools`)
      .then(res => res.json())
      .then(data => {
        if (alive) setTools(data.tools || []);
      })
      .catch(err => setError(String(err)))
      .finally(() => {
        if (alive) setToolsLoading(false);
      });
    return () => { alive = false; };
  }, []);

  const onFileSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(event.target.files?.[0] ?? null);
  };

  const onUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFile) return;
    setDocumentsLoading(true);
    setError('');
    try {
      await uploadDocument(selectedFile, { workspaceId });
      setSelectedFile(null);
      const items = await listDocuments({ workspaceId });
      setDocuments(items);
    } catch (err) {
      setError(String(err));
    } finally {
      setDocumentsLoading(false);
    }
  };

  const onDelete = async (id: string) => {
    setDocumentsLoading(true);
    setError('');
    try {
      await deleteDocument(id, { workspaceId });
      setDocuments(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      setError(String(err));
    } finally {
      setDocumentsLoading(false);
    }
  };

  return (
    <Tabs.Root defaultValue="files" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Tabs.List style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #ccc', padding: '0 1rem' }}>
        <Tabs.Trigger value="files" style={{ padding: '0.5rem 0', border: 'none', background: 'none', cursor: 'pointer' }}>Files</Tabs.Trigger>
        <Tabs.Trigger value="tools" style={{ padding: '0.5rem 0', border: 'none', background: 'none', cursor: 'pointer' }}>Tools</Tabs.Trigger>
      </Tabs.List>

      <Tabs.Content value="files" style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
        <h3>Documents</h3>
        <form onSubmit={onUpload} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <input type="file" onChange={onFileSelected} />
          <button type="submit" disabled={!selectedFile || documentsLoading}>
            Upload
          </button>
        </form>
        {error && <div style={{ color: 'red' }}>Error: {error}</div>}
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {documents.map(doc => (
            <li key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <div>
                <strong>{doc.filename}</strong> ({doc.status})
              </div>
              <button onClick={() => onDelete(doc.id)} disabled={documentsLoading}>
                Delete
              </button>
            </li>
          ))}
          {documentsLoading && <li>Loading...</li>}
          {!documentsLoading && documents.length === 0 && <li>No documents yet.</li>}
        </ul>
      </Tabs.Content>

      <Tabs.Content value="tools" style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
        <h3>MCP Tools</h3>
        {toolsLoading && <p>Loading tools...</p>}
        {!toolsLoading && tools.length === 0 && <p>No tools available.</p>}
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {tools.map(tool => (
            <li key={tool.tool_name} style={{ marginBottom: '1rem', border: '1px solid #eee', padding: '0.5rem' }}>
              <strong>{tool.tool_name}</strong> <span style={{ color: '#666' }}>({tool.server_name})</span>
              <p style={{ margin: '0.25rem 0' }}>{tool.description}</p>
              <button>Invoke</button>
            </li>
          ))}
        </ul>
      </Tabs.Content>
    </Tabs.Root>
  );
};

export default RightPanel;
