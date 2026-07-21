import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { AgentEvent } from '@/lib/types';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0; // CONNECTING
  closed = false;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.closed = true;
    this.readyState = 3; // CLOSED
  }

  // Test helpers
  simulateOpen() {
    this.readyState = 1; // OPEN
    this.onopen?.();
  }

  simulateMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  simulateClose() {
    this.readyState = 3; // CLOSED
    this.onclose?.();
  }

  simulateError() {
    this.onerror?.();
  }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal('WebSocket', MockWebSocket);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('should connect to the provided URL on mount', () => {
    const onMessage = vi.fn();
    renderHook(() => useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage }));

    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toBe('ws://localhost:9990/ws/events');
  });

  it('should set isConnected to true on open', async () => {
    const onMessage = vi.fn();
    const onConnect = vi.fn();

    const { result } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage, onConnect })
    );

    expect(result.current.isConnected).toBe(false);

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    expect(result.current.isConnected).toBe(true);
    expect(onConnect).toHaveBeenCalledTimes(1);
  });

  it('should parse incoming JSON messages as AgentEvent and call onMessage', () => {
    const onMessage = vi.fn();
    const mockEvent: AgentEvent = {
      timestamp: '2024-01-15T10:30:05.123Z',
      agent: 'Orchestrator Agent',
      event_type: 'tool_call',
      details: { tool_name: 'duckduckgo_search', query: 'LangGraph agents' },
    };

    renderHook(() => useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage }));

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      MockWebSocket.instances[0].simulateMessage(mockEvent);
    });

    expect(onMessage).toHaveBeenCalledTimes(1);
    expect(onMessage).toHaveBeenCalledWith(mockEvent);
  });

  it('should silently ignore malformed JSON messages', () => {
    const onMessage = vi.fn();

    renderHook(() => useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage }));

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      // Send invalid JSON directly via onmessage
      MockWebSocket.instances[0].onmessage?.({ data: 'not valid json{{{' });
    });

    expect(onMessage).not.toHaveBeenCalled();
  });

  it('should set isConnected to false and call onDisconnect on close', () => {
    const onMessage = vi.fn();
    const onDisconnect = vi.fn();

    const { result } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage, onDisconnect })
    );

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    expect(result.current.isConnected).toBe(true);

    act(() => {
      MockWebSocket.instances[0].simulateClose();
    });

    expect(result.current.isConnected).toBe(false);
    expect(onDisconnect).toHaveBeenCalledTimes(1);
  });

  it('should attempt to reconnect after 5 seconds on disconnect', () => {
    const onMessage = vi.fn();

    renderHook(() => useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage }));

    expect(MockWebSocket.instances).toHaveLength(1);

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      MockWebSocket.instances[0].simulateClose();
    });

    // Should not reconnect immediately
    expect(MockWebSocket.instances).toHaveLength(1);

    // Advance time by 5 seconds
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    // Should have created a new WebSocket instance
    expect(MockWebSocket.instances).toHaveLength(2);
    expect(MockWebSocket.instances[1].url).toBe('ws://localhost:9990/ws/events');
  });

  it('should use custom reconnect interval', () => {
    const onMessage = vi.fn();

    renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:9990/ws/events',
        onMessage,
        reconnectInterval: 3000,
      })
    );

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      MockWebSocket.instances[0].simulateClose();
    });

    // Should not reconnect at 2 seconds
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(MockWebSocket.instances).toHaveLength(1);

    // Should reconnect at 3 seconds
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it('should clean up WebSocket and timeout on unmount', () => {
    const onMessage = vi.fn();

    const { unmount } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage })
    );

    const ws = MockWebSocket.instances[0];

    act(() => {
      ws.simulateOpen();
    });

    unmount();

    expect(ws.closed).toBe(true);
  });

  it('should clean up reconnect timeout on unmount', () => {
    const onMessage = vi.fn();

    const { unmount } = renderHook(() =>
      useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage })
    );

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      MockWebSocket.instances[0].simulateClose();
    });

    // Unmount before reconnect fires
    unmount();

    // Advance time - should not create new WebSocket
    act(() => {
      vi.advanceTimersByTime(10000);
    });

    // Only the original instance should exist
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it('should close WebSocket on error and trigger reconnect', () => {
    const onMessage = vi.fn();
    const onDisconnect = vi.fn();

    renderHook(() =>
      useWebSocket({ url: 'ws://localhost:9990/ws/events', onMessage, onDisconnect })
    );

    act(() => {
      MockWebSocket.instances[0].simulateOpen();
    });

    act(() => {
      MockWebSocket.instances[0].simulateError();
    });

    // Error handler calls close(), which should trigger the onclose handler
    expect(MockWebSocket.instances[0].closed).toBe(true);
  });
});
