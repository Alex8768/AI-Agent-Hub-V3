import { useState } from 'react'
import { PlugZap } from 'lucide-react'
import type { ConnectionModelSettings } from './settingsTypes'
import { getHealth } from '@/lib/apiClient'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

type HealthState = 'idle' | 'ok' | 'failed'

interface ConnectionModelModalProps {
  value: ConnectionModelSettings
  onChange: (next: ConnectionModelSettings) => void
}

export default function ConnectionModelModal({ value, onChange }: ConnectionModelModalProps) {
  const [healthState, setHealthState] = useState<HealthState>('idle')
  const [checking, setChecking] = useState(false)

  const testConnection = async () => {
    setChecking(true)
    try {
      await getHealth()
      setHealthState('ok')
    } catch {
      setHealthState('failed')
    } finally {
      setChecking(false)
    }
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="h-8 gap-1.5">
          <PlugZap className="h-4 w-4" />
          Model
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Model / Connection</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Provider</Label>
              <Select value={value.provider} onValueChange={(next) => onChange({ ...value, provider: next as ConnectionModelSettings['provider'] })}>
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
                value={value.model}
                onChange={(event) => onChange({ ...value, model: event.target.value })}
                placeholder="gpt-4o-mini"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Endpoint</Label>
            <Input
              value={value.endpoint}
              onChange={(event) => onChange({ ...value, endpoint: event.target.value })}
              placeholder="http://localhost:8000"
            />
          </div>
          <div className="flex items-center justify-between rounded-md border bg-muted/30 p-3">
            <div className="text-sm">
              <div className="font-medium">Backend status</div>
              <div className="text-xs text-muted-foreground">Use connection test to verify API availability.</div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={healthState === 'ok' ? 'secondary' : healthState === 'failed' ? 'destructive' : 'outline'}>
                {healthState === 'ok' ? 'Connected' : healthState === 'failed' ? 'Offline' : 'Unknown'}
              </Badge>
              <Button size="sm" variant="outline" onClick={testConnection} disabled={checking}>
                {checking ? 'Testing...' : 'Test connection'}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
