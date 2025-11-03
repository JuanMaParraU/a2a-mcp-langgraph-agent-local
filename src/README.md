# Source Code Overview

This directory contains the core implementation of the local agentic AI system, demonstrating the integration of Agent-to-Agent (A2A) communication, Model Context Protocol (MCP), and LangGraph orchestration.

---

## 📁 File Structure

```
src/
├── __init__.py                  # Package initialization
├── a2a_1_starlette.py          # A2A HTTP server layer
├── a2a_2_executor.py           # A2A task execution engine
├── a2a_3_agent.py              # Complete A2A agent implementation
├── client.py                    # Main client for interacting with agents
├── mcp_server.py               # MCP server providing tools to agents
├── mcp_test_client.py          # MCP testing and validation
```

---
## Architecture
```
┌─────────────────────────────────────────────────────────┐
│  👤 User                                                │
│  ┌───────────────────────────────────────────────────┐  │
│  │ client.py (A2A Client)                            │  │
│  │ • Terminal interface                              │  │
│  │ • Sends POST requests                             │  │
│  └────────────────────┬──────────────────────────────┘  │
└──────────────────────┬┼──────────────────────────────────┘
                       │ POST /send_message
                       ↓
┌─────────────────────────────────────────────────────────┐
│  a2a_1_starlette.py (Outermost Layer)                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │ HTTP Server (Starlette)                           │  │
│  │ • Exposes REST API endpoints                      │  │
│  │ • Handles A2A protocol                            │  │
│  └────────────────────┬──────────────────────────────┘  │
│                       │ wraps                           │
│         ┌─────────────▼──────────────────────────────┐  │
│         │  a2a_2_executor.py (Middle Layer)          │  │
│         │  ┌──────────────────────────────────────┐  │  │
│         │  │ Task Execution Engine                │  │  │
│         │  │ • Manages task lifecycle             │  │  │
│         │  │ • Error handling & retries           │  │  │
│         │  └───────────────┬──────────────────────┘  │  │
│         │                  │ wraps                   │  │
│         │    ┌─────────────▼──────────────────────┐  │  │
│         │    │ a2a_3_agent.py (Core)              │  │  │
│         │    │ ┌──────────────────────────────┐   │  │  │
│         │    │ │ LangGraph State Machine      │   │  │  │
│         │    │ │ • Agent reasoning logic      │   │  │  │
│         │    │ │ • Ollama LLM backend         │   │  │  │
│         │    │ │ • MCP client for tools       │   │  │  │
│         │    │ └──────────────────────────────┘   │  │  │
│         │    └────────┬───────────────────────────┘  │  │
│         └─────────────┼──────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────┘
                        │ connects to
                        ↓
       ┌──────────────────────────────────┐
       │ mcp_server.py (Tool Wrapper)     │
       │ ┌──────────────────────────────┐ │
       │ │ MCP Protocol Layer           │ │
       │ │ • Standardizes tool access   │ │
       │ │ • Formats responses          │ │
       │ │ • Tool discovery             │ │
       │ └────────────┬─────────────────┘ │
       │              │ wraps             │
       │   ┌──────────▼────────────────┐  │
       │   │ Actual Tools              │  │
       │   │ • DuckDuckGo Search       │  │
       │   │ • arXiv Search            │  │
       │   │ • Wikipedia Search        │  │
       │   └───────────────────────────┘  │
       └──────────────────────────────────┘
                        
                    ┌───┐ reasoning
                    │   │
                    ↓   │
       ┌──────────────────────────────────┐
       │ 🧠 Ollama (Local LLM)            │
       │ ┌──────────────────────────────┐ │
       │ │ Local LLM Server             │ │
       │ │ • Hosts open-source models   │ │
       │ └────────────┬─────────────────┘ │
       │              │ serves            │
       │   ┌──────────▼────────────────┐  │
       │   │ Models:                   │  │
       │   │ 🔷 Mistral                │  │
       │   │ 🦙 Llama 3                │  │
       │   │ ⚡ Qwen                    │  │
       │   │ 💎 Gemma                  │  │
       │   │ 🤖 Gpt-oss                │  │
       │   └───────────────────────────┘  │
       └──────────────────────────────────┘

User interaction flow:
client.py → POST /send_message → a2a_1_starlette.py → a2a_2_executor.py 
          → a2a_3_agent.py ──┬→ mcp_server.py → Actual Tools (DuckDuckGo, arXiv, etc.)
                             └→ Ollama → Models (reasoning)
```

## 🔍 Detailed File Descriptions

### `__init__.py`
**Purpose:** Python package initialization file

**Role:**
- Makes the `src/` directory importable as a Python package
- May contain package-level imports and configuration
- Exposes key classes/functions for easier imports elsewhere

---

### `a2a_3_agent.py`
**Purpose:** Core LangGraph agent implementation with Ollama backend

**What it does:**
- Implements the actual agent logic using LangGraph for state management
- Uses Ollama as the LLM backend for reasoning and decision-making
- Connects to MCP server for tool access
- Defines the agent's reasoning loop, state transitions, and capabilities

**Key concepts:**
- **LangGraph State Machine:** Manages agent state and transitions
- **Ollama Integration:** Local LLM provides reasoning capabilities
- **MCP Client:** Calls tools via Model Context Protocol
- **Agent Logic:** The "brain" of the agent - planning and decision-making

**When to use:** This is the core agent logic. Study this to understand how the agent thinks and makes decisions.

---

### `a2a_2_executor.py`
**Purpose:** Task execution wrapper around the LangGraph agent

**What it does:**
- Wraps `a2a_3_agent.py` to handle task execution
- Manages task lifecycle, queue, and state
- Coordinates between receiving tasks and invoking the LangGraph agent
- Handles error recovery, retries, and result formatting
- Bridges between external requests and the agent's reasoning engine

**Key concepts:**
- **Executor Pattern:** Separates task management from reasoning logic
- **Task Queue:** May handle multiple tasks or prioritization
- **State Management:** Tracks task progress and results
- **Error Handling:** Manages failures and retries

**When to use:** This wraps the agent logic to make it executable. It's the middle layer between the HTTP server and the agent's brain.

---

### `a2a_1_starlette.py`
**Purpose:** A2A HTTP server wrapping the executor

**What it does:**
- Wraps `a2a_2_executor.py` with HTTP transport layer using Starlette framework
- Exposes REST API endpoints for Agent-to-Agent communication
- Handles HTTP requests and routes them to the executor
- Implements A2A protocol over HTTP (service discovery, message passing)
- Makes the agent accessible over the network

**Key concepts:**
- **HTTP Transport:** Agents communicate via HTTP REST API
- **A2A Protocol:** Standardized endpoints for agent discovery and communication
- **Starlette Framework:** Lightweight ASGI framework for async HTTP
- **Network Layer:** The outermost layer that external clients interact with

**When to use:** This is what you run to start the agent server. It's the outermost wrapper that makes everything accessible.

**Wrapping structure:**
```
a2a_1_starlette.py (HTTP server)
    └─ wraps a2a_2_executor.py (Task execution)
        └─ wraps a2a_3_agent.py (LangGraph + Ollama)
            └─ connects to mcp_server.py (Tools)
```

---

### `client.py`
**Purpose:** Main client interface for interacting with the agentic system

**What it does:**
- Provides a user-friendly interface to interact with agents
- Handles communication with both A2A agents and MCP servers
- May include CLI or programmatic API for sending tasks to agents
- Manages connections and handles responses

**Key concepts:**
- **Entry Point:** This is likely how you start interactions with your agent system
- **Request/Response:** Sends tasks to agents and receives results
- **Connection Management:** Maintains connections to running agents

**When to use:** Use this as your main interface to test and interact with agents. This is likely what users run to send tasks to the agentic system.

**Example usage:**
```python
from src.client import AgentClient

client = AgentClient()
result = client.send_task("research", {"topic": "agentic AI"})
```

---

### `mcp_server.py`
**Purpose:** MCP server that exposes tools to agents

**What it does:**
- Implements the Model Context Protocol server specification
- Exposes tools (file operations, web search, data processing, etc.) in a standardized way
- Handles tool discovery, description, and execution
- Provides a consistent interface for agents to access capabilities

**Key concepts:**
- **Tool Registry:** Maintains list of available tools
- **Standardized Interface:** Tools exposed via MCP can be used by any MCP-compatible agent
- **Tool Execution:** Safely executes tool calls and returns results

**Available tools (typical examples):**
- File system operations (read, write, list)
- Web requests
- Data processing
- Custom domain-specific tools

**When to use:** Run this server to make tools available to agents. Agents connect to this server when they need to use tools.

**Example flow:**
1. MCP server starts and registers available tools
2. Agent queries: "What tools are available?"
3. MCP server responds with tool list and descriptions
4. Agent requests: "Execute file_read tool with path='data.json'"
5. MCP server executes and returns results

---

### `mcp_test_client.py`
**Purpose:** Testing and validation client for MCP server

**What it does:**
- Tests MCP server functionality independently
- Validates tool discovery and execution
- Useful for debugging and development
- May include examples of how to interact with MCP server

**Key concepts:**
- **Testing:** Ensures MCP server works correctly before agent integration
- **Validation:** Checks tool responses and error handling
- **Examples:** Shows how to properly interact with MCP protocol

**When to use:** Use this to test your MCP server is working correctly before connecting agents to it.

**Example usage:**
```bash
python src/mcp_test_client.py
# Tests tool discovery and execution
```

## 🚀 Quick Start Guide

### Terminal 1: Start the MCP Server
```bash
python src/mcp_server.py
# Exposes tools on default port (e.g., 8001)
# Keep this running - agents will connect to it for tool access
```

### Terminal 1 (Optional): Test MCP Server First
```bash
python src/mcp_test_client.py
# Validates tools are working before starting agents
# Run this once to confirm MCP server is operational
```

### Terminal 2: Start the Starlette Server (Agent)
```bash
python src/a2a_1_starlette.py
# This starts the full agent stack:
#   - Starlette HTTP server (outer wrapper)
#   - Executor (middle layer)
#   - LangGraph agent with Ollama (core)
# Agent exposes A2A interface on default port (e.g., 8000)
# Keep this running - this is your agent server
```

### Terminal 3: Run the Client
```bash
python src/client.py
# Interact with the agent
# Send tasks and receive results
```

**Summary:**
1. **Terminal 1:** MCP Server (provides tools)
2. **Terminal 2:** Starlette Server (starts the full agent)
3. **Terminal 3:** Client (send tasks to agent)

---

## 🛠️ Development Workflow

### Adding a New MCP Tool

1. Edit `mcp_server.py`
2. Add tool definition:
```python
@mcp_server.tool()
def my_new_tool(param: str) -> dict:
    """Tool description for LLM"""
    # Tool logic here
    return {"result": "success"}
```
3. Restart MCP server
4. Test with `mcp_test_client.py`

### Creating a New Agent Type

1. Copy `a2a_3_agent.py` as template
2. Modify agent capabilities and reasoning logic
3. Register agent with different identity/port
4. Test multi-agent communication

### Debugging Tips

- **MCP issues:** Check `mcp_test_client.py` first
- **A2A communication:** Check agent logs for HTTP requests
- **Reasoning problems:** Check Ollama is running (`ollama serve`)
- **Port conflicts:** Check default ports (8000, 8001) are available
