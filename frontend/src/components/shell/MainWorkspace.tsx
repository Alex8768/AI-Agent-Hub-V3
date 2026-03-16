import { useEffect, useRef, useState, type ReactNode } from 'react'
import type { AppMode } from './layoutState'

interface MainWorkspaceProps {
  appMode: AppMode
  chatContent: ReactNode
  canvasContent: ReactNode
}

const SPLIT_STORAGE_KEY = 'workspace.split.ratio.v1'
const DEFAULT_CHAT_SPLIT = 62
const MIN_CHAT_SPLIT = 35
const MAX_CHAT_SPLIT = 75

function clampSplit(value: number): number {
  return Math.min(MAX_CHAT_SPLIT, Math.max(MIN_CHAT_SPLIT, value))
}

function readSplitRatio(): number {
  if (typeof window === 'undefined') return DEFAULT_CHAT_SPLIT
  const raw = Number(localStorage.getItem(SPLIT_STORAGE_KEY))
  if (Number.isNaN(raw)) return DEFAULT_CHAT_SPLIT
  return clampSplit(raw)
}

export default function MainWorkspace({
  appMode,
  chatContent,
  canvasContent,
}: MainWorkspaceProps) {
  const [chatSplit, setChatSplit] = useState<number>(() => readSplitRatio())
  const splitRef = useRef<HTMLDivElement | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    localStorage.setItem(SPLIT_STORAGE_KEY, String(chatSplit))
  }, [chatSplit])

  useEffect(() => {
    if (!isDragging) return

    const onPointerMove = (event: PointerEvent) => {
      const container = splitRef.current
      if (!container) return
      const rect = container.getBoundingClientRect()
      if (rect.width <= 0) return
      const next = ((event.clientX - rect.left) / rect.width) * 100
      setChatSplit(clampSplit(next))
    }

    const onPointerUp = () => setIsDragging(false)

    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
    return () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
    }
  }, [isDragging])

  if (appMode === 'canvas') {
    return <div className="h-full bg-background">{canvasContent}</div>
  }

  if (appMode === 'split') {
    return (
      <div
        ref={splitRef}
        className="grid h-full min-h-0 w-full"
        style={{
          gridTemplateColumns: `${chatSplit}% 12px minmax(0, 1fr)`,
        }}
      >
        <section className="h-full min-h-0 overflow-hidden bg-background">{chatContent}</section>
        <div
          role="separator"
          aria-orientation="vertical"
          aria-valuemin={MIN_CHAT_SPLIT}
          aria-valuemax={MAX_CHAT_SPLIT}
          aria-valuenow={Math.round(chatSplit)}
          className={`group relative cursor-col-resize select-none ${isDragging ? 'bg-primary/20' : 'bg-muted/30 hover:bg-muted/60'}`}
          onPointerDown={(event) => {
            event.preventDefault()
            ;(event.currentTarget as HTMLDivElement).setPointerCapture?.(event.pointerId)
            setIsDragging(true)
          }}
        >
          <div className="absolute inset-y-0 left-1/2 w-3 -translate-x-1/2" />
          <div
            className={`absolute inset-y-2 left-1/2 w-px -translate-x-1/2 rounded-full transition-colors ${isDragging ? 'bg-primary' : 'bg-border/90 group-hover:bg-primary/80'}`}
          />
        </div>
        <section className="h-full min-h-0 overflow-hidden bg-background/95">{canvasContent}</section>
      </div>
    )
  }

  return <div className="h-full bg-background">{chatContent}</div>
}
