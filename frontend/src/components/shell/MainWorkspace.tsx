import type { ReactNode } from 'react'
import type { AppMode } from './layoutState'

interface MainWorkspaceProps {
  appMode: AppMode
  chatContent: ReactNode
  canvasContent: ReactNode
}

export default function MainWorkspace({
  appMode,
  chatContent,
  canvasContent,
}: MainWorkspaceProps) {
  if (appMode === 'canvas') {
    return <div className="h-full">{canvasContent}</div>
  }

  if (appMode === 'split') {
    return (
      <div className="grid h-full min-h-0 grid-cols-[1.3fr_1fr] gap-2 p-2">
        <section className="min-h-0 overflow-hidden rounded-lg border">{chatContent}</section>
        <section className="min-h-0 overflow-hidden rounded-lg border">{canvasContent}</section>
      </div>
    )
  }

  return <div className="h-full">{chatContent}</div>
}
