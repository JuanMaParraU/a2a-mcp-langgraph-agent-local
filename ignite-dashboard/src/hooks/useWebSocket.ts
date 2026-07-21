'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { AgentEvent } from '@/lib/types';

interface UseWebSocketOptions {
  url: string;
  onMessage: (event: AgentEvent) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number; // default 5000ms
}

/**
 * Custom hook for WebSocket connections with auto-reconnect.
 * Connects to the given URL, parses incoming JSON messages as AgentEvent,
 * and automatically reconnects every `reconnectInterval` ms on disconnect.
 */
function useWebSocket(options: UseWebSocketOptions): { isConnected: boolean } {
  const { url, onMessage, onConnect, onDisconnect, reconnectInterval = 5000 } = options;

  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // Use refs for callbacks to avoid re-triggering the effect on callback changes
  const onMessageRef = useRef(onMessage);
  const onConnectRef = useRef(onConnect);
  const onDisconnectRef = useRef(onDisconnect);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    onConnectRef.current = onConnect;
  }, [onConnect]);

  useEffect(() => {
    onDisconnectRef.current = onDisconnect;
  }, [onDisconnect]);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    // Clean up any existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setIsConnected(true);
      onConnectRef.current?.();
    };

    ws.onmessage = (messageEvent: MessageEvent) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(messageEvent.data) as AgentEvent;
        onMessageRef.current(data);
      } catch {
        // Silently ignore malformed JSON messages
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setIsConnected(false);
      onDisconnectRef.current?.();
      // Schedule reconnect
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, reconnectInterval);
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      // The close event will fire after error, triggering reconnect
      ws.close();
    };
  }, [url, reconnectInterval]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;

      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      // Close WebSocket connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { isConnected };
}

export { useWebSocket };
export type { UseWebSocketOptions };
