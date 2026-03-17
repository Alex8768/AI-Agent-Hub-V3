import { Settings2 } from 'lucide-react'
import { useTheme } from 'next-themes'
import type { LayoutDensity } from './settingsTypes'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface QuickSettingsPopoverProps {
  density: LayoutDensity
  onDensityChange: (next: LayoutDensity) => void
  showReasoningSummaries: boolean
  onShowReasoningSummariesChange: (next: boolean) => void
  showExecutionEvents: boolean
  onShowExecutionEventsChange: (next: boolean) => void
  traceShortcutVisible: boolean
  onTraceShortcutVisibleChange: (next: boolean) => void
}

export default function QuickSettingsPopover({
  density,
  onDensityChange,
  showReasoningSummaries,
  onShowReasoningSummariesChange,
  showExecutionEvents,
  onShowExecutionEventsChange,
  traceShortcutVisible,
  onTraceShortcutVisibleChange,
}: QuickSettingsPopoverProps) {
  const { theme, setTheme } = useTheme()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" className="h-8 w-8" aria-label="Quick settings">
          <Settings2 className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>Quick Settings</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground">Theme</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => setTheme('light')}>
          {theme === 'light' ? '✓ ' : ''}Light
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          {theme === 'dark' ? '✓ ' : ''}Dark
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          {theme === 'system' ? '✓ ' : ''}System
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground">Density</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => onDensityChange('comfortable')}>
          {density === 'comfortable' ? '✓ ' : ''}Comfortable
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => onDensityChange('compact')}>
          {density === 'compact' ? '✓ ' : ''}Compact
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuCheckboxItem
          checked={showReasoningSummaries}
          onCheckedChange={(checked) => onShowReasoningSummariesChange(Boolean(checked))}
        >
          Show reasoning summaries
        </DropdownMenuCheckboxItem>
        <DropdownMenuCheckboxItem
          checked={showExecutionEvents}
          onCheckedChange={(checked) => onShowExecutionEventsChange(Boolean(checked))}
        >
          Show execution events
        </DropdownMenuCheckboxItem>
        <DropdownMenuCheckboxItem
          checked={traceShortcutVisible}
          onCheckedChange={(checked) => onTraceShortcutVisibleChange(Boolean(checked))}
        >
          Trace shortcut in runtime
        </DropdownMenuCheckboxItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
