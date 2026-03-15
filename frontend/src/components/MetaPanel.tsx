import React from 'react';

interface MetaPanelProps {
  diagnostics: Record<string, unknown> | null;
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

const MetaPanel: React.FC<MetaPanelProps> = ({ diagnostics }) => {
  const root = diagnostics ?? {};
  const optimization = asRecord(root.reasoning_optimization);
  const metaCognition = asRecord(root.meta_cognition);
  const runtimeMode = asRecord(root.runtime_mode);
  const actRuntime = asRecord(root.act_runtime);

  const hasOptimization = Object.keys(optimization).length > 0;
  const hasMetaCognition = Object.keys(metaCognition).length > 0;
  const hasRuntimeMode = Object.keys(runtimeMode).length > 0;
  const hasActRuntime = Object.keys(actRuntime).length > 0;

  return (
    <div className="meta-shell">
      <h2 className="panel-title">Meta / Self-Evolution</h2>

      {!hasOptimization && !hasMetaCognition && !hasRuntimeMode && !hasActRuntime && (
        <div className="empty-note">
          No diagnostics yet. Send a query to populate optimization, meta-cognition, and runtime mode data.
        </div>
      )}

      <div className="meta-card">
        <h3 className="section-title">Runtime Mode</h3>
        {hasRuntimeMode ? (
          <pre className="meta-pre">{JSON.stringify(runtimeMode, null, 2)}</pre>
        ) : (
          <p className="empty-note">No `diagnostics.runtime_mode` payload.</p>
        )}
      </div>

      <div className="meta-card">
        <h3 className="section-title">Act Runtime</h3>
        {hasActRuntime ? (
          <pre className="meta-pre">{JSON.stringify(actRuntime, null, 2)}</pre>
        ) : (
          <p className="empty-note">No `diagnostics.act_runtime` payload.</p>
        )}
      </div>

      <div className="meta-card">
        <h3 className="section-title">Reasoning Optimization</h3>
        {hasOptimization ? (
          <pre className="meta-pre">{JSON.stringify(optimization, null, 2)}</pre>
        ) : (
          <p className="empty-note">No `diagnostics.reasoning_optimization` payload.</p>
        )}
      </div>

      <div className="meta-card">
        <h3 className="section-title">Meta Cognition</h3>
        {hasMetaCognition ? (
          <pre className="meta-pre">{JSON.stringify(metaCognition, null, 2)}</pre>
        ) : (
          <p className="empty-note">No `diagnostics.meta_cognition` payload.</p>
        )}
      </div>
    </div>
  );
};

export default MetaPanel;
