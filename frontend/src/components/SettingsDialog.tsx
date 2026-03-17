import { useMemo, useState } from 'react'
import { AlertTriangle, Settings2 } from 'lucide-react'
import type { LegacyAgentSettings } from './settings/settingsTypes'
import type { AppSettingsState } from './settings/settingsTypes'
import { DEFAULT_APP_SETTINGS, toLegacyAgentSettings } from './settings/settingsTypes'
import ConnectionModelModal from './settings/ConnectionModelModal'
import AgentBehaviorModal from './settings/AgentBehaviorModal'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

export type AgentSettings = LegacyAgentSettings

interface SettingsDialogProps {
  settings: AgentSettings
  onChange: (next: AgentSettings) => void
  localeMode: 'auto' | 'en' | 'ru'
  onLocaleModeChange: (next: 'auto' | 'en' | 'ru') => void
  iconOnly?: boolean
}

export default function SettingsDialog({
  settings,
  onChange,
  localeMode: _localeMode,
  onLocaleModeChange: _onLocaleModeChange,
  iconOnly = false
}: SettingsDialogProps) {
  void _localeMode
  void _onLocaleModeChange

  const [compat, setCompat] = useState<AppSettingsState>({
    ...DEFAULT_APP_SETTINGS,
    connection: {
      provider: (settings.apiProvider as AppSettingsState['connection']['provider']) || 'openai',
      model: settings.selectedModel,
      endpoint: settings.apiBaseUrl,
    },
    behavior: {
      ...DEFAULT_APP_SETTINGS.behavior,
      reasoningMode: settings.reasoningMode,
      searchBehavior: settings.forceSearch ? 'force' : 'normal',
      executionDetailLevel: settings.showReasoning ? 'detailed' : 'summary',
    },
  })

  const legacyView = useMemo(() => toLegacyAgentSettings(compat), [compat])

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size={iconOnly ? 'icon' : 'sm'} className={iconOnly ? 'h-8 w-8' : 'h-8 gap-1.5'}>
          <Settings2 className="h-4 w-4" />
          {!iconOnly && 'Legacy Settings'}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Compatibility Settings Adapter</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="rounded-md border border-amber-300/70 bg-amber-50/40 p-3 text-xs text-amber-900 dark:text-amber-200">
            <div className="mb-1 flex items-center gap-2 font-medium">
              <AlertTriangle className="h-4 w-4" />
              Deprecated wrapper
            </div>
            Main settings architecture now lives in top bar quick settings and dedicated modals.
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <ConnectionModelModal
              value={compat.connection}
              onChange={(next) => {
                const merged = { ...compat, connection: next }
                setCompat(merged)
                onChange(toLegacyAgentSettings(merged))
              }}
            />
            <AgentBehaviorModal
              value={compat.behavior}
              onChange={(next) => {
                const merged = { ...compat, behavior: next }
                setCompat(merged)
                onChange(toLegacyAgentSettings(merged))
              }}
            />
            <Badge variant="outline">Legacy map active</Badge>
          </div>
          <div className="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
            Legacy output: provider={legacyView.apiProvider}, model={legacyView.selectedModel || 'n/a'}, reasoning=
            {legacyView.reasoningMode}, forceSearch={String(legacyView.forceSearch)}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
