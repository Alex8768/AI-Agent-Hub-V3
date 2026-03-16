import type { CanvasState } from '../canvasState'

interface EmptyCanvasViewProps {
  canvasState: CanvasState
}

export default function EmptyCanvasView({ canvasState }: EmptyCanvasViewProps) {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="rounded-lg border bg-card px-4 py-3 text-sm text-muted-foreground">
        {canvasState.title ?? 'Canvas is ready. Open graph, plan, diff, artifact, or document.'}
      </div>
    </div>
  )
}
