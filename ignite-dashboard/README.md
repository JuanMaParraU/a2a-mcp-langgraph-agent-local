# IGNITE Dashboard

**Intelligent Service Orchestration** — A real-time monitoring and interaction dashboard for the A2A + MCP + LangGraph multi-agent system.

## Features

- **Agent Topology Visualization** — Directed graph showing agent connections and live health status
- **Server Metrics & Telemetry** — Real-time gauges and time-series charts for inference performance
- **Agent Chat Interface** — Tabbed chat for direct A2A protocol communication with agents
- **Activity Log** — Real-time WebSocket event stream with filtering

## Prerequisites

- Node.js >= 18.0.0
- npm (comes with Node.js)

## Setup

1. Clone the repository and navigate to the dashboard directory:

```bash
cd ignite-dashboard
```

2. Install dependencies:

```bash
npm install
```

3. Create your local environment file:

```bash
cp .env.local.example .env.local
```

4. Edit `.env.local` if your backend agents run on non-default ports.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `NEXT_PUBLIC_ORCHESTRATOR_URL` | Orchestrator Agent base URL (A2A, metrics, WebSocket) | `http://localhost:9990` |
| `NEXT_PUBLIC_RESEARCH_AGENT_URL` | Research Agent base URL (A2A, health checks) | `http://localhost:9991` |
| `NEXT_PUBLIC_MCP_SERVER_URL` | MCP Server base URL (health checks) | `http://localhost:8000` |

## Development Commands

```bash
# Start development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter
npm run lint

# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Tech Stack

- **Framework**: Next.js 15 (App Router) with React 19
- **Language**: TypeScript 5.7
- **Styling**: Tailwind CSS 3.4 (dark theme)
- **State Management**: Zustand 5
- **Graph Visualization**: React Flow (@xyflow/react)
- **Charts**: Recharts 2.15
- **Testing**: Vitest + fast-check + Testing Library + MSW

## Architecture

The dashboard is a standalone frontend application that communicates with backend agents exclusively through HTTP REST and WebSocket APIs:

- `GET /.well-known/agent.json` — Agent health checks (10s polling)
- `GET /metrics` — Inference telemetry (5s polling)
- `WS /ws/events` — Real-time activity event stream
- `POST /send_message` — A2A protocol chat messages

No shared code or build dependencies with the backend repository.
