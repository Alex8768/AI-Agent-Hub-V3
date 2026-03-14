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

const GraphCanvas: React.FC<GraphCanvasProps> = ({ nodes = [], edges = [] }) => {
  const [flowNodes, setNodes, onNodesChange] = useNodesState([]);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const newNodes = nodes.map((node, idx) => ({
      id: node.id || `node-${idx}`,
      position: { x: Math.random() * 500, y: Math.random() * 300 },
      data: { label: node.name || node.id || `Node ${idx + 1}` },
      style: { background: node.type === 'seed' ? '#ffcc00' : '#fff' },
    }));
    const newEdges = edges.map((edge, idx) => ({
      id: edge.id || `edge-${idx}`,
      source: edge.src_id || edge.source || '',
      target: edge.dst_id || edge.target || '',
      label: edge.rel_type || '',
    }));
    setNodes(newNodes);
    setEdges(newEdges);
  }, [nodes, edges, setNodes, setEdges]);

  return (
    <div style={{ height: '100%', width: '100%' }}>
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
