'use client';

import { useEffect } from 'react';
import { fetchWithTimeout } from '@/lib/api';
import { useMetricsStore } from '@/stores/metricsStore';
import { MetricsSnapshot } from '@/lib/types';

/**
 * Polls the /metrics endpoint at a configurable interval and feeds
 * snapshots into the metrics store. Marks the endpoint as unavailable
 * on failure and resumes normal updates when it becomes reachable again.
 */
export function useMetricsPolling(url: string, intervalMs: number = 5000): void {
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;

    async function fetchMetrics() {
      try {
        const response = await fetchWithTimeout(`${url}/metrics`, undefined, 5000);

        if (response.ok) {
          const snapshot: MetricsSnapshot = await response.json();
          useMetricsStore.getState().addSnapshot(snapshot);
          useMetricsStore.getState().setAvailable();
        } else {
          useMetricsStore.getState().setUnavailable();
        }
      } catch {
        useMetricsStore.getState().setUnavailable();
      }
    }

    // Immediately perform first fetch on mount
    fetchMetrics();

    // Set up polling interval
    intervalId = setInterval(fetchMetrics, intervalMs);

    // Clean up on unmount
    return () => {
      if (intervalId !== null) {
        clearInterval(intervalId);
      }
    };
  }, [url, intervalMs]);
}
