'use client';

import React, { useMemo } from 'react';
import { ReactFlow, Background, Controls, type Node } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useHealthStore } from '@/stores/healthStore';
import { AGENT_NODES } from '@/lib/config';
import { Panel } from '@/components/ui/Panel';
import { AgentNode } from '@/components/topology/AgentNode';
import { getTopologyEdges } from '@/components/topology/edges';

// Static layout positions for each agent node
// Orchestrator is the central node with worker agents branching out
const NODE_POSITIONS: Record<string, { x: number; y: number }> = {
  orchestrator: { x: 50, y: 100 },
  'research-agent': { x: 300, y: 100 },
  'mcp-server': { x: 550, y: 100 },
};

// Register custom node types
const nodeTypes = { agentNode: AgentNode };

export function TopologyPanel() {
  const agents = useHealthStore((state) => state.agents);

  const nodes: Node[] = useMemo(
    () =>
      AGENT_NODES.map((agent) => ({
        id: agent.id,
        type: 'agentNode',
        position: NODE_POSITIONS[agent.id] || { x: 0, y: 0 },
        data: {
          name: agent.name,
          port: agent.port,
          status: agents[agent.id]?.status || 'checking',
        },
      })),
    [agents]
  );

  const edges = useMemo(() => getTopologyEdges(), []);

  return (
    <Panel className="h-full flex flex-col">
      <h2 className="text-sm font-semibold text-white/80 mb-2">System Topology</h2>
      <div className="flex-1 min-h-0">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
        >
          <Background color="#ffffff10" gap={20} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </Panel>
  );
}
