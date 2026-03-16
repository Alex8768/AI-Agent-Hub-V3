interface DiffPayload {
  before?: string
  after?: string
  unified?: string
}

interface DiffCanvasViewProps {
  payload?: unknown
}

export default function DiffCanvasView({ payload }: DiffCanvasViewProps) {
  const diff = (payload as DiffPayload | undefined) ?? {}

  if (typeof diff.unified === 'string' && diff.unified.trim()) {
    return (
      <div className="h-full overflow-auto p-4">
        <h3 className="mb-3 text-sm font-semibold">Diff Preview</h3>
        <pre className="rounded-md border bg-card p-3 font-mono text-xs leading-5 whitespace-pre-wrap">
          {diff.unified}
        </pre>
      </div>
    )
  }

  return (
    <div className="grid h-full min-h-0 grid-cols-2 gap-3 p-4">
      <section className="min-h-0 overflow-auto rounded-md border bg-card p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Before</h3>
        <pre className="font-mono text-xs leading-5 whitespace-pre-wrap">{diff.before ?? ''}</pre>
      </section>
      <section className="min-h-0 overflow-auto rounded-md border bg-card p-3">
        <h3 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">After</h3>
        <pre className="font-mono text-xs leading-5 whitespace-pre-wrap">{diff.after ?? ''}</pre>
      </section>
    </div>
  )
}
