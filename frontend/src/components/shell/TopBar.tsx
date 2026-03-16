import SettingsDialog, { type AgentSettings } from '../SettingsDialog'
import { ModeToggle } from '@/components/ui/ModeToggle'
import type { AppMode } from './layoutState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

type HealthState = 'checking' | 'healthy' | 'unreachable'

interface TopBarProps {
  title: string
  workspaceId: string
  sessionId: string
  settings: AgentSettings
  onSettingsChange: (next: AgentSettings) => void
  localeMode: 'auto' | 'en' | 'ru'
  onLocaleModeChange: (next: 'auto' | 'en' | 'ru') => void
  healthStatus: HealthState
  appMode: AppMode
  onAppModeChange: (mode: AppMode) => void
}

const modeOptions: Array<{ id: AppMode; label: string }> = [
  { id: 'chat', label: 'Chat' },
  { id: 'split', label: 'Split' },
  { id: 'canvas', label: 'Canvas' },
]

export default function TopBar({
  title,
  workspaceId,
  sessionId,
  settings,
  onSettingsChange,
  localeMode,
  onLocaleModeChange,
  healthStatus,
  appMode,
  onAppModeChange,
}: TopBarProps) {
  return (
    <header className="border-b bg-background/95 px-4 py-2 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold tracking-tight">{title}</div>
          <div className="truncate text-xs text-muted-foreground">
            Workspace: {workspaceId} / Session: {sessionId}
          </div>
        </div>

        <div className="flex items-center gap-1 rounded-lg border bg-muted/30 p-1">
          {modeOptions.map((option) => (
            <Button
              key={option.id}
              type="button"
              size="sm"
              variant={appMode === option.id ? 'default' : 'outline'}
              className="h-8 px-3"
              onClick={() => onAppModeChange(option.id)}
            >
              {option.label}
            </Button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={healthStatus === 'healthy' ? 'secondary' : 'destructive'}>
            {healthStatus === 'healthy' ? 'Connected' : healthStatus === 'checking' ? 'Checking' : 'Offline'}
          </Badge>
          <ModeToggle />
          <SettingsDialog
            settings={settings}
            onChange={onSettingsChange}
            localeMode={localeMode}
            onLocaleModeChange={onLocaleModeChange}
            iconOnly
          />
        </div>
      </div>
    </header>
  )
}
