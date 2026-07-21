import { type Edge, MarkerType } from '@xyflow/react';
import { TOPOLOGY_EDGES } from '@/lib/config';

/**
 * Generate React Flow edge definitions from the static topology configuration.
 * Edges are animated with directional arrow markers and labeled with protocol type.
 */
export function getTopologyEdges(): Edge[] {
  return TOPOLOGY_EDGES.map((edge) => ({
    id: `${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target,
    animated: true,
    label: edge.label,
    labelStyle: { fill: '#ffffff', fontSize: 11, fontWeight: 500 },
    labelBgStyle: { fill: '#1a1a2e', fillOpacity: 0.8 },
    labelBgPadding: [6, 4] as [number, number],
    labelBgBorderRadius: 4,
    style: { stroke: '#ffffff40' },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#ffffff80',
    },
  }));
}
