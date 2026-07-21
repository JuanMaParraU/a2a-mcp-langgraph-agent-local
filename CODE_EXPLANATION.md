# Code Explanation — Line-by-Line Breakdown

This document provides a detailed explanation of every code file in the project, covering imports, classes, methods, and logic flow.

---

## Table of Contents

1. [src/mcp_server.py](#srcmcp_serverpy)
2. [src/a2a_1_starlette.py](#srca2a_1_starlettepy)
3. [src/a2a_2_executor.py](#srca2a_2_executorpy)
4. [src/a2a_3_agent.py](#srca2a_3_agentpy)
5. [src/client.py](#srcclientpy)
6. [src/mcp_test_client.py](#srcmcp_test_clientpy)
7. [src/orchestrator/o1_server.py](#srcorchestratoro1_serverpy)
8. [src/orchestrator/o2_executor.py](#srcorchestratoro2_executorpy)
9. [src/orchestrator/o3_agent.py](#srcorchestratoro3_agentpy)
10. [src/orchestrator/metrics.py](#srcorchestratormetricspy)
11. [src/orchestrator/metrics_middleware.py](#srcorchestratormetrics_middlewarepy)

---

## src/mcp_server.py

**Purpose:** MCP (Model Context Protocol) server that exposes research tools (DuckDuckGo, Wikipedia, arXiv) to agents via a standardised HTTP interface.

**Port:** 8000

### Imports and Setup

```python
import asyncio                    # Async event loop for non-blocking I/O
from functools import partial     # Create partial functions for executor calls
from mcp.server.fastmcp import FastMCP  # FastMCP framework for building MCP servers
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
import wikipedia                  # Wikipedia API wrapper
import logging
import signal, sys, atexit        # Graceful shutdown handling
import os
from ddgs import DDGS             # DuckDuckGo search library
import arxiv                      # arXiv academic paper search
import ssl, urllib.request        # SSL context manipulation
import requests                   # HTTP library
from urllib3.exceptions import InsecureRequestWarning
```

### SSL Workaround (Corporate Proxy)

```python
ssl._create_default_https_context = ssl._create_unverified_context
```
Overrides Python's default SSL context to skip certificate verification. Needed because the corporate proxy performs SSL interception, causing `CERTIFICATE_VERIFY_FAILED` errors.

```python
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
```
Suppresses the "InsecureRequestWarning" that would flood logs when `verify=False`.

```python
_original_session_init = requests.Session.__init__
def _patched_session_init(self, *args, **kwargs):
    _original_session_init(self, *args, **kwargs)
    self.verify = False
requests.Session.__init__ = _patched_session_init
```
**Monkey-patch:** Every new `requests.Session` instance automatically has `verify=False`. This is the key fix — the `arxiv` library creates its own Session internally, and there's no way to pass `verify=False` through its API.

### Environment Variables

```python
os.environ["NO_PROXY"] = "127.0.0.1,localhost,10.215.130.20"  # Bypass proxy for local + Ollama
os.environ["CURL_CA_BUNDLE"] = ""       # Disable CA bundle for curl-based libraries
os.environ["REQUESTS_CA_BUNDLE"] = ""   # Disable CA bundle for requests library
os.environ["PORT"] = "8000"             # Server port
```

### FastMCP Server Initialisation

```python
mcp = FastMCP("ResearchTools")
```
Creates a FastMCP server instance named "ResearchTools". This name appears in tool discovery.

### Tool: `duckduckgo_search`

```python
@mcp.tool()
async def duckduckgo_search(query: str) -> str:
```
- **Decorator:** `@mcp.tool()` registers this function as an MCP tool, making it discoverable by agents.
- **Async wrapper:** The function is async but DuckDuckGo's library is synchronous, so it uses `run_in_executor` to run in a thread pool.
- **Inner `_search()` function:** Creates a `DDGS` context manager, searches for up to 5 results, formats them with title/body/source.
- **Returns:** Formatted string of search results or error message.

### Tool: `wikipedia_search`

```python
@mcp.tool()
async def wikipedia_search(query: str) -> str:
```
- Uses `wikipedia.summary(query, sentences=3)` to get a 3-sentence summary.
- Runs in executor because `wikipedia` library is synchronous.
- Returns the summary text or error message.

### Tool: `arxiv_search`

```python
@mcp.tool()
async def arxiv_search(query: str, max_results: int = 5) -> str:
```
- Creates an `arxiv.Client()` and explicitly sets `client._session.verify = False` (belt-and-suspenders with the monkey-patch).
- Searches for papers sorted by submission date (newest first).
- Formats each paper with: title, authors (max 3 + "et al."), publication date, summary (truncated to 300 chars), PDF URL, and arXiv ID.
- Returns formatted results separated by `---` dividers.

### Graceful Shutdown

```python
def cleanup(): ...
def signal_handler(sig, frame): ...
def setup_signal_handlers(): ...
```
- Registers handlers for SIGINT (Ctrl+C) and SIGTERM.
- `atexit.register(cleanup)` ensures cleanup runs on normal exit.
- Allows the server to shut down cleanly without leaving orphan processes.

### Main Entry Point

```python
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```
Starts the FastMCP server using streamable HTTP transport on port 8000 (from `os.environ["PORT"]`).

---

## src/a2a_1_starlette.py

**Purpose:** HTTP server that wraps the Research Agent and exposes it via the A2A (Agent-to-Agent) protocol. This is the outermost layer — what other agents and clients connect to.

**Port:** 9991

### Key Components

```python
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a_2_executor import LangGraphAgentExecutor
```

### Agent Skills Definition

```python
skills = [
    AgentSkill(id="web_search", name="Web Search (DuckDuckGo)", ...),
    AgentSkill(id="arxiv_search", name="Academic Paper Search (arXiv)", ...),
    AgentSkill(id="wikipedia_search", name="Wikipedia Search", ...),
]
```
Each skill has:
- `id` — unique identifier
- `name` — human-readable name
- `description` — what the skill does (used by other agents to decide whether to delegate)
- `tags` — searchable keywords
- `examples` — sample queries

### Agent Card

```python
agent_card = AgentCard(
    name="LangGraph Agent",
    description="A simple LangGraph agent that does web searchs",
    url="http://localhost:9991/",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    skills=skills,
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True, pushNotifications=True),
)
```
The **Agent Card** is like a business card — it tells other agents what this agent can do, where to reach it, and what protocols it supports. Other agents fetch this card to decide whether to delegate work here.

### Server Assembly

```python
request_handler = DefaultRequestHandler(
    agent_executor=LangGraphAgentExecutor(),  # The executor that runs the agent
    task_store=InMemoryTaskStore(),           # Tasks stored in memory (lost on restart)
)

server = A2AStarletteApplication(
    http_handler=request_handler,
    agent_card=agent_card,
)

uvicorn.run(server.build(), host="0.0.0.0", port=9991)
```
- `DefaultRequestHandler` handles incoming A2A protocol messages and routes them to the executor.
- `InMemoryTaskStore` tracks task state (submitted, working, completed).
- `A2AStarletteApplication` builds a Starlette ASGI app with A2A endpoints.
- `uvicorn.run()` starts the HTTP server on all interfaces, port 9991.

---

## src/a2a_2_executor.py

**Purpose:** Task execution engine that bridges between the A2A protocol layer and the LangGraph agent. Manages task lifecycle (submit → working → completed).

### Class: `LangGraphAgentExecutor`

Implements the `AgentExecutor` interface from `a2a-sdk`.

#### `__init__(self)`
```python
self.agent = langG_agent()
```
Creates an instance of the LangGraph agent (from `a2a_3_agent.py`).

#### `execute(self, context, event_queue)`

This is called every time a message arrives:

1. **Validate inputs:** Checks that `task_id`, `context_id`, and `message` exist.
2. **Create TaskUpdater:** Used to send status updates back to the client.
3. **Submit task:** If this is a new task, marks it as submitted.
4. **Start work:** Transitions task to "working" state.
5. **Stream agent response:** Iterates over the agent's streaming output:
   - If `is_task_complete=False` and `require_user_input=False` → update status to "working" (intermediate progress)
   - If `require_user_input=True` → update status to "input_required" (agent needs more info)
   - If `is_task_complete=True` → add artifact (final answer) and mark complete

#### `cancel(self, context, event_queue)`
```python
raise ServerError(error=UnsupportedOperationError())
```
Cancellation is not implemented — raises an error if attempted.

---

## src/a2a_3_agent.py

**Purpose:** The core Research Agent — a LangGraph ReAct agent that reasons using `mistral-nemo` and calls MCP tools to gather information.

### Class: `ResponseFormat` (Pydantic Model)

```python
class ResponseFormat(BaseModel):
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str
```
Defines the structured output format the LLM must produce. LangGraph uses this to extract a structured response from the agent's final output.

### Class: `langG_agent`

#### `SYSTEM_INSTRUCTION`
The system prompt that tells the LLM:
- It's a research assistant
- It can make multiple tool calls
- It should set status to `input_required`, `error`, or `completed` based on the situation

#### `__init__(self)`
```python
self.model = ChatOllama(base_url="http://10.215.130.20:11434", model="mistral-nemo", temperature=0)
self.tools = None
self.graph = None
self._initialized = False
```
- Uses `ChatOllama` to connect to the remote Ollama server.
- `temperature=0` makes responses deterministic (no randomness).
- Tools and graph are lazily initialised (async components can't be created in `__init__`).

#### `_initialize(self)` (async)
```python
self.tools = await self._get_mcp_tools()
self.graph = create_react_agent(
    self.model,
    tools=self.tools,
    checkpointer=memory,
    prompt=self.SYSTEM_INSTRUCTION,
    response_format=ResponseFormat,
)
```
- Fetches available tools from the MCP server.
- Creates a **ReAct agent** — this is LangGraph's built-in agent that follows the Reason-Act-Observe loop:
  1. **Reason:** LLM decides what to do
  2. **Act:** Calls a tool
  3. **Observe:** Processes the tool result
  4. Repeat until the LLM decides it has enough info
- `checkpointer=memory` enables conversation memory across turns.
- `response_format=ResponseFormat` forces the LLM to output structured JSON at the end.

#### `stream(self, query, context_id)` (async generator)

Token-by-token streaming using `astream_events`:

- **`on_chat_model_stream`** — Individual LLM tokens as they're generated. Yielded immediately for real-time display.
- **`on_tool_start`** — A tool is about to be called. Yields "🔧 Using tool: {name}".
- **`on_tool_end`** — A tool finished. Yields "✅ Tool {name} completed".
- **`on_chain_error`** — An error occurred. Yields error message and stops.
- After all events, yields the final structured response via `get_agent_response()`.

#### `get_agent_response(self, config)`

Extracts the structured response from the agent's state:
```python
current_state = self.graph.get_state(config)
structured_response = current_state.values.get("structured_response")
```
Maps the `ResponseFormat` status to the dict format expected by the executor.

#### `_get_mcp_tools(self)` (async)

```python
mcp_client = MultiServerMCPClient({
    "research": {
        "url": "http://localhost:8000/mcp/",
        "transport": "streamable_http",
    }
})
tools = await mcp_client.get_tools()
```
Connects to the MCP server and retrieves all available tools. These become callable functions that the LangGraph agent can invoke during reasoning.

---

## src/client.py

**Purpose:** Interactive terminal client that connects to the Orchestrator Agent and provides a chat interface for the user.

### Configuration

```python
os.environ["NO_PROXY"] = "127.0.0.1,localhost,10.215.130.20"
BASE_URL = "http://localhost:9990"  # Connects to Orchestrator

timeout_config = httpx.Timeout(
    connect=30.0,   # 30s to establish connection
    read=120.0,     # 120s to wait for response (LLM can be slow)
    write=10.0,     # 10s to send request
    pool=5.0,       # 5s to get a connection from pool
)
```

### `main()` Function

1. **Connect to agent:** Fetches the agent card from `BASE_URL` to verify the agent is running.
2. **Create A2A client:** Uses `ClientFactory` to create a client configured for the agent's capabilities.
3. **Conversation loop:**
   - Reads user input
   - Special commands: `quit`/`exit`/`q` to exit, `card` to show agent capabilities
   - Builds an A2A `Message` with a unique ID and the user's text
   - Sends via `client.send_message(message)` and iterates over streaming events
   - **Deduplication:** Uses `seen_content` set to avoid printing the same chunk twice
   - Prints status messages and artifacts as they arrive

### Event Processing

The client handles three types of events:
- **Status messages** — Intermediate progress (e.g., "working on it...")
- **Singular artifact** — The final answer from the agent
- **Plural artifacts** — Multiple result artifacts (if the agent produces several)

---

## src/mcp_test_client.py

**Purpose:** Standalone test client for debugging the MCP server + LLM integration without the A2A protocol layer.

### What It Does

1. Connects to MCP server at `http://localhost:8000/mcp/`
2. Lists available tools
3. Tests model reachability with a simple "Hello!" prompt
4. Creates a ReAct agent with the MCP tools
5. Offers two streaming modes:
   - **Mode 1 (State-based):** Shows complete messages at each state transition
   - **Mode 2 (Token-by-token):** Real-time character-by-character output
6. Runs an interactive chat loop

### Key Difference from Full Stack

This bypasses the A2A protocol entirely — it directly creates a LangGraph agent and talks to it. Useful for:
- Testing if MCP tools work correctly
- Debugging LLM reasoning without A2A overhead
- Verifying model connectivity

---

## src/orchestrator/o1_server.py

**Purpose:** HTTP server for the Orchestrator Agent — the coordinator that decides whether to answer directly or delegate to the Research Agent.

**Port:** 9990

### Key Differences from `a2a_1_starlette.py`

1. **Metrics Middleware:** Adds `MetricsMiddleware` to track request latencies and error rates.
2. **Background metrics logging:** A daemon thread logs metrics every 30 seconds.
3. **Metrics persistence:** On shutdown (SIGINT, SIGTERM, or normal exit), saves metrics to `metrics_log.json`.
4. **Different skills:** Defines "Planning" and "Delegation" skills instead of research tools.

### Agent Card

```python
agent_card = AgentCard(
    name="Orchestrator Agent",
    description="Coordinates multiple agents via A2A",
    url="http://localhost:9990/",
    ...
)
```

### Metrics Background Thread

```python
threading.Thread(target=log_metrics_periodically, daemon=True).start()
```
Runs `metrics.log_summary()` every 30 seconds in the background. `daemon=True` means it dies when the main process exits.

### Shutdown Hooks

```python
signal.signal(signal.SIGINT, lambda sig, frame: save_metrics_on_exit() or exit(0))
atexit.register(save_metrics_on_exit)
```
Ensures metrics are saved to disk regardless of how the server stops.

---

## src/orchestrator/o2_executor.py

**Purpose:** Task executor for the Orchestrator Agent. Same pattern as `a2a_2_executor.py` but simpler — no streaming, just invoke and return.

### Key Differences from Research Agent Executor

1. **No streaming:** Calls `self.agent.invoke()` (single response) instead of `self.agent.stream()` (streaming).
2. **Metrics recording:** Records task duration via `MetricsCollector`.
3. **Verbose logging:** Logs every step (context validation, task creation, agent invocation, completion).

### Flow

```
execute() called
  → Validate context (task_id, context_id, message)
  → Submit task (if new)
  → Start work
  → Invoke orchestrator agent
  → Create artifact with response content
  → Mark task complete
  → Record duration metric
```

---

## src/orchestrator/o3_agent.py

**Purpose:** The Orchestrator Agent — a LangGraph StateGraph that routes requests either to direct LLM answering or to the Research Agent via A2A delegation.

### Schemas

```python
class OrchestratorState(TypedDict):
    user_input: str              # The user's original query
    plan: str | None             # "Answer directly" or "Delegate to research agent"
    needs_delegation: bool       # Whether to delegate
    delegated_result: str | None # Result from the research agent (if delegated)
    final_response: str | None   # The final answer to return
```

### Class: `OrchestratorAgent`

#### `__init__(self)`
```python
self.llm = "qwen3:4b"
self.model = ChatOllama(base_url="http://10.215.130.20:11434", model=self.llm, temperature=0)
```
Uses the lightweight `qwen3:4b` model for fast routing decisions.

#### `plan(self, state)` — Node 1

```python
needs_delegation = any(
    k in state["user_input"].lower()
    for k in ["research", "search", "wikipedia", "paper"]
)
```
Simple keyword-based routing. If the user's input contains any of these keywords, the request is delegated to the Research Agent. Otherwise, the orchestrator answers directly.

#### `synthesize(self, state)` — Node 3

Two paths:
- **If delegated:** Wraps the delegated result with "Synthesized answer:\n{result}"
- **If direct:** Invokes `qwen3:4b` with the user's question and returns the LLM's response

### Function: `run_a2a_with_print(client, message)`

Handles the A2A communication with the Research Agent:

1. Sends the message via `client.send_message(message)`
2. Iterates over streaming events
3. **Status messages:** Printed to terminal for visibility but NOT included in the return value
4. **Artifacts (final answer):** Printed AND collected into `artifact_buffer`
5. Returns only the artifact content (the actual answer)

This separation prevents raw tool metadata (`[TOOL_CALLS]`, `🔧 Using tool:...`) from appearing in the final response.

### Class: `OrchestratorGraph`

#### `delegate(self, state)` — Node 2

1. Increments metrics counters (`inter_agent_messages`, `retrievals`)
2. Resolves the Research Agent's card at `http://localhost:9991`
3. Creates an A2A client
4. Sends the user's input as a message
5. Collects the response via `run_a2a_with_print()`
6. Returns the delegated result in state

#### `build(self)` — Graph Construction

```python
graph = StateGraph(OrchestratorState)
graph.add_node("plan", self.agent.plan)
graph.add_node("delegate", self.delegate)
graph.add_node("synthesize", self.agent.synthesize)
graph.set_entry_point("plan")
graph.add_conditional_edges(
    "plan",
    lambda state: state["needs_delegation"],
    {True: "delegate", False: "synthesize"},
)
graph.add_edge("delegate", "synthesize")
graph.add_edge("synthesize", END)
return graph.compile(checkpointer=memory)
```

**Graph flow:**
```
START → plan → [needs_delegation?]
                 ├─ True  → delegate → synthesize → END
                 └─ False → synthesize → END
```

### Class: `Orchestrator` (Wrapper)

```python
class Orchestrator:
    def __init__(self):
        self.agent = OrchestratorAgent()
        self.graph = OrchestratorGraph(self.agent).build()

    async def invoke(self, query, context_id):
        config = {"configurable": {"thread_id": context_id}}
        result = await self.graph.ainvoke({"user_input": query}, config)
        return {
            "is_task_complete": True,
            "require_user_input": False,
            "content": result.get("final_response", ""),
        }
```
Simple wrapper that the executor calls. Invokes the graph and extracts the final response.

---

## src/orchestrator/metrics.py

**Purpose:** Singleton metrics collector that tracks performance data across all layers of the orchestrator.

### Pattern: Thread-Safe Singleton

```python
class MetricsCollector:
    _instance = None
    _lock = Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = MetricsCollector()
        return cls._instance
```
Double-checked locking ensures only one instance exists, even with concurrent access.

### Metrics Tracked

| Layer | Metrics |
|-------|---------|
| **HTTP (Starlette)** | `requests_total`, `errors_total`, `submission_latencies` |
| **Executor** | `task_durations` |
| **LangGraph** | `tokens_total`, `tokens_prompt`, `tokens_completion`, `ai_messages_count`, `reasoning_steps` |
| **Inter-Agent** | `inter_agent_messages`, `tool_calls`, `tools_used`, `retrievals` |
| **Model** | `model` (name of LLM in use) |

### Key Methods

#### `record_request(duration, status_code)`
Called by the middleware for every HTTP request. Tracks latency and error rate.

#### `record_task_duration(duration)`
Called by the executor when a task completes.

#### `record_langgraph_invoke(result, duration)`
Extracts metrics from LangChain message objects:
- Token usage (input/output/total)
- Tool calls made
- Model info from response metadata

#### `summary()`
Computes derived metrics:
- `avg_latency` — average HTTP request latency
- `avg_task_duration` — average time to complete a task
- `tokens_per_request` — average tokens used per request
- `tools_per_request` — average tool calls per request

---

## src/orchestrator/metrics_middleware.py

**Purpose:** Starlette middleware that wraps every HTTP request to record timing and status metrics.

```python
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        metrics = MetricsCollector.get_instance()
        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            metrics.record_request(time.time() - start_time, 500)
            raise

        duration = time.time() - start_time
        metrics.record_request(duration, status)
        return response
```

**How it works:**
1. Records the start time before passing the request to the next handler
2. If an exception occurs, records it as a 500 error
3. Otherwise, records the actual status code and duration
4. This runs for EVERY request to the orchestrator server

---

## Summary: How Files Connect

```
client.py
    → connects to o1_server.py (port 9990)
        → uses o2_executor.py to manage tasks
            → calls o3_agent.py (Orchestrator)
                → either answers directly (qwen3:4b)
                → or delegates to a2a_1_starlette.py (port 9991)
                    → uses a2a_2_executor.py to manage tasks
                        → calls a2a_3_agent.py (Research Agent)
                            → reasons with mistral-nemo
                            → calls tools on mcp_server.py (port 8000)
                                → DuckDuckGo / Wikipedia / arXiv
```

Each layer adds a specific responsibility:
- **Server files** (`o1_server.py`, `a2a_1_starlette.py`) — HTTP transport + A2A protocol
- **Executor files** (`o2_executor.py`, `a2a_2_executor.py`) — Task lifecycle management
- **Agent files** (`o3_agent.py`, `a2a_3_agent.py`) — Actual reasoning logic
- **MCP server** (`mcp_server.py`) — Tool execution
- **Client** (`client.py`) — User interface
- **Metrics** (`metrics.py`, `metrics_middleware.py`) — Observability
