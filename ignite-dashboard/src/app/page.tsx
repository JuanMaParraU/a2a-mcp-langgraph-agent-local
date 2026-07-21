'use client';

import { useCallback } from 'react';
import { Header } from '@/components/Header';
import { TopologyPanel } from '@/components/TopologyPanel';
import { MetricsPanel } from '@/components/MetricsPanel';
import { ChatPanel } from '@/components/ChatPanel';
import { ActivityLogPanel } from '@/components/ActivityLogPanel';
import { useHealthPolling } from '@/hooks/useHealthPolling';
import { useMetricsPolling } from '@/hooks/useMetricsPolling';
import { useWebSocket } from '@/hooks/useWebSocket';
import { config, AGENT_NODES } from '@/lib/config';
import { useEventsStore } from '@/stores/eventsStore';
import { AgentEvent } from '@/lib/types';

/**
 * Main Dashboard Page
 *
 * Renders a 2x2 grid layout:
 *   - Top-left: Topology Panel
 *   - Top-right: Metrics Panel
 *   - Bottom-left: Chat Panel
 *   - Bottom-right: Activity Log Panel
 *
 * Below 1024px viewport width, panels stack vertically in order:
 *   Topology → Metrics → Chat → Activity Log
 *
 * All data-fetching hooks are wired here at the page level to ensure
 * polling and WebSocket connections are active for the entire dashboard lifetime.
 */
export default function DashboardPage() {
  // Wire health polling for all configured agents (10s interval)
  useHealthPolling(AGENT_NODES);

  // Wire metrics polling against the orchestrator (5s interval)
  useMetricsPolling(config.ORCHESTRATOR_URL);

  // Wire WebSocket for real-time activity events
  const addEvent = useEventsStore((state) => state.addEvent);
  const setConnected = useEventsStore((state) => state.setConnected);

  const handleMessage = useCallback(
    (event: AgentEvent) => {
      addEvent(event);
    },
    [addEvent]
  );

  const handleConnect = useCallback(() => {
    setConnected(true);
  }, [setConnected]);

  const handleDisconnect = useCallback(() => {
    setConnected(false);
  }, [setConnected]);

  const wsUrl = config.ORCHESTRATOR_URL.replace(/^http/, 'ws') + '/ws/events';

  useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    reconnectInterval: 5000,
  });

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header with global status */}
      <Header />

      {/* 2x2 Grid Layout - stacks vertically below 1024px */}
      <main className="flex-1 p-4 grid grid-cols-1 lg:grid-cols-2 grid-rows-[1fr_1fr] gap-4 min-h-0 overflow-hidden">
        {/* Top-left: Topology */}
        <section className="min-h-0 overflow-hidden">
          <TopologyPanel />
        </section>

        {/* Top-right: Metrics */}
        <section className="min-h-0 overflow-hidden">
          <MetricsPanel />
        </section>

        {/* Bottom-left: Chat */}
        <section className="min-h-0 overflow-hidden">
          <ChatPanel />
        </section>

        {/* Bottom-right: Activity Log */}
        <section className="min-h-0 overflow-hidden">
          <ActivityLogPanel />
        </section>
      </main>
    </div>
  );
}
