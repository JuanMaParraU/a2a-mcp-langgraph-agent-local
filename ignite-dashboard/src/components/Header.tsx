'use client';

import React from 'react';
import { useHealthStore } from '@/stores/healthStore';
import { useMetricsStore } from '@/stores/metricsStore';
import { StatusBadge } from '@/components/ui/StatusBadge';

/**
 * Dashboard Header - Displays global system status summary.
 * Shows title, subtitle, active agent count, MCP tools count,
 * global status badge, and live telemetry indicator.
 */
export function Header() {
  const { activeCount, totalCount, globalStatus } = useHealthStore();
  const { current, isAvailable } = useMetricsStore();

  const toolsCount = current?.tools_used?.length ?? 0;

  return (
    <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 px-6 py-4 bg-card border-b border-white/10">
      {/* Title section */}
      <div>
        <h1 className="text-2xl font-bold text-accent-cyan">
          IGNITE - Intelligent Service Orchestration
        </h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Multi-Agent Orchestration Platform
        </p>
      </div>

      {/* Stats section */}
      <div className="flex items-center gap-4 flex-wrap">
        <span className="text-sm font-mono text-gray-300">
          {activeCount}/{totalCount} Agents
        </span>
        <span className="text-sm font-mono text-gray-300">
          {toolsCount} Tools
        </span>
        <StatusBadge status={globalStatus} />
        {isAvailable && (
          <span className="text-sm font-semibold text-accent-green">
            Live Telemetry
          </span>
        )}
      </div>
    </header>
  );
}
