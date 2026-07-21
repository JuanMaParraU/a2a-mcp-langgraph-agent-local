import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useHealthPolling } from '@/hooks/useHealthPolling';
import { useHealthStore } from '@/stores/healthStore';
import { AgentConfig } from '@/lib/types';

// Mock fetchWithTimeout
vi.mock('@/lib/api', () => ({
  fetchWithTimeout: vi.fn(),
}));

import { fetchWithTimeout } from '@/lib/api';

const mockFetch = vi.mocked(fetchWithTimeout);

const testAgents: AgentConfig[] = [
  {
    id: 'orchestrator',
    name: 'Orchestrator Agent',
    url: 'http://localhost:9990',
    port: 9990,
    type: 'orchestrator',
    healthEndpoint: '/.well-known/agent.json',
  },
  {
    id: 'mcp-server',
    name: 'MCP Server',
    url: 'http://localhost:8000',
    port: 8000,
    type: 'mcp',
    healthEndpoint: '/',
  },
];

describe('useHealthPolling', () => {
  beforeEach(() => {
    // Reset health store
    useHealthStore.setState({
      agents: {
        orchestrator: { agentId: 'orchestrator', status: 'checking', lastChecked: 0, agentCard: null },
        'mcp-server': { agentId: 'mcp-server', status: 'checking', lastChecked: 0, agentCard: null },
      },
      globalStatus: 'checking',
      activeCount: 0,
      totalCount: 2,
    });
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('performs an immediate health check on mount', async () => {
    const agentCard = { name: 'Orchestrator Agent', description: 'Test' };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(agentCard),
    } as unknown as Response);

    renderHook(() => useHealthPolling(testAgents, 10000));

    await waitFor(() => {
      const state = useHealthStore.getState();
      expect(state.agents['orchestrator'].status).toBe('online');
      expect(state.agents['mcp-server'].status).toBe('online');
    });
  });

  it('sets status to online on HTTP 200 with valid JSON and stores card', async () => {
    const card = { name: 'Orchestrator Agent', skills: [] };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(card),
    } as unknown as Response);

    renderHook(() => useHealthPolling(testAgents, 10000));

    await waitFor(() => {
      const state = useHealthStore.getState();
      expect(state.agents['orchestrator'].status).toBe('online');
      expect(state.agents['orchestrator'].agentCard).toEqual(card);
    });
  });

  it('sets status to offline on non-200 response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 503,
      json: () => Promise.resolve({}),
    } as unknown as Response);

    renderHook(() => useHealthPolling(testAgents, 10000));

    await waitFor(() => {
      const state = useHealthStore.getState();
      expect(state.agents['orchestrator'].status).toBe('offline');
      expect(state.agents['mcp-server'].status).toBe('offline');
    });
  });

  it('sets status to offline on network error/timeout', async () => {
    mockFetch.mockRejectedValue(new Error('Request timed out'));

    renderHook(() => useHealthPolling(testAgents, 10000));

    await waitFor(() => {
      const state = useHealthStore.getState();
      expect(state.agents['orchestrator'].status).toBe('offline');
      expect(state.agents['mcp-server'].status).toBe('offline');
    });
  });

  it('sets status to offline when response body is not valid JSON', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.reject(new SyntaxError('Unexpected token')),
    } as unknown as Response);

    renderHook(() => useHealthPolling(testAgents, 10000));

    await waitFor(() => {
      const state = useHealthStore.getState();
      expect(state.agents['orchestrator'].status).toBe('offline');
    });
  });

  it('polls at the specified interval', async () => {
    vi.useFakeTimers();
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ name: 'Agent' }),
    } as unknown as Response);

    renderHook(() => useHealthPolling(testAgents, 5000));

    // Flush the initial poll
    await vi.advanceTimersByTimeAsync(0);
    expect(mockFetch).toHaveBeenCalledTimes(2); // 2 agents

    // Advance by interval
    mockFetch.mockClear();
    await vi.advanceTimersByTimeAsync(5000);
    expect(mockFetch).toHaveBeenCalledTimes(2); // 2 agents polled again

    vi.useRealTimers();
  });

  it('cleans up interval on unmount', async () => {
    vi.useFakeTimers();
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ name: 'Agent' }),
    } as unknown as Response);

    const { unmount } = renderHook(() => useHealthPolling(testAgents, 10000));

    // Flush the initial poll
    await vi.advanceTimersByTimeAsync(0);

    mockFetch.mockClear();
    unmount();

    await vi.advanceTimersByTimeAsync(10000);
    expect(mockFetch).not.toHaveBeenCalled();

    vi.useRealTimers();
  });

  it('fetches the correct URL for each agent', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ name: 'Agent' }),
    } as unknown as Response);

    renderHook(() => useHealthPolling(testAgents, 10000));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:9990/.well-known/agent.json',
        undefined,
        5000
      );
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/',
        undefined,
        5000
      );
    });
  });
});
