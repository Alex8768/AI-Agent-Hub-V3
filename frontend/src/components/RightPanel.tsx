import React, { useState, useEffect } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { listDocuments, uploadDocument, deleteDocument, listTools, invokeTool, getToolSchema } from '../lib/apiClient';
import type { DocumentItem, ToolItemDto, ToolSchemaDto } from '../contracts/api';

interface RightPanelProps {
  workspaceId: string;
}

const RightPanel: React.FC<RightPanelProps> = ({ workspaceId }) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [tools, setTools] = useState<ToolItemDto[]>([]);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedTool, setSelectedTool] = useState<ToolItemDto | null>(null);
  const [selectedToolSchema, setSelectedToolSchema] = useState<ToolSchemaDto | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [invokeArgsText, setInvokeArgsText] = useState('{}');
  const [invokeResult, setInvokeResult] = useState<string>('');
  const [invokeError, setInvokeError] = useState('');
  const [invokeLoading, setInvokeLoading] = useState(false);

  const buildTemplateFromSchema = (schema: unknown): Record<string, unknown> => {
    if (!schema || typeof schema !== 'object' || Array.isArray(schema)) return {};
    const row = schema as Record<string, unknown>;
    const properties =
      row.properties && typeof row.properties === 'object' && !Array.isArray(row.properties)
        ? (row.properties as Record<string, unknown>)
        : {};
    const required = Array.isArray(row.required)
      ? row.required.map((x) => String(x || '')).filter((x) => x.length > 0)
      : [];

    const inferDefault = (value: unknown): unknown => {
      if (!value || typeof value !== 'object' || Array.isArray(value)) return '';
      const spec = value as Record<string, unknown>;
      if (spec.default !== undefined) return spec.default;
      const type = String(spec.type || '').toLowerCase();
      if (type === 'number' || type === 'integer') return 0;
      if (type === 'boolean') return false;
      if (type === 'array') return [];
      if (type === 'object') return {};
      return '';
    };

    const keys = required.length > 0 ? required : Object.keys(properties);
    const output: Record<string, unknown> = {};
    keys.forEach((key) => {
      output[key] = inferDefault(properties[key]);
    });
    return output;
  };

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
    listTools({ workspaceId })
      .then(data => {
        if (alive) setTools(data.tools || []);
      })
      .catch(err => setError(String(err)))
      .finally(() => {
        if (alive) setToolsLoading(false);
      });
    return () => { alive = false; };
  }, [workspaceId]);

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

  const openInvokeModal = async (tool: ToolItemDto) => {
    setSelectedTool(tool);
    setSelectedToolSchema(null);
    setInvokeArgsText('{}');
    setInvokeResult('');
    setInvokeError('');
    setSchemaLoading(true);
    try {
      const schema = await getToolSchema(tool.tool_name, { workspaceId });
      setSelectedToolSchema(schema);
      const template = buildTemplateFromSchema(schema.input_schema);
      setInvokeArgsText(JSON.stringify(template, null, 2));
    } catch (err) {
      setInvokeError(`Failed to load schema: ${String(err)}`);
    } finally {
      setSchemaLoading(false);
    }
  };

  const closeInvokeModal = () => {
    setSelectedTool(null);
    setSelectedToolSchema(null);
    setSchemaLoading(false);
    setInvokeLoading(false);
  };

  const onInvoke = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedTool?.tool_name) return;
    setInvokeLoading(true);
    setInvokeError('');
    setInvokeResult('');
    try {
      let parsed: unknown = {};
      if (invokeArgsText.trim().length > 0) {
        parsed = JSON.parse(invokeArgsText);
      }
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('Arguments must be a JSON object');
      }
      const result = await invokeTool(
        selectedTool.tool_name,
        parsed as Record<string, unknown>,
        { workspaceId },
      );
      setInvokeResult(JSON.stringify(result, null, 2));
    } catch (err) {
      setInvokeError(String(err));
    } finally {
      setInvokeLoading(false);
    }
  };

  const applySchemaTemplate = () => {
    if (!selectedToolSchema) return;
    const template = buildTemplateFromSchema(selectedToolSchema.input_schema);
    setInvokeArgsText(JSON.stringify(template, null, 2));
  };

  return (
    <>
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
              <button onClick={() => void openInvokeModal(tool)}>Invoke</button>
            </li>
          ))}
        </ul>
      </Tabs.Content>
    </Tabs.Root>
    {selectedTool && (
      <div
        role="dialog"
        aria-modal="true"
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.35)',
          display: 'grid',
          placeItems: 'center',
          zIndex: 1000,
        }}
      >
        <div style={{ width: 'min(640px, 92vw)', background: '#fff', borderRadius: '8px', padding: '1rem' }}>
          <h3 style={{ marginTop: 0 }}>Invoke Tool: {selectedTool.tool_name}</h3>
          {schemaLoading && <p style={{ marginTop: 0 }}>Loading schema...</p>}
          {selectedToolSchema?.input_schema && (
            <details style={{ marginBottom: '0.75rem' }}>
              <summary style={{ cursor: 'pointer' }}>Input schema</summary>
              <pre style={{ marginTop: '0.5rem', maxHeight: '180px', overflow: 'auto' }}>
                {JSON.stringify(selectedToolSchema.input_schema, null, 2)}
              </pre>
            </details>
          )}
          <form onSubmit={onInvoke}>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>Arguments (JSON object)</label>
            <textarea
              value={invokeArgsText}
              onChange={(e) => setInvokeArgsText(e.target.value)}
              rows={8}
              style={{ width: '100%', fontFamily: 'monospace' }}
            />
            {invokeError && <div style={{ color: 'red', marginTop: '0.5rem' }}>Error: {invokeError}</div>}
            <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
              <button type="button" onClick={applySchemaTemplate} disabled={schemaLoading || invokeLoading}>
                Use schema template
              </button>
              <button type="submit" disabled={invokeLoading}>
                {invokeLoading ? 'Invoking...' : 'Run'}
              </button>
              <button type="button" onClick={closeInvokeModal} disabled={invokeLoading}>
                Close
              </button>
            </div>
          </form>
          {invokeResult && (
            <div style={{ marginTop: '0.75rem' }}>
              <h4 style={{ margin: '0 0 0.25rem 0' }}>Result</h4>
              <pre style={{ margin: 0, maxHeight: '280px', overflow: 'auto' }}>{invokeResult}</pre>
            </div>
          )}
        </div>
      </div>
    )}
    </>
  );
};

export default RightPanel;
