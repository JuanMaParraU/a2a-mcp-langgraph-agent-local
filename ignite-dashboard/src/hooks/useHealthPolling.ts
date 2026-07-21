'use client';

import { useEffect } from 'react';
import { AgentConfig } from '@/lib/types';
import { fetchWithTimeout } from '@/lib/api';
import { useHealthStore } from '@/stores/healthStore';
import { AGENT_NODES } from '@/lib/config';

/**
 * Polls agent health endpoints at a configurable interval.
 * Sets status to "online" on HTTP 200 with valid JSON within 5 seconds,
 * "offline" otherwise. Updates healthStore on each poll cycle.
 */
export function useHealthPolling(
  agents: AgentConfig[] = AGENT_NODES,
  intervalMs: number = 10000
): void {
  useEffect(() => {
    async function checkAgent(agent: AgentConfig): Promise<void> {
      const url = agent.url + agent.healthEndpoint;

      try {
        // Don't follow redirects for health checks — a redirect means the server is alive
        const fetchOptions: RequestInit = agent.type === 'mcp' ? { redirect: 'manual' } : undefined as unknown as RequestInit;
        const response = await fetchWithTimeout(url, fetchOptions, 5000);

        if (response.ok) {
          try {
            const card = await response.json();
            useHealthStore.getState().setAgentStatus(agent.id, 'online', card);
          } catch {
            // Response was 200 but body is not valid JSON — still online (e.g., MCP server)
            useHealthStore.getState().setAgentStatus(agent.id, 'online');
          }
        } else if (response.status < 500 || response.type === 'opaqueredirect') {
          // 3xx or 4xx — server is reachable (e.g., MCP returns 307 redirect)
          useHealthStore.getState().setAgentStatus(agent.id, 'online');
        } else {
          useHealthStore.getState().setAgentStatus(agent.id, 'offline');
        }
      } catch {
        // Network error or timeout
        useHealthStore.getState().setAgentStatus(agent.id, 'offline');
      }
    }

    async function pollAll(): Promise<void> {
      await Promise.allSettled(agents.map((agent) => checkAgent(agent)));
    }

    // Immediately perform first health check
    pollAll();

    // Set up interval for subsequent checks
    const intervalId = setInterval(pollAll, intervalMs);

    // Clean up interval on unmount
    return () => {
      clearInterval(intervalId);
    };
  }, [agents, intervalMs]);
}
