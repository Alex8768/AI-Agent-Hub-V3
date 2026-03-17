import { useState } from 'react'
import { Settings2 } from 'lucide-react'
import { useTheme } from 'next-themes'
import type { AppSettingsState, LayoutDensity } from './settingsTypes'
import { getHealth } from '@/lib/apiClient'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface SettingsHubProps {
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
}

export default function SettingsHub({
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
}: SettingsHubProps) {
  const { theme, setTheme } = useTheme()
  const [connectionState, setConnectionState] = useState<'idle' | 'ok' | 'failed'>('idle')
  const [isTestingConnection, setIsTestingConnection] = useState(false)

  const testConnection = async () => {
    setIsTestingConnection(true)
    try {
      await getHealth()
      setConnectionState('ok')
    } catch {
      setConnectionState('failed')
    } finally {
      setIsTestingConnection(false)
    }
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="h-9 gap-1.5 px-3">
          <Settings2 className="h-4 w-4" />
          Settings
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Settings Hub</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="general" className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="appearance">Appearance</TabsTrigger>
            <TabsTrigger value="models">Models</TabsTrigger>
            <TabsTrigger value="behavior">Behavior</TabsTrigger>
            <TabsTrigger value="workspace">Workspace</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="space-y-4">
            <div className="space-y-2">
              <Label>Language</Label>
              <Select value={localeMode} onValueChange={(next) => onLocaleModeChange(next as SettingsHubProps['localeMode'])}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">System</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="ru">Русский</SelectItem>
                  <SelectItem value="de">Deutsch</SelectItem>
                  <SelectItem value="fr">Français</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-3 rounded-md border bg-muted/20 p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Reasoning summaries</p>
                  <p className="text-xs text-muted-foreground">Show short reasoning cards in runtime stream.</p>
                </div>
                <Switch checked={showReasoningSummaries} onCheckedChange={onShowReasoningSummariesChange} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Execution events</p>
                  <p className="text-xs text-muted-foreground">Show low-level execution event cards in chat.</p>
                </div>
                <Switch checked={showExecutionEvents} onCheckedChange={onShowExecutionEventsChange} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Trace shortcut</p>
                  <p className="text-xs text-muted-foreground">Show quick trace action in result toolbar.</p>
                </div>
                <Switch checked={traceShortcutVisible} onCheckedChange={onTraceShortcutVisibleChange} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="appearance" className="space-y-4">
            <div className="space-y-2">
              <Label>Theme</Label>
              <Select value={theme ?? 'system'} onValueChange={(next) => setTheme(next)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="system">System</SelectItem>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Density</Label>
              <Select value={density} onValueChange={(next) => onDensityChange(next as LayoutDensity)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="comfortable">Comfortable</SelectItem>
                  <SelectItem value="compact">Compact</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </TabsContent>

          <TabsContent value="models" className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select
                  value={settings.connection.provider}
                  onValueChange={(next) => onConnectionSettingsChange({ ...settings.connection, provider: next as AppSettingsState['connection']['provider'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="ollama">Ollama</SelectItem>
                    <SelectItem value="anthropic">Anthropic</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Model</Label>
                <Input
                  value={settings.connection.model}
                  onChange={(event) => onConnectionSettingsChange({ ...settings.connection, model: event.target.value })}
                  placeholder="gpt-4o-mini"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Endpoint</Label>
              <Input
                value={settings.connection.endpoint}
                onChange={(event) => onConnectionSettingsChange({ ...settings.connection, endpoint: event.target.value })}
                placeholder="http://localhost:8000"
              />
            </div>
            <div className="flex items-center justify-between rounded-md border bg-muted/20 p-3">
              <div className="text-sm">
                <p className="font-medium">Connection test</p>
                <p className="text-xs text-muted-foreground">Health: {connectionState === 'ok' ? 'Connected' : connectionState === 'failed' ? 'Offline' : 'Unknown'}</p>
              </div>
              <Button size="sm" variant="outline" disabled={isTestingConnection} onClick={testConnection}>
                {isTestingConnection ? 'Testing...' : 'Test'}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="behavior" className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Reasoning mode</Label>
                <Select
                  value={settings.behavior.reasoningMode}
                  onValueChange={(next) => onBehaviorSettingsChange({ ...settings.behavior, reasoningMode: next as AppSettingsState['behavior']['reasoningMode'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="deep">Deep</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Search behavior</Label>
                <Select
                  value={settings.behavior.searchBehavior}
                  onValueChange={(next) => onBehaviorSettingsChange({ ...settings.behavior, searchBehavior: next as AppSettingsState['behavior']['searchBehavior'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="force">Force search</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Approval strictness</Label>
                <Select
                  value={settings.behavior.approvalStrictness}
                  onValueChange={(next) => onBehaviorSettingsChange({ ...settings.behavior, approvalStrictness: next as AppSettingsState['behavior']['approvalStrictness'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="balanced">Balanced</SelectItem>
                    <SelectItem value="strict">Strict</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Execution detail</Label>
                <Select
                  value={settings.behavior.executionDetailLevel}
                  onValueChange={(next) => onBehaviorSettingsChange({ ...settings.behavior, executionDetailLevel: next as AppSettingsState['behavior']['executionDetailLevel'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="summary">Summary</SelectItem>
                    <SelectItem value="detailed">Detailed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-3 rounded-md border bg-muted/20 p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Auto-open trace</p>
                  <p className="text-xs text-muted-foreground">Open trace panel on trace-heavy responses.</p>
                </div>
                <Switch
                  checked={settings.behavior.autoOpenTrace}
                  onCheckedChange={(checked) => onBehaviorSettingsChange({ ...settings.behavior, autoOpenTrace: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Auto-open canvas</p>
                  <p className="text-xs text-muted-foreground">Auto-open canvas for result artifacts.</p>
                </div>
                <Switch
                  checked={settings.behavior.autoOpenCanvas}
                  onCheckedChange={(checked) => onBehaviorSettingsChange({ ...settings.behavior, autoOpenCanvas: checked })}
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="workspace" className="space-y-4">
            <div className="space-y-2">
              <Label>Workspace root</Label>
              <Input
                value={settings.workspace.workspaceRoot}
                onChange={(event) => onWorkspaceSettingsChange({ ...settings.workspace, workspaceRoot: event.target.value })}
                placeholder="/path/to/workspace"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>File policy</Label>
                <Select
                  value={settings.workspace.fileSafetyPolicy}
                  onValueChange={(next) => onWorkspaceSettingsChange({ ...settings.workspace, fileSafetyPolicy: next as AppSettingsState['workspace']['fileSafetyPolicy'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="confirm-writes">Confirm writes</SelectItem>
                    <SelectItem value="readonly-preferred">Readonly preferred</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Defaults profile</Label>
                <Select
                  value={settings.workspace.defaultsProfile}
                  onValueChange={(next) => onWorkspaceSettingsChange({ ...settings.workspace, defaultsProfile: next as AppSettingsState['workspace']['defaultsProfile'] })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default</SelectItem>
                    <SelectItem value="safe">Safe</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Session defaults</Label>
              <Select
                value={settings.workspace.sessionPreference}
                onValueChange={(next) => onWorkspaceSettingsChange({ ...settings.workspace, sessionPreference: next as AppSettingsState['workspace']['sessionPreference'] })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="project-scoped">Project scoped</SelectItem>
                  <SelectItem value="global">Global</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <p className="text-xs text-muted-foreground">
              Workspace options are currently UI-first preferences and are ready for deeper backend binding in a later patch.
            </p>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
