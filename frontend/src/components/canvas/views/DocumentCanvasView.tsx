import ReactMarkdown from 'react-markdown'

interface DocumentCanvasViewProps {
  payload?: unknown
}

function resolveDocumentText(payload: unknown): string {
  if (typeof payload === 'string') return payload
  if (payload && typeof payload === 'object' && typeof (payload as { text?: unknown }).text === 'string') {
    return (payload as { text: string }).text
  }
  return ''
}

export default function DocumentCanvasView({ payload }: DocumentCanvasViewProps) {
  const text = resolveDocumentText(payload)
  return (
    <div className="h-full overflow-auto p-4">
      <h3 className="mb-3 text-sm font-semibold">Document Preview</h3>
      <div className="rounded-md border bg-card p-4">
        {text ? (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">Document payload is empty.</div>
        )}
      </div>
    </div>
  )
}
