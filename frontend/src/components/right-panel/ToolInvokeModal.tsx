import React from 'react';
import type { ToolItemDto, ToolSchemaDto } from '../../contracts/api';

interface ToolInvokeModalProps {
  selectedTool: ToolItemDto;
  selectedToolSchema: ToolSchemaDto | null;
  schemaLoading: boolean;
  invokeArgsText: string;
  invokeResult: string;
  invokeError: string;
  invokeLoading: boolean;
  resultCopied: boolean;
  onClose: () => void;
  onArgsChange: (value: string) => void;
  onApplySchemaTemplate: () => void;
  onInvoke: (event: React.FormEvent) => void;
  onCopyResult: () => void | Promise<void>;
}

const ToolInvokeModal: React.FC<ToolInvokeModalProps> = ({
  selectedTool,
  selectedToolSchema,
  schemaLoading,
  invokeArgsText,
  invokeResult,
  invokeError,
  invokeLoading,
  resultCopied,
  onClose,
  onArgsChange,
  onApplySchemaTemplate,
  onInvoke,
  onCopyResult,
}) => {
  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 23, 42, 0.55)',
        display: 'grid',
        placeItems: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div className="invoke-modal" onClick={(event) => event.stopPropagation()}>
        <h3 className="panel-title" style={{ marginTop: 0 }}>
          Invoke Tool: {selectedTool.tool_name}
        </h3>

        {schemaLoading && <p className="empty-note">Loading schema...</p>}

        {selectedToolSchema?.input_schema && (
          <details className="schema-block">
            <summary>Input schema</summary>
            <pre className="schema-pre">
              {JSON.stringify(selectedToolSchema.input_schema, null, 2)}
            </pre>
          </details>
        )}

        <form onSubmit={onInvoke}>
          <label className="field-label" style={{ marginBottom: '0.5rem' }}>
            Arguments (JSON object)
          </label>

          <textarea
            value={invokeArgsText}
            onChange={(e) => onArgsChange(e.target.value)}
            rows={8}
            className="invoke-textarea"
          />

          {invokeError && (
            <div className="error-banner" style={{ marginTop: '0.75rem' }}>
              Error: {invokeError}
            </div>
          )}

          <div className="modal-actions">
            <button
              className="btn btn-secondary"
              type="button"
              onClick={onApplySchemaTemplate}
              disabled={schemaLoading || invokeLoading}
            >
              Use schema template
            </button>

            <button className="btn btn-primary" type="submit" disabled={invokeLoading}>
              {invokeLoading ? 'Invoking...' : 'Run'}
            </button>

            <button
              className="btn btn-secondary"
              type="button"
              onClick={onClose}
              disabled={invokeLoading}
            >
              Close
            </button>
          </div>
        </form>

        {invokeResult && (
          <div className="invoke-result-wrap">
            <div className="invoke-result-head">
              <h4 className="section-title">Result</h4>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => void onCopyResult()}
              >
                {resultCopied ? 'Copied' : 'Copy'}
              </button>
            </div>

            <pre className="invoke-result-pre">{invokeResult}</pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ToolInvokeModal;
