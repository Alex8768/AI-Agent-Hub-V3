import type { AnswerResponseDto } from '../../contracts/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface ContextTabProps {
  lastAnswer: AnswerResponseDto | null
}

export default function ContextTab({ lastAnswer }: ContextTabProps) {
  const usedChunks = lastAnswer?.used_chunks ?? []
  const usedNodes = lastAnswer?.used_nodes ?? []
  const usedEdges = lastAnswer?.used_edges ?? []

  return (
    <div className="space-y-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Context</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <div className="rounded-md border bg-muted/40 p-2">Chunks: {usedChunks.length}</div>
          <div className="rounded-md border bg-muted/40 p-2">Nodes: {usedNodes.length}</div>
          <div className="rounded-md border bg-muted/40 p-2">Edges: {usedEdges.length}</div>
        </CardContent>
      </Card>
    </div>
  )
}
