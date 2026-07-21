# Implementation Plan: IGNITE Frontend Dashboard

## Overview

Build a standalone Next.js TypeScript dashboard application that provides real-time monitoring, visualization, and interaction capabilities for the A2A + MCP + LangGraph multi-agent system. The implementation follows an incremental approach: project scaffolding → shared utilities and state → individual panels → integration and wiring.

## Tasks

- [x] 1. Project scaffolding and core infrastructure
  - [x] 1.1 Initialize Next.js project with TypeScript, Tailwind CSS, and package.json
    - Bootstrap Next.js app with App Router and TypeScript
    - Configure Tailwind CSS with dark theme colors (#0a0a0f background, #1a1a2e cards, accent colors: cyan #00d4ff, green #00ff88, red #ff4444, amber #ffaa00)
    - Create package.json with exact dependency versions (no ^ or ~), engines field >=18.0.0
    - Add dependencies: react-flow, recharts, zustand, fast-check, vitest, @testing-library/react, msw
    - Create .env.local.example with NEXT_PUBLIC_ORCHESTRATOR_URL, NEXT_PUBLIC_RESEARCH_AGENT_URL, NEXT_PUBLIC_MCP_SERVER_URL
    - Create README.md with setup instructions, env var documentation, and dev commands
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 1.6, 1.7_

  - [x] 1.2 Create shared TypeScript interfaces and configuration module
    - Create `src/lib/types.ts` with all interfaces: AgentConfig, AgentStatus, GlobalStatus, AgentHealthState, MetricsSnapshot, TimeSeriesPoint, AgentEvent, ChatMessage, A2AMessage
    - Create `src/lib/config.ts` with environment variable resolution (defaults: localhost:9990, :9991, :8000) and console warning for missing variables
    - Create `src/lib/utils.ts` with formatting helpers (timestamp HH:mm:ss.SSS, percentile computation, tokens-per-second calculation)
    - Create `src/lib/api.ts` with HTTP client utilities (fetch with timeout, error handling)
    - _Requirements: 1.2, 1.3, 3.2_

  - [x]* 1.3 Write property test for environment variable resolution
    - **Property 1: Environment Variable Resolution**
    - **Validates: Requirements 1.2**

- [x] 2. State management stores
  - [x] 2.1 Implement health store with Zustand
    - Create `src/stores/healthStore.ts` with agent status tracking
    - Implement `setAgentStatus`, `getGlobalStatus` actions
    - Derive globalStatus: "online" (all online), "degraded" (mixed), "offline" (all offline), "checking" (initial)
    - Derive activeCount and totalCount from agent states
    - _Requirements: 2.3, 2.4, 2.8, 6.3, 6.5, 6.6, 6.7, 6.10_

  - [x]* 2.2 Write property test for global status badge derivation
    - **Property 17: Global Status Badge Derivation**
    - **Validates: Requirements 6.5, 6.6, 6.7**

  - [x]* 2.3 Write property test for active agent count
    - **Property 16: Active Agent Count**
    - **Validates: Requirements 6.3**

  - [x] 2.4 Implement metrics store with Zustand
    - Create `src/stores/metricsStore.ts` with time-series buffer (max 60 points)
    - Implement `addSnapshot` that computes derived TimeSeriesPoint (tokensPerSecond, percentiles)
    - Implement `setUnavailable`/`setAvailable` for connection state
    - Derive modelName with "No Model Detected" fallback
    - Enforce circular buffer: discard oldest when exceeding 60 items
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [x]* 2.5 Write property test for metrics time-series buffer invariant
    - **Property 6: Metrics Time-Series Buffer Invariant**
    - **Validates: Requirements 3.6**

  - [x]* 2.6 Write property test for derived metrics computation
    - **Property 5: Derived Metrics Computation**
    - **Validates: Requirements 3.2**

  - [x] 2.7 Implement events store with Zustand
    - Create `src/stores/eventsStore.ts` with event buffer (max 500, newest first)
    - Implement `addEvent` that prepends and enforces buffer limit
    - Implement `setFilter` and `getFilteredEvents` for event type filtering
    - Implement `setConnected` for WebSocket connection state
    - Map event types to display labels with "Unknown" fallback for unrecognized types
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x]* 2.8 Write property test for activity log buffer invariant
    - **Property 13: Activity Log Buffer Invariant**
    - **Validates: Requirements 5.5**

  - [x]* 2.9 Write property test for event ordering
    - **Property 14: Event Ordering**
    - **Validates: Requirements 5.6**

  - [x]* 2.10 Write property test for event type categorization
    - **Property 11: Event Type Categorization**
    - **Validates: Requirements 5.2**

  - [x]* 2.11 Write property test for event filtering
    - **Property 12: Event Filtering**
    - **Validates: Requirements 5.3, 5.4**

  - [x] 2.12 Implement chat store with Zustand
    - Create `src/stores/chatStore.ts` with per-agent message histories (max 200 each)
    - Implement `addMessage` that appends and enforces buffer limit per agent
    - Implement `setActiveAgent` and `setPending` actions
    - Implement chat message validation (1-10,000 chars, reject whitespace-only)
    - _Requirements: 4.2, 4.7, 4.9_

  - [x]* 2.13 Write property test for chat message validation
    - **Property 7: Chat Message Validation**
    - **Validates: Requirements 4.2, 4.9**

  - [x]* 2.14 Write property test for chat history buffer invariant
    - **Property 9: Chat History Buffer Invariant**
    - **Validates: Requirements 4.7**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Custom hooks for data fetching
  - [x] 4.1 Implement useHealthPolling hook
    - Create `src/hooks/useHealthPolling.ts` that polls agent health endpoints every 10 seconds
    - Fetch /.well-known/agent.json for agents, / for MCP server
    - Set status to "online" on HTTP 200 with valid JSON within 5 seconds, "offline" otherwise
    - Update healthStore on each poll cycle
    - _Requirements: 2.3, 2.4, 2.5, 2.8, 2.9_

  - [x]* 4.2 Write property test for agent health status derivation
    - **Property 2: Agent Health Status Derivation**
    - **Validates: Requirements 2.3, 2.4, 2.9**

  - [x] 4.3 Implement useMetricsPolling hook
    - Create `src/hooks/useMetricsPolling.ts` that polls /metrics every 5 seconds
    - Parse MetricsSnapshot response and feed to metricsStore.addSnapshot
    - Handle unreachable endpoint by calling metricsStore.setUnavailable
    - Resume normal updates when endpoint becomes reachable again
    - _Requirements: 3.3, 3.4, 3.5_

  - [x] 4.4 Implement useWebSocket hook
    - Create `src/hooks/useWebSocket.ts` with auto-reconnect every 5 seconds on disconnect
    - Parse incoming JSON messages as AgentEvent
    - Call onMessage callback for each event, onConnect/onDisconnect for state changes
    - Expose isConnected state
    - _Requirements: 5.6, 5.7, 5.8_

  - [x] 4.5 Implement useA2AChat hook
    - Create `src/hooks/useA2AChat.ts` that sends POST /send_message to selected agent
    - Format message as A2A protocol payload
    - Handle 120-second timeout, return error on failure
    - Manage isPending state during request
    - _Requirements: 4.2, 4.5, 4.6_

- [x] 5. Shared UI components
  - [x] 5.1 Create Panel, StatusBadge, and Gauge UI primitives
    - Create `src/components/ui/Panel.tsx` with dark card styling (rounded-lg, border, #1a1a2e background)
    - Create `src/components/ui/StatusBadge.tsx` for ONLINE/OFFLINE/DEGRADED/CHECKING badges with correct colors
    - Create `src/components/ui/Gauge.tsx` circular gauge with auto-scaling max (120% of highest observed value)
    - _Requirements: 8.2, 8.3, 8.6, 3.1_

  - [x]* 5.2 Write property test for gauge auto-scaling
    - **Property 4: Gauge Auto-Scaling**
    - **Validates: Requirements 3.1**

- [x] 6. Dashboard panels implementation
  - [x] 6.1 Implement Dashboard Header component
    - Create `src/components/Header.tsx` with title "IGNITE - Intelligent Service Orchestration" and subtitle "Multi-Agent Orchestration Platform"
    - Display active agent count (e.g., "2/2 Agents") from healthStore
    - Display total MCP tools count from metricsStore
    - Display global status badge (ONLINE/DEGRADED/OFFLINE/CHECKING)
    - Display "Live Telemetry" text when metrics endpoint is reachable
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10_

  - [x] 6.2 Implement Topology Panel with React Flow
    - Create `src/components/TopologyPanel.tsx` with directed graph layout
    - Create `src/components/topology/AgentNode.tsx` custom node showing name, port, and status indicator
    - Create `src/components/topology/edges.ts` with directional arrow edges
    - Render Orchestrator as central node connected to Research Agent, Research Agent connected to MCP Server
    - Show green/red/grey status indicators based on healthStore
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x]* 6.3 Write property test for agent node label rendering
    - **Property 3: Agent Node Label Rendering**
    - **Validates: Requirements 2.6**

  - [x] 6.4 Implement Metrics Panel with Recharts
    - Create `src/components/MetricsPanel.tsx` with gauge indicators and time-series charts
    - Display circular gauges for: total requests, total tokens, total tool calls, active agents
    - Display line charts for: tokens/second, average latency, P50/P95/P99 latency
    - Display current model name with "No Model Detected" fallback
    - Show "Metrics Unavailable" indicator when endpoint is unreachable
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.7, 3.8_

  - [x] 6.5 Implement Chat Panel with tabbed interface
    - Create `src/components/ChatPanel.tsx` with agent tabs (Orchestrator, Research Agent)
    - Implement message input with Send button and Enter key support
    - Display user messages right-aligned, agent messages left-aligned with attribution (name + icon)
    - Show loading indicator and disable input while awaiting response
    - Display error messages in chat history on failure/timeout
    - Auto-scroll to latest message on new message
    - Reject empty/whitespace-only messages silently
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_

  - [x]* 6.6 Write property test for chat response attribution
    - **Property 8: Chat Response Attribution**
    - **Validates: Requirements 4.3**

  - [x] 6.7 Implement Activity Log Panel
    - Create `src/components/ActivityLogPanel.tsx` with scrollable event table
    - Display columns: Timestamp (HH:mm:ss.SSS), Agent, Event Type, Details
    - Implement Event Type filter dropdown with "All Events" option
    - Show "Disconnected" indicator when WebSocket is disconnected
    - Display appropriate details per event type (token counts, tool name, target agent, error text)
    - Prepend new events to top of table
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 5.7, 5.8, 5.9_

  - [x]* 6.8 Write property test for event table row rendering
    - **Property 10: Event Table Row Rendering**
    - **Validates: Requirements 5.1**

  - [x]* 6.9 Write property test for event detail extraction
    - **Property 15: Event Detail Extraction**
    - **Validates: Requirements 5.9**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Main page layout and integration
  - [x] 8.1 Create root layout and main dashboard page
    - Create `src/app/layout.tsx` with dark theme, font configuration (monospace + sans-serif)
    - Create `src/app/globals.css` with Tailwind directives and CSS custom properties for color palette
    - Create `src/app/page.tsx` with 2x2 grid layout (Topology top-left, Metrics top-right, Chat bottom-left, Activity Log bottom-right)
    - Implement responsive breakpoint: stack vertically below 1024px viewport width
    - Wire all hooks (useHealthPolling, useMetricsPolling, useWebSocket, useA2AChat) into the page
    - Connect Header component with global status from stores 
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 9. Backend API extensions
  - [x] 9.1 Add /metrics GET endpoint to Orchestrator Agent
    - Add route handler in `src/orchestrator/o1_server.py` for GET /metrics
    - Return MetricsCollector.summary() as JSON with added "timestamp" field (ISO 8601)
    - Add CORS headers (configurable origin via environment variable)
    - Return HTTP 503 with error JSON if MetricsCollector is unreachable
    - _Requirements: 7.1, 7.3, 7.6, 7.7_

  - [x]* 9.2 Write property test for metrics API response schema
    - **Property 18: Metrics API Response Schema**
    - **Validates: Requirements 7.6**

  - [x] 9.3 Add /ws/events WebSocket endpoint to Orchestrator Agent
    - Add WebSocket route in `src/orchestrator/o1_server.py` for /ws/events
    - Stream agent activity events as JSON messages with fields: timestamp, agent, event_type, details
    - Send heartbeat message every 15 seconds with event_type "heartbeat"
    - Broadcast new MetricsCollector events to all connected clients within 1 second
    - _Requirements: 7.2, 7.4, 7.5_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The frontend (tasks 1-8) is a standalone Next.js project in a separate directory
- Backend extensions (task 9) modify the existing Python orchestrator with minimal changes
- All polling intervals and buffer sizes match the requirements exactly (10s health, 5s metrics, 60 metrics points, 200 chat messages, 500 events)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3", "2.1", "2.4", "2.7", "2.12"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.5", "2.6", "2.8", "2.9", "2.10", "2.11", "2.13", "2.14"] },
    { "id": 4, "tasks": ["4.1", "4.3", "4.4", "4.5", "5.1"] },
    { "id": 5, "tasks": ["4.2", "5.2"] },
    { "id": 6, "tasks": ["6.1", "6.2", "6.4", "6.5", "6.7", "9.1", "9.3"] },
    { "id": 7, "tasks": ["6.3", "6.6", "6.8", "6.9", "9.2"] },
    { "id": 8, "tasks": ["8.1"] }
  ]
}
```
