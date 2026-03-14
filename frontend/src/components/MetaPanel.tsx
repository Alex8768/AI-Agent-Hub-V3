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

  const hasOptimization = Object.keys(optimization).length > 0;
  const hasMetaCognition = Object.keys(metaCognition).length > 0;

  return (
    <div style={{ padding: '1rem', display: 'grid', gap: '1rem' }}>
      <h2 style={{ margin: 0 }}>Meta / Self-Evolution</h2>

      {!hasOptimization && !hasMetaCognition && (
        <div style={{ color: '#666', fontSize: '0.95rem' }}>
          Нет meta-данных. Отправьте запрос в чате, чтобы получить `reasoning_optimization` и `meta_cognition`.
        </div>
      )}

      <div style={{ border: '1px solid #ddd', borderRadius: '6px', padding: '0.75rem' }}>
        <h3 style={{ marginTop: 0 }}>Reasoning Optimization</h3>
        {hasOptimization ? (
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(optimization, null, 2)}
          </pre>
        ) : (
          <p style={{ margin: 0, color: '#666' }}>Нет данных в `diagnostics.reasoning_optimization`.</p>
        )}
      </div>

      <div style={{ border: '1px solid #ddd', borderRadius: '6px', padding: '0.75rem' }}>
        <h3 style={{ marginTop: 0 }}>Meta Cognition</h3>
        {hasMetaCognition ? (
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(metaCognition, null, 2)}
          </pre>
        ) : (
          <p style={{ margin: 0, color: '#666' }}>Нет данных в `diagnostics.meta_cognition`.</p>
        )}
      </div>
    </div>
  );
};

export default MetaPanel;
