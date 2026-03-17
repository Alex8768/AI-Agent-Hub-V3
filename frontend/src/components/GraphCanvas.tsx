import React, { useEffect } from 'react';
import ReactFlow, { Background, Controls, MiniMap, useEdgesState, useNodesState } from 'reactflow';
import 'reactflow/dist/style.css';

interface GraphNodeLike {
  id?: string;
  name?: string;
  type?: string;
}

interface GraphEdgeLike {
  id?: string;
  src_id?: string;
  dst_id?: string;
  source?: string;
  target?: string;
  rel_type?: string;
}

interface GraphCanvasProps {
  nodes?: GraphNodeLike[];
  edges?: GraphEdgeLike[];
}

const HORIZONTAL_GAP = 260;
const VERTICAL_GAP = 120;
const FALLBACK_COLUMNS = 4;

function normalizeNodeId(node: GraphNodeLike, idx: number): string {
  return String(node.id || `node-${idx}`);
}

function normalizeEdgeSource(edge: GraphEdgeLike): string {
  return String(edge.src_id || edge.source || '');
}

function normalizeEdgeTarget(edge: GraphEdgeLike): string {
  return String(edge.dst_id || edge.target || '');
}

function buildNodeLevels(nodeIds: string[], edges: Array<{ source: string; target: string }>): Map<string, number> {
  const levels = new Map<string, number>();
  const inbound = new Map<string, number>();
  const outgoing = new Map<string, string[]>();

  nodeIds.forEach((id) => {
    inbound.set(id, 0);
    outgoing.set(id, []);
  });

  edges.forEach(({ source, target }) => {
    if (!inbound.has(source) || !inbound.has(target)) return;
    outboundPush(outgoing, source, target);
    inbound.set(target, (inbound.get(target) || 0) + 1);
  });

  const queue: string[] = nodeIds
    .filter((id) => (inbound.get(id) || 0) === 0)
    .sort((a, b) => a.localeCompare(b));

  queue.forEach((id) => levels.set(id, 0));

  while (queue.length > 0) {
    const current = queue.shift() as string;
    const currentLevel = levels.get(current) || 0;
    const nextIds = (outgoing.get(current) || []).slice().sort((a, b) => a.localeCompare(b));
    nextIds.forEach((nextId) => {
      const proposed = currentLevel + 1;
      levels.set(nextId, Math.max(levels.get(nextId) || 0, proposed));
      inbound.set(nextId, (inbound.get(nextId) || 1) - 1);
      if ((inbound.get(nextId) || 0) <= 0) queue.push(nextId);
    });
  }

  // If cycle/no roots exists, keep layout deterministic using sorted fallback columns.
  const unresolved = nodeIds.filter((id) => !levels.has(id)).sort((a, b) => a.localeCompare(b));
  unresolved.forEach((id, idx) => {
    const level = Math.floor(idx / FALLBACK_COLUMNS);
    levels.set(id, level);
  });

  return levels;
}

function outboundPush(outgoing: Map<string, string[]>, source: string, target: string): void {
  const current = outgoing.get(source) || [];
  current.push(target);
  outgoing.set(source, current);
}

const GraphCanvas: React.FC<GraphCanvasProps> = ({ nodes = [], edges = [] }) => {
  const [flowNodes, setNodes, onNodesChange] = useNodesState([]);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState([]);
  const isEmpty = nodes.length === 0;

  useEffect(() => {
    const normalizedNodeIds = nodes.map(normalizeNodeId);
    const normalizedEdges = edges
      .map((edge, idx) => ({
        id: String(edge.id || `edge-${idx}`),
        source: normalizeEdgeSource(edge),
        target: normalizeEdgeTarget(edge),
        label: String(edge.rel_type || ''),
      }))
      .filter((edge) => edge.source.length > 0 && edge.target.length > 0);

    const levelByNode = buildNodeLevels(
      normalizedNodeIds,
      normalizedEdges.map((edge) => ({ source: edge.source, target: edge.target })),
    );
    const rowsByLevel = new Map<number, string[]>();
    normalizedNodeIds
      .slice()
      .sort((a, b) => a.localeCompare(b))
      .forEach((id) => {
        const level = levelByNode.get(id) || 0;
        const bucket = rowsByLevel.get(level) || [];
        bucket.push(id);
        rowsByLevel.set(level, bucket);
      });

    const newNodes = nodes.map((node, idx) => {
      const id = normalizeNodeId(node, idx);
      const level = levelByNode.get(id) || 0;
      const row = (rowsByLevel.get(level) || []).indexOf(id);
      const isSeed = String(node.type || '').toLowerCase() === 'seed';
      return {
        id,
        position: { x: level * HORIZONTAL_GAP, y: row * VERTICAL_GAP },
        data: { label: node.name || node.id || `Node ${idx + 1}` },
        style: isSeed
          ? { background: '#ffef99', border: '2px solid #e0b000', fontWeight: 600 }
          : { background: '#fff', border: '1px solid #d5d5d5' },
      };
    });

    const newEdges = normalizedEdges;
    setNodes(newNodes);
    setEdges(newEdges);
  }, [nodes, edges, setNodes, setEdges]);

  return (
    <div className="relative h-full w-full bg-background">
      {isEmpty && (
        <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-xs rounded-md border bg-card/90 p-3 shadow-sm">
          <h3 className="text-sm font-semibold">Canvas is ready</h3>
          <p className="mt-1 text-xs text-muted-foreground">Send a query that returns graph data to populate nodes and edges.</p>
        </div>
      )}
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};

export default GraphCanvas;
