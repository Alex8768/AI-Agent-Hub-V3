import React from 'react'
import { ChevronLeft, ChevronRight, PanelLeft, PanelRight } from 'lucide-react'

import { Button } from '@/components/ui/button'

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
  const gridTemplateColumns = `${leftVisible ? 'minmax(248px, 312px)' : '56px'} minmax(0, 1fr) ${rightVisible ? 'minmax(290px, 360px)' : '56px'}`

  return (
    <div className="h-full w-full p-3">
      <div className="grid h-full w-full gap-3" style={{ gridTemplateColumns }}>
        <div className="min-h-0">
          {leftVisible ? (
            <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border bg-card/50">
              <div className="flex h-9 items-center justify-end border-b px-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={onToggleLeft}
                  aria-label="Collapse left sidebar"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              </div>
              <div className="min-h-0 flex-1 overflow-auto">{leftPanel}</div>
            </div>
          ) : (
            <div className="flex h-full min-h-0 flex-col items-center justify-start rounded-xl border bg-muted/30 p-1.5">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-md"
                onClick={onToggleLeft}
                aria-label="Expand left sidebar"
              >
                <PanelLeft className="h-4 w-4" />
              </Button>
              <span className="mt-2 text-[10px] uppercase tracking-wider text-muted-foreground">Nav</span>
            </div>
          )}
        </div>

        <div className="min-h-0">
          <div className="h-full min-h-0 overflow-hidden rounded-xl border bg-background">{centerPanel}</div>
        </div>

        <div className="min-h-0">
          {rightVisible ? (
            <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border bg-card/50">
              <div className="flex h-9 items-center justify-start border-b px-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={onToggleRight}
                  aria-label="Collapse right sidebar"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <div className="min-h-0 flex-1 overflow-auto">{rightPanel}</div>
            </div>
          ) : (
            <div className="flex h-full min-h-0 flex-col items-center justify-start rounded-xl border bg-muted/30 p-1.5">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-md"
                onClick={onToggleRight}
                aria-label="Expand right sidebar"
              >
                <PanelRight className="h-4 w-4" />
              </Button>
              <span className="mt-2 text-[10px] uppercase tracking-wider text-muted-foreground">Ops</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AppLayout
