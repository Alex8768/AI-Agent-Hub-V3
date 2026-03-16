export type CanvasViewType = 'graph' | 'plan' | 'diff' | 'artifact' | 'document' | 'empty'

export interface CanvasState {
  activeView: CanvasViewType
  title?: string
  payload?: unknown
}

export const DEFAULT_CANVAS_STATE: CanvasState = {
  activeView: 'empty',
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function normalizeCanvasState(raw: unknown): CanvasState {
  if (!isObject(raw)) return DEFAULT_CANVAS_STATE

  const view = raw.activeView
  const activeView: CanvasViewType =
    view === 'graph' ||
    view === 'plan' ||
    view === 'diff' ||
    view === 'artifact' ||
    view === 'document'
      ? view
      : 'empty'

  return {
    activeView,
    title: typeof raw.title === 'string' ? raw.title : undefined,
    payload: raw.payload,
  }
}
