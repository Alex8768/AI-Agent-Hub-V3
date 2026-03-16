import React from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

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
  const gridTemplateColumns = `${leftVisible ? 'minmax(240px, 320px)' : '48px'} minmax(0, 1fr) ${rightVisible ? 'minmax(280px, 380px)' : '48px'}`

  return (
    <div className="h-full w-full p-2">
      <div className="grid h-full w-full gap-2" style={{ gridTemplateColumns }}>
        <div className="min-h-0">
          <Card className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border shadow-sm">
            <div className="flex h-10 items-center justify-between border-b px-3">
              {leftVisible ? (
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  History
                </span>
              ) : (
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">L</span>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={onToggleLeft}
                aria-label={leftVisible ? 'Collapse left sidebar' : 'Expand left sidebar'}
              >
                {leftVisible ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </Button>
            </div>
            <div className={`min-h-0 flex-1 overflow-auto ${leftVisible ? '' : 'hidden'}`}>
              {leftPanel}
            </div>
          </Card>
        </div>

        <div className="min-h-0">
          <Card className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border shadow-sm">
            <div className="min-h-0 flex-1 overflow-hidden">{centerPanel}</div>
          </Card>
        </div>

        <div className="min-h-0">
          <Card className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border shadow-sm">
            <div className="flex h-10 items-center justify-between border-b px-3">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={onToggleRight}
                aria-label={rightVisible ? 'Collapse right sidebar' : 'Expand right sidebar'}
              >
                {rightVisible ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
              </Button>
              {rightVisible ? (
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Context
                </span>
              ) : (
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">R</span>
              )}
            </div>
            <div className={`min-h-0 flex-1 overflow-auto ${rightVisible ? '' : 'hidden'}`}>
              {rightPanel}
            </div>
            {!rightVisible && (
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-full border-t"
                onClick={onToggleRight}
                aria-label="Expand right sidebar"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
