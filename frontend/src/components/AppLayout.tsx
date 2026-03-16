import React, { useEffect } from 'react'
import { X } from 'lucide-react'

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
  const hasOpenDrawer = leftVisible || rightVisible

  useEffect(() => {
    if (!hasOpenDrawer) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      if (leftVisible && onToggleLeft) onToggleLeft()
      if (rightVisible && onToggleRight) onToggleRight()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [hasOpenDrawer, leftVisible, rightVisible, onToggleLeft, onToggleRight])

  return (
    <div className="h-full w-full p-3">
      <div className="relative h-full w-full overflow-hidden rounded-xl border bg-background">
        <div className="h-full min-h-0">{centerPanel}</div>

        {hasOpenDrawer && (
          <button
            type="button"
            className="absolute inset-0 z-20 bg-black/10 backdrop-blur-[1px]"
            aria-label="Close side panels"
            onClick={() => {
              if (leftVisible && onToggleLeft) onToggleLeft()
              if (rightVisible && onToggleRight) onToggleRight()
            }}
          />
        )}

        {leftVisible && (
          <aside className="absolute inset-y-0 left-0 z-30 w-[min(20rem,calc(100vw-3rem))] border-r bg-background shadow-xl">
            <div className="flex h-10 items-center justify-end border-b px-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={onToggleLeft}
                aria-label="Close left panel"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="h-[calc(100%-2.5rem)] min-h-0 overflow-auto">{leftPanel}</div>
          </aside>
        )}

        {rightVisible && (
          <aside className="absolute inset-y-0 right-0 z-30 w-[min(22rem,calc(100vw-3rem))] border-l bg-background shadow-xl">
            <div className="flex h-10 items-center justify-start border-b px-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={onToggleRight}
                aria-label="Close right panel"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="h-[calc(100%-2.5rem)] min-h-0 overflow-auto">{rightPanel}</div>
          </aside>
        )}
      </div>
    </div>
  )
}

export default AppLayout
