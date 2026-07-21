'use client';

import React from 'react';
import type { GlobalStatus, AgentStatus } from '@/lib/types';

interface StatusBadgeProps {
  status: GlobalStatus | AgentStatus;
}

const STATUS_CONFIG: Record<
  GlobalStatus | AgentStatus,
  { label: string; color: string; bgColor: string }
> = {
  online: {
    label: 'ONLINE',
    color: 'text-accent-green',
    bgColor: 'bg-accent-green/20',
  },
  offline: {
    label: 'OFFLINE',
    color: 'text-accent-red',
    bgColor: 'bg-accent-red/20',
  },
  degraded: {
    label: 'DEGRADED',
    color: 'text-accent-amber',
    bgColor: 'bg-accent-amber/20',
  },
  checking: {
    label: 'CHECKING',
    color: 'text-gray-400',
    bgColor: 'bg-gray-400/20',
  },
};

/**
 * StatusBadge - Displays a colored pill badge for agent/global status.
 * Maps status values to appropriate colors and labels.
 */
export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${config.bgColor} ${config.color}`}
    >
      {config.label}
    </span>
  );
}
