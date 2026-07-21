import { create } from 'zustand';
import { ChatMessage } from '@/lib/types';

const MAX_MESSAGES_PER_AGENT = 200;
const MAX_MESSAGE_LENGTH = 10000;

/**
 * Validates a chat message text input.
 * Returns true if the trimmed text length is between 1 and 10,000 characters (inclusive).
 * Returns false for empty strings, whitespace-only strings, or strings exceeding 10,000 chars after trimming.
 */
export function validateChatMessage(text: string): boolean {
  const trimmed = text.trim();
  return trimmed.length >= 1 && trimmed.length <= MAX_MESSAGE_LENGTH;
}

interface ChatStore {
  histories: Record<string, ChatMessage[]>;
  activeAgent: string;
  isPending: boolean;
  addMessage: (agentId: string, message: ChatMessage) => void;
  setActiveAgent: (agentId: string) => void;
  setPending: (pending: boolean) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  histories: {},
  activeAgent: 'orchestrator',
  isPending: false,

  addMessage: (agentId: string, message: ChatMessage) => {
    set((state) => {
      const existing = state.histories[agentId] || [];
      const updated = [...existing, message];

      // Enforce buffer limit: remove oldest if exceeding max
      if (updated.length > MAX_MESSAGES_PER_AGENT) {
        updated.shift();
      }

      return {
        histories: {
          ...state.histories,
          [agentId]: updated,
        },
      };
    });
  },

  setActiveAgent: (agentId: string) => {
    set({ activeAgent: agentId });
  },

  setPending: (pending: boolean) => {
    set({ isPending: pending });
  },
}));
