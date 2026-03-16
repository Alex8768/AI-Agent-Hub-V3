import React, { useEffect } from 'react'

interface AppLayoutProps {
  leftPanel: React.ReactNode
  centerPanel: React.ReactNode
  rightPanel: React.ReactNode
  leftVisible?: boolean
  rightVisible?: boolean
  onToggleLeft?: () => void
  onToggleRight?: () => void
}

const AppLayout: React.FC<AppLayoutProps> = ({
  leftPanel,
  centerPanel,
  rightPanel,
  leftVisible = true,
  rightVisible = true,
  onToggleLeft,
  onToggleRight,
}) => {
  const hasOpenPane = leftVisible || rightVisible
  const bothPanesOpen = leftVisible && rightVisible
  const leftPaneWidth = bothPanesOpen
    ? 'clamp(14rem, 19vw, 17rem)'
    : 'clamp(16rem, 22vw, 20rem)'
  const rightPaneWidth = bothPanesOpen
    ? 'clamp(15rem, 20vw, 18rem)'
    : 'clamp(18rem, 24vw, 22rem)'

  const gridTemplateColumns = leftVisible && rightVisible
    ? `${leftPaneWidth} minmax(0,1fr) ${rightPaneWidth}`
    : leftVisible
      ? `${leftPaneWidth} minmax(0,1fr)`
      : rightVisible
        ? `minmax(0,1fr) ${rightPaneWidth}`
        : 'minmax(0,1fr)'

  useEffect(() => {
    if (!hasOpenPane) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      if (leftVisible && onToggleLeft) onToggleLeft()
      if (rightVisible && onToggleRight) onToggleRight()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [hasOpenPane, leftVisible, rightVisible, onToggleLeft, onToggleRight])

  return (
    <div className="h-full w-full">
      <div
        className="grid h-full min-h-0 w-full overflow-hidden border-t border-border/70 bg-background transition-[grid-template-columns] duration-200 ease-out"
        style={{ gridTemplateColumns }}
      >
        {leftVisible && (
          <aside className="min-h-0 border-r border-border/70 bg-muted/20">
            <div className="h-full min-h-0 overflow-auto">{leftPanel}</div>
          </aside>
        )}

        <main className="min-h-0 bg-background">
          <div className="h-full min-h-0 overflow-hidden">{centerPanel}</div>
        </main>

        {rightVisible && (
          <aside className="min-h-0 border-l border-border/70 bg-muted/20">
            <div className="h-full min-h-0 overflow-auto">{rightPanel}</div>
          </aside>
        )}
      </div>
    </div>
  )
}

export default AppLayout
