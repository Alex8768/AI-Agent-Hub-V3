import type { AppSettingsState } from '../settings/settingsTypes'
import type { AppMode } from './layoutState'

type HealthState = 'checking' | 'healthy' | 'unreachable'

interface BottomStatusBarProps {
  sessionId: string
  appMode: AppMode
  settings: AppSettingsState
  healthStatus: HealthState
  runtimeActive: boolean
  localeMode: 'auto' | 'en' | 'ru' | 'de' | 'fr'
}

function formatMode(mode: AppMode): string {
  if (mode === 'chat') return 'Chat'
  if (mode === 'split') return 'Split'
  return 'Canvas'
}

function formatBackend(healthStatus: HealthState): string {
  if (healthStatus === 'healthy') return 'Connected'
  if (healthStatus === 'checking') return 'Checking'
  return 'Offline'
}

export default function BottomStatusBar({
  sessionId,
  appMode,
  settings,
  healthStatus,
  runtimeActive,
  localeMode,
}: BottomStatusBarProps) {
  const model = settings.connection.model || 'default'
  const workspaceRoot = settings.workspace.workspaceRoot.trim()
  const workspaceLabel = workspaceRoot ? workspaceRoot.split('/').filter(Boolean).slice(-1)[0] : 'default'

  return (
    <footer className="border-t border-border/60 bg-background/80 px-3 py-1.5 text-[11px] text-muted-foreground">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <span>Session: {sessionId}</span>
        <span>Mode: {formatMode(appMode)}</span>
        <span>Model: {settings.connection.provider} / {model}</span>
        <span>Backend: {formatBackend(healthStatus)}</span>
        <span>Runtime: {runtimeActive ? 'Active' : 'Muted'}</span>
        <span>Workspace: {workspaceLabel}</span>
        <span>Language: {localeMode}</span>
      </div>
    </footer>
  )
}
