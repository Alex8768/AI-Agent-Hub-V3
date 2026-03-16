import type { ReactNode } from 'react'
interface RightSidebarProps {
  children: ReactNode
}

export default function RightSidebar({ children }: RightSidebarProps) {
  return (
    <div className="h-full min-h-0">{children}</div>
  )
}
