'use client';

import React from 'react';
import { useEventsStore, getEventTypeLabel } from '@/stores/eventsStore';
import { formatTimestamp } from '@/lib/utils';
import { Panel } from '@/components/ui/Panel';
import { AgentEvent } from '@/lib/types';

/**
 * Extracts a human-readable details string from an AgentEvent based on its type.
 */
function getEventDetails(event: AgentEvent): string {
  const { event_type, details } = event;

  switch (event_type) {
    case 'token_usage': {
      const prompt = details.prompt_tokens ?? 0;
      const completion = details.completion_tokens ?? 0;
      const total = details.total_tokens ?? 0;
      return `Prompt: ${prompt}, Completion: ${completion}, Total: ${total}`;
    }
    case 'tool_call': {
      const toolName = details.tool_name ?? 'unknown';
      return `Tool: ${toolName}`;
    }
    case 'inter_agent_message': {
      const target = details.target_agent ?? 'unknown';
      return `Target: ${target}`;
    }
    case 'error': {
      return String(details.error_text ?? details.message ?? 'Unknown error');
    }
    case 'request': {
      if (details.method && details.path) {
        return `${details.method} ${details.path}`;
      }
      return JSON.stringify(details);
    }
    case 'heartbeat':
      return '—';
    default:
      return JSON.stringify(details);
  }
}

const EVENT_FILTER_OPTIONS = [
  { value: 'all', label: 'All Events' },
  { value: 'request', label: 'Request' },
  { value: 'tool_call', label: 'Tool Call' },
  { value: 'token_usage', label: 'Token Usage' },
  { value: 'heartbeat', label: 'Heartbeat' },
  { value: 'inter_agent_message', label: 'A2A Message' },
  { value: 'error', label: 'Error' },
];

/**
 * ActivityLogPanel - Displays a real-time scrollable event table
 * with filtering by event type and connection status indicator.
 */
export function ActivityLogPanel() {
  const { filter, isConnected, setFilter, getFilteredEvents } = useEventsStore();
  const filteredEvents = getFilteredEvents();

  return (
    <Panel className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-white">Activity Log</h2>
          {!isConnected && (
            <span className="px-2 py-0.5 text-xs font-medium rounded bg-red-500/20 text-red-400 border border-red-500/30">
              Disconnected
            </span>
          )}
        </div>

        {/* Filter dropdown */}
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="text-xs bg-white/5 border border-white/20 rounded px-2 py-1 text-white/80 focus:outline-none focus:border-cyan-400"
        >
          {EVENT_FILTER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value} className="bg-card text-white">
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Scrollable table */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-card">
            <tr className="text-white/50 border-b border-white/10">
              <th className="text-left py-1.5 px-2 font-medium">Timestamp</th>
              <th className="text-left py-1.5 px-2 font-medium">Agent</th>
              <th className="text-left py-1.5 px-2 font-medium">Event Type</th>
              <th className="text-left py-1.5 px-2 font-medium">Details</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-8 text-white/30">
                  {isConnected ? 'No events yet' : 'Waiting for connection...'}
                </td>
              </tr>
            ) : (
              filteredEvents.map((event, index) => (
                <tr
                  key={`${event.timestamp}-${index}`}
                  className="border-b border-white/5 hover:bg-white/5"
                >
                  <td className="py-1.5 px-2 font-mono text-white/70 whitespace-nowrap">
                    {formatTimestamp(event.timestamp)}
                  </td>
                  <td className="py-1.5 px-2 text-white/80 whitespace-nowrap">
                    {event.agent}
                  </td>
                  <td className="py-1.5 px-2 whitespace-nowrap">
                    <EventTypeBadge eventType={event.event_type} />
                  </td>
                  <td className="py-1.5 px-2 font-mono text-white/60 truncate max-w-[200px]">
                    {getEventDetails(event)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

/**
 * Small colored badge for event type display.
 */
function EventTypeBadge({ eventType }: { eventType: string }) {
  const label = getEventTypeLabel(eventType);

  const colorClass = (() => {
    switch (eventType) {
      case 'error':
        return 'text-red-400 bg-red-500/10';
      case 'token_usage':
        return 'text-cyan-400 bg-cyan-500/10';
      case 'tool_call':
        return 'text-green-400 bg-green-500/10';
      case 'inter_agent_message':
        return 'text-amber-400 bg-amber-500/10';
      case 'heartbeat':
        return 'text-white/40 bg-white/5';
      case 'request':
        return 'text-purple-400 bg-purple-500/10';
      default:
        return 'text-white/50 bg-white/5';
    }
  })();

  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${colorClass}`}>
      {label}
    </span>
  );
}
