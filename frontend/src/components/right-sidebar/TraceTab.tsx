import type { AnswerResponseDto } from '../../contracts/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface TraceTabProps {
  lastAnswer: AnswerResponseDto | null
}

export default function TraceTab({ lastAnswer }: TraceTabProps) {
  const diagnosticsKeys = Object.keys((lastAnswer?.diagnostics ?? {}) as Record<string, unknown>)

  return (
    <div className="space-y-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Trace</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <div className="rounded-md border bg-muted/40 p-2">
            Diagnostics keys: {diagnosticsKeys.length}
          </div>
          <div className="rounded-md border bg-muted/40 p-2 text-muted-foreground">
            Detailed runtime event stream will be introduced in Patch 3.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
