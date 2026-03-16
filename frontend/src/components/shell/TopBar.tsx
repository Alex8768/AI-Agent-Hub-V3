import Header from '../Header'
import type { AgentSettings } from '../SettingsDialog'
import type { AppMode } from './layoutState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

type HealthState = 'checking' | 'healthy' | 'unreachable'

interface TopBarProps {
  title: string
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
  settings,
  onSettingsChange,
  localeMode,
  onLocaleModeChange,
  healthStatus,
  appMode,
  onAppModeChange,
}: TopBarProps) {
  return (
    <div className="border-b">
      <Header
        title={title}
        settings={settings}
        onSettingsChange={onSettingsChange}
        localeMode={localeMode}
        onLocaleModeChange={onLocaleModeChange}
      />
      <div className="flex items-center justify-between gap-3 px-4 py-2">
        <div className="flex items-center gap-2">
          {modeOptions.map((option) => (
            <Button
              key={option.id}
              type="button"
              size="sm"
              variant={appMode === option.id ? 'default' : 'outline'}
              onClick={() => onAppModeChange(option.id)}
            >
              {option.label}
            </Button>
          ))}
        </div>
        <Badge variant={healthStatus === 'healthy' ? 'secondary' : 'destructive'}>
          {healthStatus === 'healthy' ? 'Connected' : healthStatus === 'checking' ? 'Checking' : 'Offline'}
        </Badge>
      </div>
    </div>
  )
}
