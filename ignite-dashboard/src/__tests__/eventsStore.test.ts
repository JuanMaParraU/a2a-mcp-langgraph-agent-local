import { describe, it, expect, beforeEach } from 'vitest';
import { useEventsStore, getEventTypeLabel } from '@/stores/eventsStore';
import { AgentEvent } from '@/lib/types';

function createEvent(overrides: Partial<AgentEvent> = {}): AgentEvent {
  return {
    timestamp: new Date().toISOString(),
    agent: 'Orchestrator Agent',
    event_type: 'request',
    details: {},
    ...overrides,
  };
}

describe('eventsStore', () => {
  beforeEach(() => {
    useEventsStore.setState({ events: [], filter: 'all', isConnected: false });
  });

  describe('addEvent', () => {
    it('prepends new events (newest first)', () => {
      const event1 = createEvent({ timestamp: '2024-01-01T00:00:01.000Z' });
      const event2 = createEvent({ timestamp: '2024-01-01T00:00:02.000Z' });

      useEventsStore.getState().addEvent(event1);
      useEventsStore.getState().addEvent(event2);

      const events = useEventsStore.getState().events;
      expect(events[0]).toBe(event2);
      expect(events[1]).toBe(event1);
    });

    it('enforces max 500 events buffer limit', () => {
      // Add 500 events
      for (let i = 0; i < 500; i++) {
        useEventsStore.getState().addEvent(createEvent({ timestamp: `2024-01-01T00:00:${String(i).padStart(2, '0')}.000Z` }));
      }
      expect(useEventsStore.getState().events.length).toBe(500);

      // Add one more - should still be 500
      const newestEvent = createEvent({ timestamp: '2024-01-01T01:00:00.000Z' });
      useEventsStore.getState().addEvent(newestEvent);

      const events = useEventsStore.getState().events;
      expect(events.length).toBe(500);
      expect(events[0]).toBe(newestEvent);
    });

    it('removes the oldest event when buffer overflows', () => {
      // Fill buffer
      for (let i = 0; i < 500; i++) {
        useEventsStore.getState().addEvent(createEvent({ agent: `agent-${i}` }));
      }

      // The oldest event is agent-0 (at the end since we prepend)
      const eventsBeforeOverflow = useEventsStore.getState().events;
      expect(eventsBeforeOverflow[499].agent).toBe('agent-0');

      // Add one more
      useEventsStore.getState().addEvent(createEvent({ agent: 'agent-new' }));

      const eventsAfterOverflow = useEventsStore.getState().events;
      expect(eventsAfterOverflow.length).toBe(500);
      expect(eventsAfterOverflow[0].agent).toBe('agent-new');
      // agent-0 should be gone
      expect(eventsAfterOverflow[499].agent).toBe('agent-1');
    });
  });

  describe('setFilter', () => {
    it('sets the filter value', () => {
      useEventsStore.getState().setFilter('tool_call');
      expect(useEventsStore.getState().filter).toBe('tool_call');
    });

    it('can set filter to all', () => {
      useEventsStore.getState().setFilter('tool_call');
      useEventsStore.getState().setFilter('all');
      expect(useEventsStore.getState().filter).toBe('all');
    });
  });

  describe('getFilteredEvents', () => {
    it('returns all events when filter is "all"', () => {
      useEventsStore.getState().addEvent(createEvent({ event_type: 'request' }));
      useEventsStore.getState().addEvent(createEvent({ event_type: 'tool_call' }));
      useEventsStore.getState().addEvent(createEvent({ event_type: 'error' }));

      const filtered = useEventsStore.getState().getFilteredEvents();
      expect(filtered.length).toBe(3);
    });

    it('filters events by event_type', () => {
      useEventsStore.getState().addEvent(createEvent({ event_type: 'request' }));
      useEventsStore.getState().addEvent(createEvent({ event_type: 'tool_call' }));
      useEventsStore.getState().addEvent(createEvent({ event_type: 'request' }));

      useEventsStore.getState().setFilter('request');
      const filtered = useEventsStore.getState().getFilteredEvents();
      expect(filtered.length).toBe(2);
      expect(filtered.every((e) => e.event_type === 'request')).toBe(true);
    });

    it('returns empty array when no events match filter', () => {
      useEventsStore.getState().addEvent(createEvent({ event_type: 'request' }));
      useEventsStore.getState().setFilter('error');
      const filtered = useEventsStore.getState().getFilteredEvents();
      expect(filtered.length).toBe(0);
    });
  });

  describe('setConnected', () => {
    it('sets isConnected to true', () => {
      useEventsStore.getState().setConnected(true);
      expect(useEventsStore.getState().isConnected).toBe(true);
    });

    it('sets isConnected to false', () => {
      useEventsStore.getState().setConnected(true);
      useEventsStore.getState().setConnected(false);
      expect(useEventsStore.getState().isConnected).toBe(false);
    });
  });

  describe('initial state', () => {
    it('starts with empty events array', () => {
      expect(useEventsStore.getState().events).toEqual([]);
    });

    it('starts with filter set to "all"', () => {
      expect(useEventsStore.getState().filter).toBe('all');
    });

    it('starts with isConnected false', () => {
      expect(useEventsStore.getState().isConnected).toBe(false);
    });
  });
});

describe('getEventTypeLabel', () => {
  it('maps "request" to "Request"', () => {
    expect(getEventTypeLabel('request')).toBe('Request');
  });

  it('maps "tool_call" to "Tool Call"', () => {
    expect(getEventTypeLabel('tool_call')).toBe('Tool Call');
  });

  it('maps "token_usage" to "Token Usage"', () => {
    expect(getEventTypeLabel('token_usage')).toBe('Token Usage');
  });

  it('maps "heartbeat" to "Heartbeat"', () => {
    expect(getEventTypeLabel('heartbeat')).toBe('Heartbeat');
  });

  it('maps "inter_agent_message" to "A2A Message"', () => {
    expect(getEventTypeLabel('inter_agent_message')).toBe('A2A Message');
  });

  it('maps "error" to "Error"', () => {
    expect(getEventTypeLabel('error')).toBe('Error');
  });

  it('maps unrecognized types to "Unknown"', () => {
    expect(getEventTypeLabel('unknown_type')).toBe('Unknown');
    expect(getEventTypeLabel('')).toBe('Unknown');
    expect(getEventTypeLabel('foo_bar')).toBe('Unknown');
  });
});
