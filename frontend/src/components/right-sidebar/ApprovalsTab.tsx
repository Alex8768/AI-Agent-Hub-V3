import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function ApprovalsTab() {
  return (
    <div className="space-y-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Approvals</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <Badge variant="outline">No pending approvals</Badge>
          <div className="rounded-md border bg-muted/40 p-2 text-muted-foreground">
            Inline approval cards in chat stream will be delivered in Patch 3.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
