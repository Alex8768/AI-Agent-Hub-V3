import { MessageSquare, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface ChatsSectionProps {
  workspaceId: string
  sessionId: string
  lastUsedSession: string
}

export default function ChatsSection({ workspaceId, sessionId, lastUsedSession }: ChatsSectionProps) {
  return (
    <div className="space-y-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Chats</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button size="sm" className="w-full">
            <Plus className="mr-2 h-3.5 w-3.5" />
            New Chat
          </Button>
          <div className="rounded-md border bg-muted/40 p-2 text-xs">
            <div className="font-medium">Recent sessions</div>
            <div className="mt-1 text-muted-foreground">{lastUsedSession}</div>
            <div className="mt-2 text-muted-foreground">
              Current: {workspaceId}/{sessionId}
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <MessageSquare className="h-4 w-4" />
            Active Session
          </CardTitle>
        </CardHeader>
        <CardContent className="font-mono text-xs">
          {workspaceId}:{sessionId}
        </CardContent>
      </Card>
    </div>
  )
}
