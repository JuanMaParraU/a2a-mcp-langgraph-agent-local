import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useMetricsPolling } from '@/hooks/useMetricsPolling';
import { useMetricsStore } from '@/stores/metricsStore';
import { MetricsSnapshot } from '@/lib/types';

// Mock fetchWithTimeout
vi.mock('@/lib/api', () => ({
  fetchWithTimeout: vi.fn(),
}));

import { fetchWithTimeout } from '@/lib/api';

const mockFetch = vi.mocked(fetchWithTimeout);

function createMockSnapshot(overrides?: Partial<MetricsSnapshot>): MetricsSnapshot {
  return {
    timestamp: '2024-01-15T10:30:00.000Z',
    model: 'qwen3:4b',
    requests_total: 42,
    errors_total: 1,
    inter_agent_messages: 15,
    tool_calls: 8,
    retrievals: 3,
    tokens_total: 12500,
    tokens_prompt: 8000,
    tokens_completion: 4500,
    submission_latencies: [0.5, 0.8, 1.2],
    task_durations: [2.1, 3.5],
    tools_used: ['duckduckgo_search', 'wikipedia_search'],
    ai_messages_count: 20,
    reasoning_steps: 18,
    avg_latency: 0.83,
    avg_task_duration: 2.8,
    tokens_per_request: 297.6,
    tools_per_request: 0.19,
    ...overrides,
  };
}

describe('useMetricsPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Reset the metrics store before each test
    useMetricsStore.setState({
      current: null,
      timeSeries: [],
      isAvailable: true,
      modelName: 'No Model Detected',
    });
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should perform an immediate fetch on mount', async () => {
    const snapshot = createMockSnapshot();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => snapshot,
    } as Response);

    renderHook(() => useMetricsPolling('http://localhost:9990'));

    // Flush the microtask queue for the immediate fetch
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(mockFetch).toHaveBeenCalledWith('http://localhost:9990/metrics', undefined, 5000);
    expect(useMetricsStore.getState().current).toEqual(snapshot);
    expect(useMetricsStore.getState().isAvailable).toBe(true);
  });

  it('should poll at the specified interval', async () => {
    const snapshot = createMockSnapshot();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => snapshot,
    } as Response);

    renderHook(() => useMetricsPolling('http://localhost:9990', 5000));

    // Initial fetch
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Advance by 5 seconds for next poll
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(mockFetch).toHaveBeenCalledTimes(2);

    // Advance by another 5 seconds
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('should call setUnavailable on non-200 response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ error: 'Service unavailable' }),
    } as Response);

    renderHook(() => useMetricsPolling('http://localhost:9990'));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(useMetricsStore.getState().isAvailable).toBe(false);
  });

  it('should call setUnavailable on network error', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'));

    renderHook(() => useMetricsPolling('http://localhost:9990'));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(useMetricsStore.getState().isAvailable).toBe(false);
  });

  it('should call setUnavailable on timeout', async () => {
    mockFetch.mockRejectedValue(
      new Error('Request to http://localhost:9990/metrics timed out after 5000ms')
    );

    renderHook(() => useMetricsPolling('http://localhost:9990'));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(useMetricsStore.getState().isAvailable).toBe(false);
  });

  it('should resume normal updates when endpoint becomes reachable again', async () => {
    const snapshot = createMockSnapshot();

    // First call fails
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    renderHook(() => useMetricsPolling('http://localhost:9990', 5000));

    // Initial fetch fails
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(useMetricsStore.getState().isAvailable).toBe(false);

    // Second call succeeds
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => snapshot,
    } as Response);

    // Next poll succeeds
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(useMetricsStore.getState().isAvailable).toBe(true);
    expect(useMetricsStore.getState().current).toEqual(snapshot);
  });

  it('should clean up interval on unmount', async () => {
    const snapshot = createMockSnapshot();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => snapshot,
    } as Response);

    const { unmount } = renderHook(() => useMetricsPolling('http://localhost:9990', 5000));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    unmount();

    // Advance time - no more calls should happen
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000);
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('should use default interval of 5000ms', async () => {
    const snapshot = createMockSnapshot();
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => snapshot,
    } as Response);

    renderHook(() => useMetricsPolling('http://localhost:9990'));

    // Initial fetch
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Should not fire at 4999ms
    await act(async () => {
      await vi.advanceTimersByTimeAsync(4999);
    });
    expect(mockFetch).toHaveBeenCalledTimes(1);

    // Should fire at 5000ms total
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
