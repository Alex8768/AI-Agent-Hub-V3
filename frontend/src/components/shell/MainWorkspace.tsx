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
    return <div className="h-full bg-background">{canvasContent}</div>
  }

  if (appMode === 'split') {
    return (
      <div className="grid h-full min-h-0 grid-cols-[1.3fr_1fr] gap-3 p-3">
        <section className="min-h-0 overflow-hidden rounded-lg bg-background">{chatContent}</section>
        <section className="min-h-0 overflow-hidden rounded-lg bg-background">{canvasContent}</section>
      </div>
    )
  }

  return <div className="h-full bg-background">{chatContent}</div>
}
