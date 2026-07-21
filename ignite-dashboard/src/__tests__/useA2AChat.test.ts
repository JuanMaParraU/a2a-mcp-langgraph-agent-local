import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useA2AChat } from '@/hooks/useA2AChat';

// Mock the fetchWithTimeout function
vi.mock('@/lib/api', () => ({
  fetchWithTimeout: vi.fn(),
}));

import { fetchWithTimeout } from '@/lib/api';

const mockFetchWithTimeout = vi.mocked(fetchWithTimeout);

describe('useA2AChat', () => {
  const agentUrl = 'http://localhost:9990';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('initial state', () => {
    it('should have isPending set to false initially', () => {
      const { result } = renderHook(() => useA2AChat(agentUrl));
      expect(result.current.isPending).toBe(false);
    });

    it('should expose a sendMessage function', () => {
      const { result } = renderHook(() => useA2AChat(agentUrl));
      expect(typeof result.current.sendMessage).toBe('function');
    });
  });

  describe('sendMessage', () => {
    it('should send a POST request to agentUrl/send_message with A2A payload', async () => {
      mockFetchWithTimeout.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ parts: [{ root: { text: 'Agent response' } }] }),
      } as unknown as Response);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      await act(async () => {
        await result.current.sendMessage('Hello agent');
      });

      expect(mockFetchWithTimeout).toHaveBeenCalledTimes(1);
      const [url, options, timeout] = mockFetchWithTimeout.mock.calls[0];
      expect(url).toBe('http://localhost:9990/send_message');
      expect(timeout).toBe(120000);
      expect(options?.method).toBe('POST');
      expect(options?.headers).toEqual({ 'Content-Type': 'application/json' });

      const body = JSON.parse(options?.body as string);
      expect(body.role).toBe('user');
      expect(body.messageId).toBeDefined();
      expect(body.parts).toHaveLength(1);
      expect(body.parts[0].root.text).toBe('Hello agent');
    });

    it('should return the agent response text from parts[0].root.text', async () => {
      mockFetchWithTimeout.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ parts: [{ root: { text: 'Hello from agent' } }] }),
      } as unknown as Response);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      let responseText: string = '';
      await act(async () => {
        responseText = await result.current.sendMessage('Hi');
      });

      expect(responseText).toBe('Hello from agent');
    });

    it('should fall back to data.content if parts are not present', async () => {
      mockFetchWithTimeout.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ content: 'Fallback content' }),
      } as unknown as Response);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      let responseText: string = '';
      await act(async () => {
        responseText = await result.current.sendMessage('Hi');
      });

      expect(responseText).toBe('Fallback content');
    });

    it('should fall back to data.message if parts and content are not present', async () => {
      mockFetchWithTimeout.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Message fallback' }),
      } as unknown as Response);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      let responseText: string = '';
      await act(async () => {
        responseText = await result.current.sendMessage('Hi');
      });

      expect(responseText).toBe('Message fallback');
    });

    it('should JSON.stringify the response if no known fields are present', async () => {
      mockFetchWithTimeout.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ unknown: 'data' }),
      } as unknown as Response);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      let responseText: string = '';
      await act(async () => {
        responseText = await result.current.sendMessage('Hi');
      });

      expect(responseText).toBe(JSON.stringify({ unknown: 'data' }));
    });

    it('should set isPending to true during request and false after', async () => {
      let resolvePromise: (value: Response) => void;
      const pendingPromise = new Promise<Response>((resolve) => {
        resolvePromise = resolve;
      });
      mockFetchWithTimeout.mockReturnValueOnce(pendingPromise);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      expect(result.current.isPending).toBe(false);

      let sendPromise: Promise<string>;
      act(() => {
        sendPromise = result.current.sendMessage('Hello');
      });

      // isPending should be true while waiting
      expect(result.current.isPending).toBe(true);

      // Resolve the fetch
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => ({ parts: [{ root: { text: 'Done' } }] }),
        } as unknown as Response);
        await sendPromise;
      });

      expect(result.current.isPending).toBe(false);
    });

    it('should throw an error on non-200 response', async () => {
      mockFetchWithTimeout.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as unknown as Response);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      await act(async () => {
        await expect(result.current.sendMessage('Hi')).rejects.toThrow(
          'Agent responded with status 500: Internal Server Error'
        );
      });

      expect(result.current.isPending).toBe(false);
    });

    it('should throw an error on timeout', async () => {
      mockFetchWithTimeout.mockRejectedValueOnce(
        new Error('Request to http://localhost:9990/send_message timed out after 120000ms')
      );

      const { result } = renderHook(() => useA2AChat(agentUrl));

      await act(async () => {
        await expect(result.current.sendMessage('Hi')).rejects.toThrow(
          'Request to http://localhost:9990/send_message timed out after 120000ms'
        );
      });

      expect(result.current.isPending).toBe(false);
    });

    it('should throw an error on network failure', async () => {
      mockFetchWithTimeout.mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useA2AChat(agentUrl));

      await act(async () => {
        await expect(result.current.sendMessage('Hi')).rejects.toThrow('Network error');
      });

      expect(result.current.isPending).toBe(false);
    });

    it('should generate a unique messageId for each request', async () => {
      mockFetchWithTimeout.mockResolvedValue({
        ok: true,
        json: async () => ({ parts: [{ root: { text: 'Response' } }] }),
      } as unknown as Response);

      const { result } = renderHook(() => useA2AChat(agentUrl));

      await act(async () => {
        await result.current.sendMessage('First');
      });

      await act(async () => {
        await result.current.sendMessage('Second');
      });

      const firstBody = JSON.parse(mockFetchWithTimeout.mock.calls[0][1]?.body as string);
      const secondBody = JSON.parse(mockFetchWithTimeout.mock.calls[1][1]?.body as string);

      expect(firstBody.messageId).toBeDefined();
      expect(secondBody.messageId).toBeDefined();
      expect(firstBody.messageId).not.toBe(secondBody.messageId);
    });
  });
});
