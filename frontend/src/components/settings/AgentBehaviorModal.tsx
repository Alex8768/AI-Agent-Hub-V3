import { SlidersHorizontal } from 'lucide-react'
import type { AgentBehaviorSettings } from './settingsTypes'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'

interface AgentBehaviorModalProps {
  value: AgentBehaviorSettings
  onChange: (next: AgentBehaviorSettings) => void
}

export default function AgentBehaviorModal({ value, onChange }: AgentBehaviorModalProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="h-8 gap-1.5">
          <SlidersHorizontal className="h-4 w-4" />
          Behavior
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Agent Behavior</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Reasoning mode</Label>
            <Select
              value={value.reasoningMode}
              onValueChange={(next) => onChange({ ...value, reasoningMode: next as AgentBehaviorSettings['reasoningMode'] })}
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
              value={value.searchBehavior}
              onValueChange={(next) => onChange({ ...value, searchBehavior: next as AgentBehaviorSettings['searchBehavior'] })}
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
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Approval strictness</Label>
              <Select
                value={value.approvalStrictness}
                onValueChange={(next) => onChange({ ...value, approvalStrictness: next as AgentBehaviorSettings['approvalStrictness'] })}
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
                value={value.executionDetailLevel}
                onValueChange={(next) => onChange({ ...value, executionDetailLevel: next as AgentBehaviorSettings['executionDetailLevel'] })}
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
          <div className="space-y-3 rounded-md border bg-muted/30 p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Auto-open trace</p>
                <p className="text-xs text-muted-foreground">Open trace panel after runtime updates</p>
              </div>
              <Switch
                checked={value.autoOpenTrace}
                onCheckedChange={(checked) => onChange({ ...value, autoOpenTrace: checked })}
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Auto-open canvas</p>
                <p className="text-xs text-muted-foreground">Open canvas for result artifacts when available</p>
              </div>
              <Switch
                checked={value.autoOpenCanvas}
                onCheckedChange={(checked) => onChange({ ...value, autoOpenCanvas: checked })}
              />
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
