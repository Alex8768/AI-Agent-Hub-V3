interface ArtifactCanvasViewProps {
  payload?: unknown
}

function toPrettyJson(payload: unknown): string {
  try {
    return JSON.stringify(payload, null, 2)
  } catch {
    return String(payload)
  }
}

export default function ArtifactCanvasView({ payload }: ArtifactCanvasViewProps) {
  return (
    <div className="h-full overflow-auto p-4">
      <h3 className="mb-3 text-sm font-semibold">Artifact Preview</h3>
      <pre className="rounded-md border bg-card p-3 font-mono text-xs leading-5 whitespace-pre-wrap">
        {toPrettyJson(payload)}
      </pre>
    </div>
  )
}
