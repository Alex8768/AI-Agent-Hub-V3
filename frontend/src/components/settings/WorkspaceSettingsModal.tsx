import { FolderCog } from 'lucide-react'
import type { WorkspaceSettingsState } from './settingsTypes'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface WorkspaceSettingsModalProps {
  value: WorkspaceSettingsState
  onChange: (next: WorkspaceSettingsState) => void
}

export default function WorkspaceSettingsModal({ value, onChange }: WorkspaceSettingsModalProps) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="h-8 gap-1.5">
          <FolderCog className="h-4 w-4" />
          Workspace
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Workspace Settings</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Workspace root</Label>
            <Input
              value={value.workspaceRoot}
              onChange={(event) => onChange({ ...value, workspaceRoot: event.target.value })}
              placeholder="/path/to/workspace"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>File safety policy</Label>
              <Select
                value={value.fileSafetyPolicy}
                onValueChange={(next) => onChange({ ...value, fileSafetyPolicy: next as WorkspaceSettingsState['fileSafetyPolicy'] })}
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
                value={value.defaultsProfile}
                onValueChange={(next) => onChange({ ...value, defaultsProfile: next as WorkspaceSettingsState['defaultsProfile'] })}
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
            <Label>Session / project preference</Label>
            <Select
              value={value.sessionPreference}
              onValueChange={(next) => onChange({ ...value, sessionPreference: next as WorkspaceSettingsState['sessionPreference'] })}
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
          <div className="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
            <Badge variant="outline" className="mb-2">Adapter</Badge>
            Some workspace options currently act as UI preferences only and are ready for deeper backend integration later.
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
