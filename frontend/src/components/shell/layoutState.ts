import { DEFAULT_CANVAS_STATE, normalizeCanvasState, type CanvasState } from '../canvas/canvasState'

export type AppMode = 'chat' | 'split' | 'canvas'

export type LeftSidebarSection = 'chats' | 'projects' | 'views' | 'saved'
export type RightSidebarTab = 'files' | 'tools' | 'context' | 'trace' | 'approvals'
export type LayoutDensity = 'comfortable' | 'compact'

export interface ShellLayoutState {
  appMode: AppMode
  leftSidebarOpen: boolean
  leftSidebarSection: LeftSidebarSection
  rightSidebarOpen: boolean
  rightSidebarTab: RightSidebarTab
  canvasVisible: boolean
  density: LayoutDensity
  showReasoningSummaries: boolean
  showExecutionEvents: boolean
  canvas: CanvasState
}

const STORAGE_KEY = 'shell.layout.v1'

export const DEFAULT_LAYOUT_STATE: ShellLayoutState = {
  appMode: 'chat',
  leftSidebarOpen: true,
  leftSidebarSection: 'chats',
  rightSidebarOpen: true,
  rightSidebarTab: 'files',
  canvasVisible: false,
  density: 'comfortable',
  showReasoningSummaries: true,
  showExecutionEvents: true,
  canvas: DEFAULT_CANVAS_STATE,
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function readLayoutState(): ShellLayoutState {
  if (typeof window === 'undefined') return DEFAULT_LAYOUT_STATE

  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_LAYOUT_STATE

    const parsed = JSON.parse(raw) as unknown
    if (!isObject(parsed)) return DEFAULT_LAYOUT_STATE

    const next: ShellLayoutState = {
      appMode: parsed.appMode === 'split' || parsed.appMode === 'canvas' ? parsed.appMode : 'chat',
      leftSidebarOpen: parsed.leftSidebarOpen !== false,
      leftSidebarSection:
        parsed.leftSidebarSection === 'chats' ||
        parsed.leftSidebarSection === 'projects' ||
        parsed.leftSidebarSection === 'views' ||
        parsed.leftSidebarSection === 'saved'
          ? parsed.leftSidebarSection
          : 'chats',
      rightSidebarOpen: parsed.rightSidebarOpen !== false,
      rightSidebarTab:
        parsed.rightSidebarTab === 'tools' ||
        parsed.rightSidebarTab === 'files' ||
        parsed.rightSidebarTab === 'context' ||
        parsed.rightSidebarTab === 'trace' ||
        parsed.rightSidebarTab === 'approvals'
          ? parsed.rightSidebarTab
          : 'files',
      canvasVisible:
        parsed.appMode === 'split' || parsed.appMode === 'canvas'
          ? parsed.canvasVisible !== false
          : false,
      density: parsed.density === 'compact' ? 'compact' : 'comfortable',
      showReasoningSummaries: parsed.showReasoningSummaries !== false,
      showExecutionEvents: parsed.showExecutionEvents !== false,
      canvas: normalizeCanvasState(parsed.canvas),
    }

    return next
  } catch {
    return DEFAULT_LAYOUT_STATE
  }
}

export function writeLayoutState(state: ShellLayoutState): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}
