import type { ReactNode } from 'react'
import type { LeftSidebarSection } from './layoutState'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'

interface LeftSidebarProps {
  section: LeftSidebarSection
  onSectionChange: (section: LeftSidebarSection) => void
  sections: Record<LeftSidebarSection, ReactNode>
}

const sectionOptions: Array<{ id: LeftSidebarSection; label: string }> = [
  { id: 'chats', label: 'Chats' },
  { id: 'projects', label: 'Projects' },
  { id: 'views', label: 'Views' },
  { id: 'saved', label: 'Saved' },
]

export default function LeftSidebar({ section, onSectionChange, sections }: LeftSidebarProps) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b bg-background/70 p-2">
        <div className="grid grid-cols-2 gap-1">
          {sectionOptions.map((item) => (
            <Button
              key={item.id}
              type="button"
              size="sm"
              variant={section === item.id ? 'default' : 'ghost'}
              className="h-8 justify-start rounded-md text-xs"
              onClick={() => onSectionChange(item.id)}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </div>
      <div className="min-h-0 flex-1 bg-background/30">
        <ScrollArea className="h-full">{sections[section]}</ScrollArea>
      </div>
    </div>
  )
}
