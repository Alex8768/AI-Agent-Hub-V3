import { Copy, Download, Forward, RefreshCcw, ScrollText, Search, SquarePen } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ResultActionBarProps {
  onCopy: () => void
  onRetry: () => void
  onContinue: () => void
  onOpenCanvas: () => void
  onOpenDiff: () => void
  onOpenArtifact: () => void
  onShowTrace: () => void
  showTraceAction?: boolean
  onShowContext: () => void
  onExport: () => void
}

export default function ResultActionBar({
  onCopy,
  onRetry,
  onContinue,
  onOpenCanvas,
  onOpenDiff,
  onOpenArtifact,
  onShowTrace,
  showTraceAction = true,
  onShowContext,
  onExport,
}: ResultActionBarProps) {
  return (
    <div className="mt-3 flex flex-wrap items-center gap-1.5">
      <Button size="sm" variant="ghost" onClick={onCopy}>
        <Copy className="mr-1 h-3.5 w-3.5" />
        Copy
      </Button>
      <Button size="sm" variant="ghost" onClick={onRetry}>
        <RefreshCcw className="mr-1 h-3.5 w-3.5" />
        Retry
      </Button>
      <Button size="sm" variant="ghost" onClick={onContinue}>
        <Forward className="mr-1 h-3.5 w-3.5" />
        Continue
      </Button>
      <Button size="sm" variant="ghost" onClick={onOpenCanvas}>
        <SquarePen className="mr-1 h-3.5 w-3.5" />
        Open Canvas
      </Button>
      <Button size="sm" variant="ghost" onClick={onOpenDiff}>
        Open Diff
      </Button>
      <Button size="sm" variant="ghost" onClick={onOpenArtifact}>
        Open Artifact
      </Button>
      {showTraceAction && (
        <Button size="sm" variant="ghost" onClick={onShowTrace}>
          <ScrollText className="mr-1 h-3.5 w-3.5" />
          Show Trace
        </Button>
      )}
      <Button size="sm" variant="ghost" onClick={onShowContext}>
        <Search className="mr-1 h-3.5 w-3.5" />
        Show Context
      </Button>
      <Button size="sm" variant="ghost" onClick={onExport}>
        <Download className="mr-1 h-3.5 w-3.5" />
        Export
      </Button>
    </div>
  )
}
