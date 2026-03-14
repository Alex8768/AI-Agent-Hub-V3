import React from 'react';
import type { DocumentItem } from '../../contracts/api';

interface DocumentsPanelProps {
  documents: DocumentItem[];
  documentsLoading: boolean;
  error: string;
  selectedFile: File | null;
  onFileSelected: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onUpload: (event: React.FormEvent) => void;
  onDelete: (id: string) => void;
}

const DocumentsPanel: React.FC<DocumentsPanelProps> = ({
  documents,
  documentsLoading,
  error,
  selectedFile,
  onFileSelected,
  onUpload,
  onDelete,
}) => {
  return (
    <div className="panel-body">
      <h3 className="panel-title">Documents</h3>

      <form onSubmit={onUpload} className="upload-form">
        <input className="field-input" type="file" onChange={onFileSelected} />
        <button
          className="btn btn-primary"
          type="submit"
          disabled={!selectedFile || documentsLoading}
        >
          Upload
        </button>
      </form>

      {error && <div className="error-banner">Error: {error}</div>}

      <ul className="item-list">
        {documents.map((doc) => (
          <li key={doc.id} className="item-row">
            <div className="item-main">
              <strong>{doc.filename}</strong>
              <div className="item-subtle">
                {doc.status} - {(doc.size_bytes / 1024).toFixed(1)} KB
              </div>
            </div>

            <button
              className="btn btn-danger"
              type="button"
              onClick={() => onDelete(doc.id)}
              disabled={documentsLoading}
            >
              Delete
            </button>
          </li>
        ))}

        {documentsLoading && <li className="empty-note">Loading...</li>}
        {!documentsLoading && documents.length === 0 && (
          <li className="empty-note">No documents yet.</li>
        )}
      </ul>
    </div>
  );
};

export default DocumentsPanel;
