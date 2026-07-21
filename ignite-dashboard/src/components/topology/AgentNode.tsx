'use client';

import React from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { AgentStatus } from '@/lib/types';

interface AgentNodeData {
  name: string;
  port: number;
  status: AgentStatus;
  [key: string]: unknown;
}

const STATUS_COLORS: Record<AgentStatus, string> = {
  online: '#00ff88',
  offline: '#ff4444',
  checking: '#888888',
};

export function AgentNode({ data }: NodeProps) {
  const { name, port, status } = data as unknown as AgentNodeData;
  const statusColor = STATUS_COLORS[status] || STATUS_COLORS.checking;

  return (
    <div className="bg-card rounded-lg border border-white/20 px-4 py-3 min-w-[160px] shadow-lg">
      <Handle type="target" position={Position.Left} className="!bg-white/40" />
      <div className="flex items-center gap-2">
        <span
          className="inline-block w-3 h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: statusColor }}
          aria-label={`Status: ${status}`}
        />
        <div className="flex flex-col">
          <span className="text-sm font-medium text-white">{name}</span>
          <span className="text-xs text-white/60">:{port}</span>
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-white/40" />
    </div>
  );
}
