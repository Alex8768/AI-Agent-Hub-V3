import { MessageSquare, History } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ChatHistoryProps {
  workspaceId: string
  sessionId: string
  lastUsedSession: string
}

export default function ChatHistory({ workspaceId, sessionId, lastUsedSession }: ChatHistoryProps) {
  return (
    <ScrollArea className="h-full">
      <div className="flex flex-col gap-3 p-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <MessageSquare className="h-4 w-4" />
              Current Session
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Workspace:</span>
              <span className="font-mono font-medium">{workspaceId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Session:</span>
              <span className="font-mono font-medium">{sessionId}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <History className="h-4 w-4" />
              Last Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border bg-muted/50 p-2 font-mono text-xs">
              {lastUsedSession}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Quick Tips</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            <ul className="list-inside list-disc space-y-1">
              <li>Upload documents to search</li>
              <li>Use tools for file operations</li>
              <li>Session persists your context</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  )
}
