import GraphCanvas from '../../GraphCanvas'

interface GraphCanvasViewProps {
  payload?: unknown
}

interface GraphNodeLike {
  id?: string
  name?: string
  type?: string
}

interface GraphEdgeLike {
  id?: string
  src_id?: string
  dst_id?: string
  source?: string
  target?: string
  rel_type?: string
}

interface GraphPayload {
  nodes?: GraphNodeLike[]
  edges?: GraphEdgeLike[]
}

export default function GraphCanvasView({ payload }: GraphCanvasViewProps) {
  const graphPayload = (payload as GraphPayload | undefined) ?? {}
  return <GraphCanvas nodes={graphPayload.nodes} edges={graphPayload.edges} />
}
