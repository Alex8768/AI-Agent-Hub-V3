import { LayoutPanelTop } from 'lucide-react'
import type { AppMode } from '../shell/layoutState'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface ViewsSectionProps {
  appMode: AppMode
  onAppModeChange: (mode: AppMode) => void
}

const modeOptions: Array<{ id: AppMode; label: string }> = [
  { id: 'chat', label: 'Chat' },
  { id: 'split', label: 'Split' },
  { id: 'canvas', label: 'Canvas' },
]

export default function ViewsSection({ appMode, onAppModeChange }: ViewsSectionProps) {
  return (
    <div className="space-y-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <LayoutPanelTop className="h-4 w-4" />
            Views
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {modeOptions.map((option) => (
            <Button
              key={option.id}
              type="button"
              size="sm"
              className="w-full justify-start"
              variant={appMode === option.id ? 'default' : 'outline'}
              onClick={() => onAppModeChange(option.id)}
            >
              {option.label}
            </Button>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
