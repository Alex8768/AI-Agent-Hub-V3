import { Copy, Download, Forward, RefreshCcw, ScrollText, Search, SquarePen } from 'lucide-react'
import { Button } from '@/components/ui/button'

export interface ResultActionVisibility {
  copy?: boolean
  retry?: boolean
  continue?: boolean
  openCanvas?: boolean
  openDiff?: boolean
  openArtifact?: boolean
  showTrace?: boolean
  showContext?: boolean
  export?: boolean
}

interface ResultActionBarProps {
  onCopy: () => void
  onRetry: () => void
  onContinue: () => void
  onOpenCanvas: () => void
  onOpenDiff: () => void
  onOpenArtifact: () => void
  onShowTrace: () => void
  onShowContext: () => void
  onExport: () => void
  visibleActions?: ResultActionVisibility
}

export default function ResultActionBar({
  onCopy,
  onRetry,
  onContinue,
  onOpenCanvas,
  onOpenDiff,
  onOpenArtifact,
  onShowTrace,
  onShowContext,
  onExport,
  visibleActions,
}: ResultActionBarProps) {
  const actions: Required<ResultActionVisibility> = {
    copy: visibleActions?.copy ?? true,
    retry: visibleActions?.retry ?? true,
    continue: visibleActions?.continue ?? true,
    openCanvas: visibleActions?.openCanvas ?? true,
    openDiff: visibleActions?.openDiff ?? true,
    openArtifact: visibleActions?.openArtifact ?? true,
    showTrace: visibleActions?.showTrace ?? true,
    showContext: visibleActions?.showContext ?? true,
    export: visibleActions?.export ?? true,
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      {actions.copy && (
        <Button size="sm" variant="outline" className="h-8 px-3" onClick={onCopy}>
          <Copy className="mr-1.5 h-3.5 w-3.5" />
          Copy
        </Button>
      )}
      {actions.retry && (
        <Button size="sm" variant="outline" className="h-8 px-3" onClick={onRetry}>
          <RefreshCcw className="mr-1.5 h-3.5 w-3.5" />
          Retry
        </Button>
      )}
      {actions.continue && (
        <Button size="sm" variant="outline" className="h-8 px-3" onClick={onContinue}>
          <Forward className="mr-1.5 h-3.5 w-3.5" />
          Continue
        </Button>
      )}
      {actions.openCanvas && (
        <Button size="sm" variant="outline" className="h-8 px-3" onClick={onOpenCanvas}>
          <SquarePen className="mr-1.5 h-3.5 w-3.5" />
          Open Canvas
        </Button>
      )}
      {actions.openDiff && (
        <Button size="sm" variant="outline" className="h-8 px-3" onClick={onOpenDiff}>
          Open Diff
        </Button>
      )}
      {actions.openArtifact && (
        <Button size="sm" variant="outline" className="h-8 px-3" onClick={onOpenArtifact}>
          Inspect Files
        </Button>
      )}
      {actions.showTrace && (
        <Button size="sm" variant="ghost" onClick={onShowTrace}>
          <ScrollText className="mr-1 h-3.5 w-3.5" />
          Show Trace
        </Button>
      )}
      {actions.showContext && (
        <Button size="sm" variant="ghost" onClick={onShowContext}>
          <Search className="mr-1 h-3.5 w-3.5" />
          Show Context
        </Button>
      )}
      {actions.export && (
        <Button size="sm" variant="ghost" onClick={onExport}>
          <Download className="mr-1 h-3.5 w-3.5" />
          Export
        </Button>
      )}
    </div>
  )
}
