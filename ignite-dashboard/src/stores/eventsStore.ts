import { create } from 'zustand';
import { AgentEvent } from '@/lib/types';

const MAX_EVENTS = 500;

/**
 * Maps event_type values to human-readable display labels.
 * Returns "Unknown" for any unrecognized event type.
 */
export function getEventTypeLabel(eventType: string): string {
  switch (eventType) {
    case 'request':
      return 'Request';
    case 'tool_call':
      return 'Tool Call';
    case 'token_usage':
      return 'Token Usage';
    case 'heartbeat':
      return 'Heartbeat';
    case 'inter_agent_message':
      return 'A2A Message';
    case 'error':
      return 'Error';
    default:
      return 'Unknown';
  }
}

interface EventsStore {
  events: AgentEvent[];
  filter: string;
  isConnected: boolean;
  addEvent: (event: AgentEvent) => void;
  setFilter: (filter: string) => void;
  setConnected: (connected: boolean) => void;
  getFilteredEvents: () => AgentEvent[];
}

export const useEventsStore = create<EventsStore>((set, get) => ({
  events: [],
  filter: 'all',
  isConnected: false,

  addEvent: (event: AgentEvent) => {
    set((state) => {
      const newEvents = [event, ...state.events];
      if (newEvents.length > MAX_EVENTS) {
        newEvents.pop();
      }
      return { events: newEvents };
    });
  },

  setFilter: (filter: string) => {
    set({ filter });
  },

  setConnected: (connected: boolean) => {
    set({ isConnected: connected });
  },

  getFilteredEvents: () => {
    const { events, filter } = get();
    if (filter === 'all') {
      return events;
    }
    return events.filter((event) => event.event_type === filter);
  },
}));
