import { Circle, PanelLeft, PanelRight } from 'lucide-react'
import SettingsHub from '../settings/SettingsHub'
import type { AppSettingsState, LayoutDensity } from '../settings/settingsTypes'
import { Button } from '@/components/ui/button'
import type { AppMode } from './layoutState'

type HealthState = 'checking' | 'healthy' | 'unreachable'

interface TopBarProps {
  productName: string
  workspaceTitle: string
  workspaceMeta: string
  settings: AppSettingsState
  onConnectionSettingsChange: (next: AppSettingsState['connection']) => void
  onBehaviorSettingsChange: (next: AppSettingsState['behavior']) => void
  onWorkspaceSettingsChange: (next: AppSettingsState['workspace']) => void
  density: LayoutDensity
  onDensityChange: (next: LayoutDensity) => void
  localeMode: 'auto' | 'en' | 'ru' | 'de' | 'fr'
  onLocaleModeChange: (next: 'auto' | 'en' | 'ru' | 'de' | 'fr') => void
  showReasoningSummaries: boolean
  onShowReasoningSummariesChange: (next: boolean) => void
  showExecutionEvents: boolean
  onShowExecutionEventsChange: (next: boolean) => void
  traceShortcutVisible: boolean
  onTraceShortcutVisibleChange: (next: boolean) => void
  healthStatus: HealthState
  appMode: AppMode
  onAppModeChange: (mode: AppMode) => void
  leftPanelOpen: boolean
  rightPanelOpen: boolean
  onToggleLeftPanel: () => void
  onToggleRightPanel: () => void
}

const modeOptions: Array<{ id: AppMode; label: string }> = [
  { id: 'chat', label: 'Chat' },
  { id: 'split', label: 'Split' },
  { id: 'canvas', label: 'Canvas' },
]

export default function TopBar({
  productName,
  workspaceTitle,
  workspaceMeta,
  settings,
  onConnectionSettingsChange,
  onBehaviorSettingsChange,
  onWorkspaceSettingsChange,
  density,
  onDensityChange,
  localeMode,
  onLocaleModeChange,
  showReasoningSummaries,
  onShowReasoningSummariesChange,
  showExecutionEvents,
  onShowExecutionEventsChange,
  traceShortcutVisible,
  onTraceShortcutVisibleChange,
  healthStatus,
  appMode,
  onAppModeChange,
  leftPanelOpen,
  rightPanelOpen,
  onToggleLeftPanel,
  onToggleRightPanel,
}: TopBarProps) {
  return (
    <header className="border-b bg-background/95 px-3 py-2 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="grid grid-cols-[auto_1fr_auto] items-center gap-3">
        <div className="flex items-center gap-2">
          <Button
            type="button"
            size="icon"
            variant={leftPanelOpen ? 'secondary' : 'ghost'}
            className="h-9 w-9"
            aria-pressed={leftPanelOpen}
            onClick={onToggleLeftPanel}
            aria-label={leftPanelOpen ? 'Close left panel' : 'Open left panel'}
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
          <span className="hidden text-xs text-muted-foreground lg:inline">{productName}</span>
        </div>

        <div className="min-w-0 px-1">
          <div className="flex items-center justify-center gap-3">
            <div className="min-w-0 text-center">
              <div className="truncate text-sm font-medium">{workspaceTitle}</div>
              <div className="truncate text-[11px] text-muted-foreground">{workspaceMeta}</div>
            </div>
            <div className="flex items-center gap-1 rounded-md border bg-muted/20 p-1">
              {modeOptions.map((option) => (
                <Button
                  key={option.id}
                  type="button"
                  size="sm"
                  variant={appMode === option.id ? 'default' : 'ghost'}
                  className="h-8 px-3"
                  onClick={() => onAppModeChange(option.id)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2">
          <SettingsHub
            settings={settings}
            onConnectionSettingsChange={onConnectionSettingsChange}
            onBehaviorSettingsChange={onBehaviorSettingsChange}
            onWorkspaceSettingsChange={onWorkspaceSettingsChange}
            density={density}
            onDensityChange={onDensityChange}
            localeMode={localeMode}
            onLocaleModeChange={onLocaleModeChange}
            showReasoningSummaries={showReasoningSummaries}
            onShowReasoningSummariesChange={onShowReasoningSummariesChange}
            showExecutionEvents={showExecutionEvents}
            onShowExecutionEventsChange={onShowExecutionEventsChange}
            traceShortcutVisible={traceShortcutVisible}
            onTraceShortcutVisibleChange={onTraceShortcutVisibleChange}
          />
          <span
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border text-muted-foreground"
            aria-label={healthStatus === 'healthy' ? 'Backend connected' : healthStatus === 'checking' ? 'Backend checking' : 'Backend offline'}
            title={healthStatus === 'healthy' ? 'Connected' : healthStatus === 'checking' ? 'Checking' : 'Offline'}
          >
            <Circle
              className={`h-3.5 w-3.5 ${
                healthStatus === 'healthy'
                  ? 'fill-emerald-500 text-emerald-500'
                  : healthStatus === 'checking'
                    ? 'fill-amber-500 text-amber-500'
                    : 'fill-destructive text-destructive'
              }`}
            />
          </span>
          <Button
            type="button"
            size="icon"
            variant={rightPanelOpen ? 'secondary' : 'ghost'}
            className="h-9 w-9"
            aria-pressed={rightPanelOpen}
            onClick={onToggleRightPanel}
            aria-label={rightPanelOpen ? 'Close right panel' : 'Open right panel'}
          >
            <PanelRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
