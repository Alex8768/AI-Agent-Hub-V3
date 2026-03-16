import type { ReactNode } from 'react'
import type { RightSidebarTab } from './layoutState'
import { Badge } from '@/components/ui/badge'

interface RightSidebarProps {
  activeTab: RightSidebarTab
  children: ReactNode
}

export default function RightSidebar({ activeTab, children }: RightSidebarProps) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b px-3 py-2">
        <Badge variant="outline">Right: {activeTab}</Badge>
      </div>
      <div className="min-h-0 flex-1">{children}</div>
    </div>
  )
}
