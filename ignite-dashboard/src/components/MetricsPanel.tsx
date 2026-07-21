'use client';

import React from 'react';
import { useMetricsStore } from '@/stores/metricsStore';
import { useHealthStore } from '@/stores/healthStore';
import { Panel } from '@/components/ui/Panel';
import { Gauge } from '@/components/ui/Gauge';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

/**
 * MetricsPanel - Displays server metrics with gauge indicators and time-series charts.
 *
 * Layout:
 * 1. Header with panel title and model name
 * 2. "Metrics Unavailable" overlay when endpoint is unreachable
 * 3. Gauges row: Total Requests, Total Tokens, Tool Calls, Active Agents
 * 4. Charts: Tokens/Second line chart, Latency chart (avg, P50, P95, P99)
 */
export function MetricsPanel() {
  const metricsStore = useMetricsStore();
  const healthStore = useHealthStore();

  const modelName = metricsStore.modelName || 'No Model Detected';
  const isAvailable = metricsStore.isAvailable;

  // Gauge values
  const totalRequests = metricsStore.current?.requests_total ?? 0;
  const totalTokens = metricsStore.current?.tokens_total ?? 0;
  const toolCalls = metricsStore.current?.tool_calls ?? 0;
  const activeAgents = healthStore.activeCount;

  // Time-series data for charts
  const timeSeries = metricsStore.timeSeries;

  return (
    <Panel className="flex flex-col gap-4 relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Server Metrics</h2>
        <span className="text-sm font-mono text-gray-400">{modelName}</span>
      </div>

      {/* Metrics Unavailable overlay */}
      {!isAvailable && (
        <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-10 rounded-lg">
          <span className="text-amber-400 font-semibold text-sm px-3 py-1 border border-amber-400/50 rounded bg-black/80">
            Metrics Unavailable
          </span>
        </div>
      )}

      {/* Gauges row */}
      <div className="grid grid-cols-4 gap-2">
        <Gauge value={totalRequests} label="Total Requests" color="#00d4ff" />
        <Gauge value={totalTokens} label="Total Tokens" color="#00ff88" />
        <Gauge value={toolCalls} label="Tool Calls" color="#ffaa00" />
        <Gauge value={activeAgents} label="Active Agents" color="#00d4ff" />
      </div>

      {/* Tokens/Second chart */}
      <div className="flex flex-col gap-1">
        <h3 className="text-xs text-gray-400 font-semibold">Tokens / Second</h3>
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="timestamp"
                tick={false}
                stroke="rgba(255,255,255,0.3)"
              />
              <YAxis
                stroke="rgba(255,255,255,0.3)"
                tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a2e',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '12px',
                }}
              />
              <Line
                type="monotone"
                dataKey="tokensPerSecond"
                stroke="#00d4ff"
                strokeWidth={2}
                dot={false}
                name="Tokens/s"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Latency chart */}
      <div className="flex flex-col gap-1">
        <h3 className="text-xs text-gray-400 font-semibold">Latency (seconds)</h3>
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis
                dataKey="timestamp"
                tick={false}
                stroke="rgba(255,255,255,0.3)"
              />
              <YAxis
                stroke="rgba(255,255,255,0.3)"
                tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a2e',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '12px',
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: '10px', color: '#9ca3af' }}
              />
              <Line
                type="monotone"
                dataKey="avgLatency"
                stroke="#00d4ff"
                strokeWidth={2}
                dot={false}
                name="Average Latency"
              />
              <Line
                type="monotone"
                dataKey="p50Latency"
                stroke="#00ff88"
                strokeWidth={1.5}
                dot={false}
                name="P50"
              />
              <Line
                type="monotone"
                dataKey="p95Latency"
                stroke="#ffaa00"
                strokeWidth={1.5}
                dot={false}
                name="P95"
              />
              <Line
                type="monotone"
                dataKey="p99Latency"
                stroke="#ff4444"
                strokeWidth={1.5}
                dot={false}
                name="P99"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Panel>
  );
}
