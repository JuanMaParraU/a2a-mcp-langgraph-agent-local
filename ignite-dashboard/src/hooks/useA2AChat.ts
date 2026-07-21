'use client';

import { useState, useCallback } from 'react';
import { fetchWithTimeout } from '@/lib/api';
import { A2AMessage } from '@/lib/types';

/**
 * Hook for sending messages to an A2A agent via POST /send_message.
 * Formats the message as an A2A protocol payload, handles a 120-second timeout,
 * and manages isPending state during the request.
 */
export function useA2AChat(agentUrl: string): {
  sendMessage: (text: string) => Promise<string>;
  isPending: boolean;
} {
  const [isPending, setIsPending] = useState(false);

  const sendMessage = useCallback(
    async (text: string): Promise<string> => {
      setIsPending(true);

      const messageId =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

      const payload: A2AMessage = {
        role: 'user',
        messageId,
        parts: [{ root: { text } }],
      };

      try {
        const response = await fetchWithTimeout(
          `${agentUrl}/send_message`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          },
          300000
        );

        if (!response.ok) {
          throw new Error(
            `Agent responded with status ${response.status}: ${response.statusText}`
          );
        }

        const data = await response.json();

        // Extract agent response text from the A2A response body
        const responseText =
          data?.parts?.[0]?.root?.text ??
          data?.content ??
          data?.message ??
          JSON.stringify(data);

        return responseText;
      } catch (error: unknown) {
        const message =
          error instanceof Error
            ? error.message
            : 'An unknown error occurred while sending the message';
        throw new Error(message);
      } finally {
        setIsPending(false);
      }
    },
    [agentUrl]
  );

  return { sendMessage, isPending };
}
