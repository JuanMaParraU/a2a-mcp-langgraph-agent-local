# Requirements Document

## Introduction

IGNITE (Intelligent Service Orchestration) is a standalone frontend dashboard and chat interface for monitoring and interacting with an existing A2A + MCP + LangGraph multi-agent system. The dashboard provides real-time visibility into agent topology, server metrics, inference telemetry, agent chat, and activity logging. It connects to the backend agents via their existing A2A HTTP endpoints and a lightweight metrics/WebSocket API layer, requiring minimal backend modifications.

## Glossary

- **Dashboard**: The IGNITE frontend web application providing visualization, chat, and monitoring panels
- **Orchestrator_Agent**: The coordinating agent running on port 9990 that routes requests to worker agents
- **Research_Agent**: A worker agent running on port 9991 that performs research tasks via MCP tools
- **MCP_Server**: The Model Context Protocol server running on port 8000 providing tool access (DuckDuckGo, Wikipedia, arXiv)
- **A2A_Protocol**: Agent-to-Agent communication protocol using HTTP POST /send_message endpoints
- **Agent_Card**: A JSON descriptor exposed at /.well-known/agent.json containing agent name, skills, capabilities, and URL
- **Topology_Panel**: The visual graph panel showing agent nodes, connections, and live status indicators
- **Metrics_Panel**: The panel displaying real-time time-series charts and gauge indicators for inference telemetry
- **Chat_Panel**: The tabbed interface allowing users to send messages to specific agents and view responses
- **Activity_Log_Panel**: The real-time event table showing agent activity with filtering capabilities
- **Metrics_Collector**: The existing Python singleton class that tracks requests, errors, tokens, latencies, tool calls, and model info
- **WebSocket_Connection**: A persistent bidirectional connection used to push real-time metrics and activity events to the Dashboard
- **Metrics_Endpoint**: A REST endpoint (GET /metrics) added to backend agents to expose current telemetry data
- **Events_WebSocket**: A WebSocket endpoint (ws://host:port/ws/events) added to backend agents to stream activity events in real time

## Requirements

### Requirement 1: Project Scaffolding and Standalone Architecture

**User Story:** As a developer, I want the IGNITE dashboard to be a separate frontend project independent of the backend repository, so that I can develop, deploy, and version the frontend independently.

#### Acceptance Criteria

1. THE Dashboard SHALL be a standalone React application bootstrapped with Next.js and TypeScript with no shared code dependencies or build steps with the backend repository
2. THE Dashboard SHALL define backend agent connection URLs via environment variables (NEXT_PUBLIC_ORCHESTRATOR_URL, NEXT_PUBLIC_RESEARCH_AGENT_URL, NEXT_PUBLIC_MCP_SERVER_URL) with default values of http://localhost:9990, http://localhost:9991, and http://localhost:8000 respectively
3. IF any required environment variable is not set and no default value is available, THEN THE Dashboard SHALL log a warning to the browser console at startup indicating which variable is missing
4. THE Dashboard SHALL use Tailwind CSS for styling with a dark theme as the default and only theme
5. THE Dashboard SHALL include a package.json with exact dependency versions (no caret "^" or tilde "~" ranges) for reproducible builds and SHALL specify the minimum supported Node.js version (>=18.0.0)
6. THE Dashboard SHALL provide a README with setup instructions, environment variable documentation (name, purpose, default value for each variable), and development commands (install, dev, build, lint)
7. WHEN a developer runs the build command, THE Dashboard SHALL produce a successful production build with zero errors and no backend connectivity required at build time

### Requirement 2: Agent Topology Visualization

**User Story:** As an operator, I want to see a visual graph of all agents and their connections, so that I can understand the system architecture and monitor connection health at a glance.

#### Acceptance Criteria

1. WHEN the Dashboard loads, THE Topology_Panel SHALL render a directed graph showing the Orchestrator_Agent as a central node connected to each worker agent node
2. THE Topology_Panel SHALL display the MCP_Server as a node connected to the Research_Agent
3. WHEN the Dashboard fetches an Agent_Card successfully (HTTP 200 response with valid JSON) from an agent URL within 5 seconds, THE Topology_Panel SHALL display a green "ONLINE" status indicator on that agent node
4. IF the Dashboard receives a non-200 response or no response within 5 seconds when fetching an Agent_Card from an agent URL, THEN THE Topology_Panel SHALL display a red "OFFLINE" status indicator on that agent node
5. THE Topology_Panel SHALL poll each agent's Agent_Card endpoint every 10 seconds to refresh connection status
6. THE Topology_Panel SHALL display the agent name and port number as labels on each node
7. THE Topology_Panel SHALL display connection lines between nodes with directional arrows indicating communication flow
8. WHILE the first health check has not yet completed after Dashboard load, THE Topology_Panel SHALL display a grey "CHECKING" status indicator on each agent node
9. WHEN the Dashboard fetches the MCP_Server root endpoint (/) and receives an HTTP 200 response within 5 seconds, THE Topology_Panel SHALL display a green "ONLINE" status indicator on the MCP_Server node

### Requirement 3: Server Metrics and Inference Telemetry

**User Story:** As an operator, I want to see real-time metrics about inference performance, so that I can monitor system health and identify performance bottlenecks.

#### Acceptance Criteria

1. WHEN the Dashboard connects to the Metrics_Endpoint, THE Metrics_Panel SHALL display circular gauge indicators showing current values for: total requests, total tokens, total tool calls, and active agents count, where each gauge auto-scales its maximum to 120% of the highest observed value
2. WHEN new metrics data arrives, THE Metrics_Panel SHALL compute and update time-series line charts showing tokens per second (calculated as the difference in total tokens between consecutive polls divided by the poll interval), average latency, and P50/P95/P99 latency percentiles computed from the submission_latencies array, over the last 5 minutes
3. THE Metrics_Panel SHALL poll the Metrics_Endpoint every 5 seconds to retrieve updated telemetry data
4. WHEN the Metrics_Endpoint is unreachable, THE Metrics_Panel SHALL display a "Metrics Unavailable" indicator and retain the last known data on the charts
5. WHEN the Metrics_Endpoint becomes reachable again after being unreachable, THE Metrics_Panel SHALL remove the "Metrics Unavailable" indicator and resume normal chart updates on the next successful poll
6. THE Metrics_Panel SHALL store up to 60 data points (5 minutes at 5-second intervals) in memory for chart rendering, discarding the oldest data point first when the limit is exceeded
7. THE Metrics_Panel SHALL display the current LLM model name retrieved from the metrics data
8. IF the model name field is null or absent in the metrics response, THEN THE Metrics_Panel SHALL display "No Model Detected" in place of the model name

### Requirement 4: Agent Chat Interface

**User Story:** As a user, I want to send messages to specific agents and see their responses in a chat interface, so that I can interact with the multi-agent system directly from the dashboard.

#### Acceptance Criteria

1. THE Chat_Panel SHALL display tabs for each configured agent (Orchestrator, Research Agent) allowing the user to select which agent to communicate with
2. WHEN the user types a message between 1 and 10,000 characters and clicks Send (or presses Enter), THE Chat_Panel SHALL send the message to the selected agent via A2A_Protocol POST /send_message
3. WHEN the agent returns a response, THE Chat_Panel SHALL display the response in the message history with agent attribution (agent name and icon)
4. THE Chat_Panel SHALL display user messages aligned to the right and agent responses aligned to the left with distinct visual styling
5. WHILE the Chat_Panel is awaiting a response from an agent, THE Chat_Panel SHALL display a loading indicator and disable the Send button and message input until the response arrives or the request times out
6. IF the A2A_Protocol request fails or times out after 120 seconds, THEN THE Chat_Panel SHALL display an error message in the chat history indicating the failure reason and re-enable the message input and Send button
7. THE Chat_Panel SHALL maintain separate message histories of up to 200 messages per agent tab within the current browser session (until page reload), discarding the oldest messages when the limit is exceeded
8. WHEN a new message is added to the chat history, THE Chat_Panel SHALL auto-scroll to the latest message
9. IF the user clicks Send or presses Enter with an empty or whitespace-only message, THEN THE Chat_Panel SHALL not send the message and SHALL keep the input focused without displaying an error

### Requirement 5: Agent Activity Log

**User Story:** As an operator, I want to see a real-time log of all agent events, so that I can trace agent behavior, debug issues, and understand system activity.

#### Acceptance Criteria

1. WHEN the Dashboard connects to the Events_WebSocket, THE Activity_Log_Panel SHALL display incoming events in a scrollable table with columns: Timestamp (formatted as HH:mm:ss.SSS), Agent (agent name), Event Type, and Details
2. THE Activity_Log_Panel SHALL categorize events by their type field into: Token Usage, Tool Call, Heartbeat, A2A Dispatch, A2A Message, and Error, and SHALL display events with an unrecognized type under a fallback label of "Unknown"
3. WHEN the user selects a filter from the Event Type dropdown, THE Activity_Log_Panel SHALL display only events matching the selected type from all currently retained events
4. WHEN the user selects "All Events" from the filter dropdown, THE Activity_Log_Panel SHALL display all retained events regardless of type
5. THE Activity_Log_Panel SHALL retain up to 500 events in memory, discarding the oldest events when the limit is exceeded
6. WHEN a new event arrives via WebSocket, THE Activity_Log_Panel SHALL prepend the event to the top of the table within 1 second of receipt
7. IF the Events_WebSocket connection is lost, THEN THE Activity_Log_Panel SHALL display a "Disconnected" indicator and attempt to reconnect every 5 seconds indefinitely until the connection is re-established
8. WHEN the Events_WebSocket connection is re-established after a disconnection, THE Activity_Log_Panel SHALL remove the "Disconnected" indicator and resume displaying incoming events
9. THE Activity_Log_Panel SHALL display token counts (prompt tokens, completion tokens, total tokens) in the Details column for Token Usage events, the tool name for Tool Call events, the target agent name for A2A Dispatch and A2A Message events, and the error summary text for Error events

### Requirement 6: Dashboard Header and Global Status

**User Story:** As an operator, I want to see a summary header showing overall system status, so that I can quickly assess whether the platform is healthy.

#### Acceptance Criteria

1. THE Dashboard SHALL display a header bar with the title "IGNITE - Intelligent Service Orchestration"
2. THE Dashboard SHALL display a subtitle reading "Multi-Agent Orchestration Platform" in the header
3. WHEN agent health checks complete, THE Dashboard SHALL display the count of active (online) agents out of the total configured agents (e.g., "2/2 Agents") in the header, where the configured agents are those defined by the backend connection environment variables
4. THE Dashboard SHALL display the total number of MCP tools reported by the Metrics_Endpoint in the header, or display "0" if the Metrics_Endpoint is unreachable
5. WHEN all configured agents are online, THE Dashboard SHALL display a green "ONLINE" status badge in the header
6. WHEN at least one but not all configured agents are offline, THE Dashboard SHALL display an amber "DEGRADED" status badge in the header
7. WHEN all configured agents are offline, THE Dashboard SHALL display a red "OFFLINE" status badge in the header
8. WHEN the Dashboard successfully receives a response from the Metrics_Endpoint within 5 seconds, THE Dashboard SHALL display "Live Telemetry" text in the header
9. IF the Metrics_Endpoint does not respond within 5 seconds, THEN THE Dashboard SHALL hide the "Live Telemetry" text from the header
10. WHILE the Dashboard is loading initial agent health checks, THE Dashboard SHALL display a neutral "CHECKING" status badge in the header until the first health check cycle completes

### Requirement 7: Backend API Extensions (Minimal Changes)

**User Story:** As a frontend developer, I want the backend to expose metrics and event streaming endpoints, so that the dashboard can consume real-time data without modifying the core agent logic.

#### Acceptance Criteria

1. WHEN a GET request is made to /metrics on the Orchestrator_Agent, THE Orchestrator_Agent SHALL return a JSON response with HTTP status 200 containing the current Metrics_Collector summary data
2. WHEN a WebSocket connection is established at /ws/events on the Orchestrator_Agent, THE Orchestrator_Agent SHALL stream agent activity events as JSON messages, where each message contains the fields: "timestamp" (ISO 8601 format), "agent" (agent name string), "event_type" (one of: "request", "tool_call", "token_usage", "inter_agent_message", "error"), and "details" (object with event-specific data)
3. THE Metrics_Endpoint SHALL include CORS headers allowing requests from the Dashboard origin (configurable via environment variable)
4. WHILE a WebSocket connection is active at /ws/events, THE Events_WebSocket SHALL send a heartbeat message containing {"event_type": "heartbeat", "timestamp": "<ISO 8601>"} every 15 seconds to keep the connection alive
5. WHEN the Metrics_Collector records a new event (request, tool call, token usage, inter-agent message), THE Events_WebSocket SHALL broadcast the event to all connected clients within 1 second
6. THE Metrics_Endpoint response SHALL conform to the existing Metrics_Collector summary() output format with an additional "timestamp" field in ISO 8601 format indicating when the snapshot was generated
7. IF the Metrics_Collector is unreachable or returns an error when /metrics is requested, THEN THE Orchestrator_Agent SHALL return an HTTP 503 response with a JSON body containing an "error" field indicating the service is temporarily unavailable

### Requirement 8: Responsive Layout and Dark Theme

**User Story:** As a user, I want the dashboard to have a professional dark-themed UI with a responsive four-panel layout, so that I can monitor the system comfortably on various screen sizes.

#### Acceptance Criteria

1. THE Dashboard SHALL render a four-panel grid layout in a 2x2 equal-proportion grid: Topology (top-left), Metrics (top-right), Chat (bottom-left), Activity Log (bottom-right)
2. THE Dashboard SHALL use a dark color scheme with a background color of #0a0a0f and card backgrounds of #1a1a2e
3. THE Dashboard SHALL use accent colors: cyan (#00d4ff) for primary highlights, green (#00ff88) for success states, red (#ff4444) for error states, and amber (#ffaa00) for warning states
4. WHEN the viewport width is below 1024 pixels, THE Dashboard SHALL stack the panels vertically in a single-column layout in the following order from top to bottom: Topology, Metrics, Chat, Activity Log
5. THE Dashboard SHALL use monospace fonts for metrics values and log entries, and sans-serif fonts for labels and headings
6. THE Dashboard SHALL render all panels with rounded corners of 8 pixels border-radius and a 1-pixel solid border using a color no brighter than 20% opacity white
7. WHEN the combined panel content exceeds the viewport height, THE Dashboard SHALL enable vertical scrolling on the page to access all panels
