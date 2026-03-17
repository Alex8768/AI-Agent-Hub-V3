import SettingsDialog, { type AgentSettings } from './SettingsDialog'
import { ModeToggle } from '@/components/ui/ModeToggle'

interface HeaderProps {
  title: string
  settings: AgentSettings
  onSettingsChange: (next: AgentSettings) => void
  localeMode: 'auto' | 'en' | 'ru'
  onLocaleModeChange: (next: 'auto' | 'en' | 'ru') => void
}

export default function Header({
  title,
  settings,
  onSettingsChange,
  localeMode,
  onLocaleModeChange,
}: HeaderProps) {
  return (
    <header className="flex h-12 items-center justify-between border-b border-muted/50 bg-background/80 px-4 backdrop-blur-md">
      <div className="text-sm font-semibold tracking-tight">{title}</div>
      <div className="flex items-center gap-2">
        <ModeToggle />
        <SettingsDialog
          settings={settings}
          onChange={onSettingsChange}
          localeMode={localeMode}
          onLocaleModeChange={onLocaleModeChange}
          iconOnly
        />
      </div>
    </header>
  )
}
