# Running Guide — A2A MCP LangGraph Agent (Windows)

This document explains how to run the multi-agent system step by step on a Windows machine.

---

## Prerequisites

Before starting, ensure the following are in place:

- **Python 3.13+** installed
- **Virtual environment** created and dependencies installed:
  ```cmd
  python -m venv .venv
  .venv\Scripts\pip.exe install -r requirements.txt
  .venv\Scripts\pip.exe install arxiv
  ```
- **Ollama server** running and accessible at `http://10.215.130.20:11434`
- Models available on the Ollama server:
  - `mistral-nemo` (used by the Research Agent)
  - `qwen3:4b` (used by the Orchestrator Agent)

---

## Step-by-Step Execution

You need **4 separate terminal windows**, started in order. Open each terminal at the project root:

```
C:\Users\614219362\OneDrive - BT Plc\Documents\QMC\Network\git\Agentic\a2a-mcp-langgraph-agent-local
```

---

### Terminal 1 — MCP Server (Tools)

```cmd
.venv\Scripts\python.exe src\mcp_server.py
```

**What it does:** Starts the MCP (Model Context Protocol) server on port 8000. This server exposes three research tools: DuckDuckGo search, Wikipedia search, and arXiv paper search.

**Wait for:** The message `🚀 Starting MCP Research Tools server...` and confirmation that the server is running on streamable-http transport.

**Expected output:**
```
INFO:root:✅ Signal handlers set up. Use Ctrl+C or kill command to stop gracefully.
INFO:root:🚀 Starting MCP Research Tools server...
INFO:root:📡 Server running on streamable-http transport
INFO:root:🔍 Available tools: duckduckgo_search, wikipedia_search
INFO:root:⏹️  Press Ctrl+C to stop the server gracefully
```

---

### Terminal 2 — Research Agent (Port 9991)

```cmd
.venv\Scripts\python.exe src\a2a_1_starlette.py
```

**What it does:** Starts the Research Agent — a LangGraph ReAct agent that uses `mistral-nemo` for reasoning and connects to the MCP server for tool access. It exposes an A2A (Agent-to-Agent) interface on port 9991.

**Wait for:** Uvicorn showing it's running on `0.0.0.0:9991`.

**Expected output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9991 (Press CTRL+C to quit)
```

---

### Terminal 3 — Orchestrator Agent (Port 9990)

```cmd
.venv\Scripts\python.exe src\orchestrator\o1_server.py
```

**What it does:** Starts the Orchestrator Agent — a lightweight coordinator that uses `qwen3:4b` to decide whether to answer directly or delegate tasks to the Research Agent via A2A. It exposes its own A2A interface on port 9990.

**Wait for:** Uvicorn showing it's running on `0.0.0.0:9990`.

**Expected output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9990 (Press CTRL+C to quit)
```

---

### Terminal 4 — Client (Interactive)

```cmd
.venv\Scripts\python.exe src\client.py
```

**What it does:** Starts an interactive terminal client that connects to the Orchestrator Agent (port 9990) and lets you send messages and receive responses.

**Expected output:**
```
✅ Connected to agent at http://localhost:9990

============================================================
🤖 Multi-turn A2A Agent ready!
Type 'quit', 'exit', or 'q' to end.
Type 'card' to view agent capabilities.
============================================================

🔎 You:
```

---

## Testing Commands

Once the client is running, try these commands:

| Command | What Happens |
|---------|-------------|
| `card` | Displays the Orchestrator Agent's capabilities and skills |
| `What is quantum computing?` | Orchestrator answers directly using `qwen3:4b` (no delegation) |
| `Search for papers on LLMs` | Orchestrator delegates to Research Agent, which uses arXiv tool |
| `Use wikipedia to explain TCP/IP` | Orchestrator delegates to Research Agent, which uses Wikipedia tool |
| `Find recent news about AI` | Orchestrator delegates to Research Agent, which uses DuckDuckGo tool |
| `quit` | Exits the client |

---

## How the Flow Works

```
User Input → Client (Terminal 4)
                │
                ▼ (A2A POST to port 9990)
         Orchestrator Agent (Terminal 3)
                │
        ┌───────┴───────┐
        │               │
   [Direct Answer]  [Delegate]
   (qwen3:4b)          │
                        ▼ (A2A POST to port 9991)
                 Research Agent (Terminal 2)
                        │
                ┌───────┴───────┐
                │               │
           [LLM Reasoning]  [Use Tools]
           (mistral-nemo)       │
                                ▼ (MCP to port 8000)
                         MCP Server (Terminal 1)
                                │
                    ┌───────────┼───────────┐
                    │           │           │
               DuckDuckGo   Wikipedia    arXiv
```

**Routing logic:** The Orchestrator checks if the user input contains keywords like "research", "search", "wikipedia", or "paper". If yes, it delegates to the Research Agent. Otherwise, it answers directly.

---

## Alternative: Quick Test (MCP Only, No A2A)

If you want to test the MCP server + LLM integration without the full A2A stack:

### Terminal 1 — MCP Server
```cmd
.venv\Scripts\python.exe src\mcp_server.py
```

### Terminal 2 — MCP Test Client
```cmd
.venv\Scripts\python.exe src\mcp_test_client.py
```

This gives you a direct chat with the Research Agent (using `mistral-nemo` + MCP tools) bypassing the A2A protocol entirely. Useful for debugging tool issues.

---

## Alternative: Batch Script Launcher

The `start_agents.bat` script launches Terminals 1-3 automatically in separate windows:

```cmd
start_agents.bat
```

Then open a 4th terminal manually and run the client:
```cmd
.venv\Scripts\python.exe src\client.py
```

---

## Stopping the System

- **Client:** Type `quit`, `exit`, or `q`, or press `Ctrl+C`
- **Servers (Terminals 1-3):** Press `Ctrl+C` in each terminal window

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'xxx'` | Run `.venv\Scripts\pip.exe install xxx` |
| Client hangs on first request | First request is slow — Ollama needs to load the model into memory. Wait 30-60 seconds. |
| SSL certificate errors in MCP tools | Already handled in code (`ssl._create_unverified_context`). If still failing, check corporate proxy settings. |
| `ConnectionRefusedError` on port 8000 | MCP server isn't running. Start Terminal 1 first. |
| `ConnectionRefusedError` on port 9991 | Research Agent isn't running. Start Terminal 2. |
| `ConnectionRefusedError` on port 9990 | Orchestrator isn't running. Start Terminal 3. |
| 404 errors with JNDI payloads in MCP logs | Ignore — this is Microsoft Defender scanning open ports, not related to your code. |
| Ollama model not found | Verify model is available: open browser to `http://10.215.130.20:11434/api/tags` |

---

## Port Summary

| Port | Service | File |
|------|---------|------|
| 8000 | MCP Tool Server | `src/mcp_server.py` |
| 9990 | Orchestrator Agent (A2A) | `src/orchestrator/o1_server.py` |
| 9991 | Research Agent (A2A) | `src/a2a_1_starlette.py` |
| 11434 | Ollama LLM Server | External (`http://10.215.130.20:11434`) |

---

*Document created for the `pw-agentic` branch.*
