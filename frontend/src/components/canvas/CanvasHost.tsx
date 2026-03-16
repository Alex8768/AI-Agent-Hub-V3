import type { CanvasState } from './canvasState'
import ArtifactCanvasView from './views/ArtifactCanvasView'
import DiffCanvasView from './views/DiffCanvasView'
import DocumentCanvasView from './views/DocumentCanvasView'
import EmptyCanvasView from './views/EmptyCanvasView'
import GraphCanvasView from './views/GraphCanvasView'
import PlanCanvasView from './views/PlanCanvasView'

interface CanvasHostProps {
  canvasState: CanvasState
}

export default function CanvasHost({ canvasState }: CanvasHostProps) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b px-3 py-2">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">Canvas</div>
        <div className="text-sm font-medium">{canvasState.title ?? 'Workspace Surface'}</div>
      </div>
      <div className="min-h-0 flex-1">
        {canvasState.activeView === 'graph' && <GraphCanvasView payload={canvasState.payload} />}
        {canvasState.activeView === 'plan' && <PlanCanvasView payload={canvasState.payload} />}
        {canvasState.activeView === 'diff' && <DiffCanvasView payload={canvasState.payload} />}
        {canvasState.activeView === 'artifact' && <ArtifactCanvasView payload={canvasState.payload} />}
        {canvasState.activeView === 'document' && <DocumentCanvasView payload={canvasState.payload} />}
        {canvasState.activeView === 'empty' && <EmptyCanvasView canvasState={canvasState} />}
      </div>
    </div>
  )
}
