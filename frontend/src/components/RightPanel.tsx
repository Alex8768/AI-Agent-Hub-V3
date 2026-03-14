import React, { useEffect, useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import {
  deleteDocument,
  getToolSchema,
  invokeTool,
  listDocuments,
  listTools,
  uploadDocument,
} from '../lib/apiClient';
import type { DocumentItem, ToolItemDto, ToolSchemaDto } from '../contracts/api';
import DocumentsPanel from './right-panel/DocumentsPanel';
import ToolsPanel from './right-panel/ToolsPanel';
import ToolInvokeModal from './right-panel/ToolInvokeModal';

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
  const [invokeResult, setInvokeResult] = useState('');
  const [invokeError, setInvokeError] = useState('');
  const [invokeLoading, setInvokeLoading] = useState(false);
  const [resultCopied, setResultCopied] = useState(false);

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

  useEffect(() => {
    let alive = true;
    setDocumentsLoading(true);

    listDocuments({ workspaceId })
      .then((items) => {
        if (alive) setDocuments(items);
      })
      .catch((err) => setError(String(err)))
      .finally(() => {
        if (alive) setDocumentsLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [workspaceId]);

  useEffect(() => {
    let alive = true;
    setToolsLoading(true);

    listTools({ workspaceId })
      .then((data) => {
        if (alive) setTools(data.tools || []);
      })
      .catch((err) => setError(String(err)))
      .finally(() => {
        if (alive) setToolsLoading(false);
      });

    return () => {
      alive = false;
    };
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
      setDocuments((prev) => prev.filter((item) => item.id !== id));
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
    setResultCopied(false);
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

  const copyInvokeResult = async () => {
    if (!invokeResult) return;

    try {
      await navigator.clipboard.writeText(invokeResult);
      setResultCopied(true);
      window.setTimeout(() => setResultCopied(false), 1200);
    } catch (err) {
      setInvokeError(`Copy failed: ${String(err)}`);
    }
  };

  return (
    <>
      <Tabs.Root defaultValue="files" className="tabs-root">
        <Tabs.List className="tabs-list">
          <Tabs.Trigger value="files" className="tabs-trigger">
            Files
          </Tabs.Trigger>
          <Tabs.Trigger value="tools" className="tabs-trigger">
            Tools
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="files" className="tabs-content">
          <DocumentsPanel
            documents={documents}
            documentsLoading={documentsLoading}
            error={error}
            selectedFile={selectedFile}
            onFileSelected={onFileSelected}
            onUpload={onUpload}
            onDelete={onDelete}
          />
        </Tabs.Content>

        <Tabs.Content value="tools" className="tabs-content">
          <ToolsPanel
            tools={tools}
            toolsLoading={toolsLoading}
            onInvokeTool={openInvokeModal}
          />
        </Tabs.Content>
      </Tabs.Root>

      {selectedTool && (
        <ToolInvokeModal
          selectedTool={selectedTool}
          selectedToolSchema={selectedToolSchema}
          schemaLoading={schemaLoading}
          invokeArgsText={invokeArgsText}
          invokeResult={invokeResult}
          invokeError={invokeError}
          invokeLoading={invokeLoading}
          resultCopied={resultCopied}
          onClose={closeInvokeModal}
          onArgsChange={setInvokeArgsText}
          onApplySchemaTemplate={applySchemaTemplate}
          onInvoke={onInvoke}
          onCopyResult={copyInvokeResult}
        />
      )}
    </>
  );
};

export default RightPanel;
