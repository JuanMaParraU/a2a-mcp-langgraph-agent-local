# Changes Made to Run Locally

This document details all modifications made to the original `mas` branch to get the system running on a local Windows machine within a corporate network environment.

**Branch:** `pw-agentic` (created from `mas`)

---

## Summary of Changes

| Category | Change | Files Affected |
|----------|--------|----------------|
| Model Configuration | Changed Ollama model references | `a2a_3_agent.py`, `o3_agent.py`, `mcp_test_client.py` |
| Network/Proxy | Added `10.215.130.20` to `NO_PROXY` | `a2a_3_agent.py`, `client.py`, `o3_agent.py`, `mcp_server.py` |
| SSL Fix | Disabled SSL verification for corporate proxy | `mcp_server.py` |
| Bug Fix | Fixed orchestrator returning raw tool metadata | `o3_agent.py` |
| Windows Support | Added Windows batch launcher | `start_agents.bat` (new) |
| Documentation | Added file docs and running guide | `FILE_DOCUMENTATION.md`, `RUNNING_GUIDE.md` (new) |

---

## 1. Model Configuration Changes

### `src/a2a_3_agent.py`

**Original:**
```python
self.model = ChatOllama(base_url="http://10.215.130.20:11434", model="mistral-nemo", temperature=0)
```

**No change to model** — kept `mistral-nemo` as the research agent model. Only the `NO_PROXY` was updated (see section 2).

---

### `src/orchestrator/o3_agent.py`

**Original:**
```python
self.llm = "gemma3:1b"
self.model = ChatOllama(model=self.llm, temperature=0)
```

**Changed to:**
```python
self.llm = "qwen3:4b"
self.model = ChatOllama(base_url="http://10.215.130.20:11434", model=self.llm, temperature=0)
```

**Reason:** 
- `gemma3:1b` is not available on the Ollama server at `10.215.130.20`
- `qwen3:4b` is available and well-suited for the orchestrator's lightweight routing task (fast, good instruction-following)
- Added explicit `base_url` since the original code relied on Ollama's default localhost which doesn't apply here

---

### `src/mcp_test_client.py`

**Original:**
```python
model = ChatOllama(model="mistral")
```

**Changed to:**
```python
model = ChatOllama(base_url="http://10.215.130.20:11434", model="mistral-nemo")
```

**Reason:** Added explicit `base_url` to point to the remote Ollama server and updated model to `mistral-nemo` for consistency.

---

## 2. Network/Proxy Configuration

All files that make HTTP connections had their `NO_PROXY` environment variable updated to include the Ollama server IP, preventing the corporate proxy from intercepting local traffic.

### Files changed:
- `src/a2a_3_agent.py`
- `src/client.py`
- `src/mcp_server.py`
- `src/orchestrator/o3_agent.py`

**Original:**
```python
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
```

**Changed to:**
```python
os.environ["NO_PROXY"] = "127.0.0.1,localhost,10.215.130.20"
```

**Reason:** Without this, the corporate proxy intercepts requests to the Ollama server at `10.215.130.20:11434`, causing connection failures or SSL issues.

---

## 3. SSL Certificate Verification Fix

### `src/mcp_server.py`

**Problem:** The corporate network uses a proxy that performs SSL interception (man-in-the-middle for inspection). This causes `SSL: CERTIFICATE_VERIFY_FAILED` errors when the MCP tools (arXiv, Wikipedia, DuckDuckGo) try to connect to external HTTPS APIs.

**Changes added at the top of the file:**

```python
import requests
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL verification globally
ssl._create_default_https_context = ssl._create_unverified_context

# Suppress InsecureRequestWarning when verify=False is used
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Monkey-patch requests.Session to disable SSL verification by default
_original_session_init = requests.Session.__init__
def _patched_session_init(self, *args, **kwargs):
    _original_session_init(self, *args, **kwargs)
    self.verify = False
requests.Session.__init__ = _patched_session_init

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
```

**Additionally, in the `arxiv_search` tool function:**

```python
client = arxiv.Client()
# Disable SSL verification for corporate proxy environments
client._session.verify = False
```

**Reason:** 
- `ssl._create_default_https_context` fixes Python's built-in `urllib` (used by Wikipedia)
- The `requests.Session` monkey-patch fixes the `requests` library (used by arXiv, DuckDuckGo)
- `client._session.verify = False` is a belt-and-suspenders fix specifically for the arxiv client which creates its own session
- `CURL_CA_BUNDLE=""` and `REQUESTS_CA_BUNDLE=""` are environment variables respected by various HTTP libraries

---

## 4. Orchestrator Response Bug Fix

### `src/orchestrator/o3_agent.py` — `run_a2a_with_print()` function

**Problem:** When the orchestrator delegated to the research agent, it collected ALL streamed content (including intermediate tool call metadata like `[TOOL_CALLS]`, `🔧 Using tool: ...`, `✅ Tool completed`) into the response buffer. This raw metadata was then returned to the user as the "answer".

**Original behaviour:**
```
User: "Use wikipedia to explain TCP/IP"
Response: "Synthesized answer: [TOOL_CALLS][{"name": "wikipedia_search"...}] Searching Wikipedia..."
```

**Fix:** Changed `run_a2a_with_print()` to separate status messages (printed for visibility but discarded) from artifacts (the actual final answer, kept as the result).

**Key change:**
```python
# Status messages — print but DON'T include in result
if hasattr(event, "status") and event.status ...
    print(content, end="", flush=True)  # visible in terminal
    # NOT added to artifact_buffer

# Artifacts (final answer) — print AND include in result
if hasattr(event, "artifact") and event.artifact:
    artifact_buffer.append(content)  # this is the actual answer
```

**Result:** Only the final processed answer from the research agent is returned to the user, not the intermediate streaming noise.

---

## 5. New Files Added

### `start_agents.bat`

A Windows batch script that launches the three server processes (MCP, Research Agent, Orchestrator) in separate terminal windows with staggered delays.

**Usage:**
```cmd
start_agents.bat
```

Then manually open a 4th terminal for the client:
```cmd
.venv\Scripts\python.exe src\client.py
```

---

### `FILE_DOCUMENTATION.md`

Comprehensive documentation explaining every file in the repository, including purpose, key components, classes/methods, and how they fit into the architecture.

---

### `RUNNING_GUIDE.md`

Step-by-step guide for running the system on Windows, including:
- Prerequisites
- Terminal-by-terminal startup instructions
- Test commands
- Architecture flow diagram
- Troubleshooting table

---

### `CHANGES.md` (this file)

Documents all modifications made to adapt the codebase for local execution.

---

## Environment Details

| Component | Value |
|-----------|-------|
| OS | Windows 10/11 |
| Python | 3.13.7 |
| Ollama Server | `http://10.215.130.20:11434` |
| Research Agent Model | `mistral-nemo` (12.2B, Q4_0) |
| Orchestrator Model | `qwen3:4b` (4.0B, Q4_K_M) |
| Virtual Environment | `.venv\` (created with `python -m venv`) |
| Package Manager | pip (from requirements.txt) + manual `pip install arxiv` |

---

## Dependencies Not in `requirements.txt`

The following package needed to be installed manually as it was missing from the exported requirements:

```cmd
.venv\Scripts\pip.exe install arxiv
```

This installs `arxiv`, `feedparser`, and `sgmllib3k`.

---

## Known Limitations

1. **SSL verification is disabled** — This is a workaround for the corporate proxy. In a non-corporate environment, remove the SSL patches and let verification work normally.
2. **First request is slow** — Ollama needs to load the model into GPU/RAM on first use. Subsequent requests are much faster.
3. **DuckDuckGo may be blocked** — Some corporate networks block DuckDuckGo. If searches fail, Wikipedia and arXiv tools still work.
4. **MDE security scanner noise** — Microsoft Defender for Endpoint probes open ports with JNDI/Log4j payloads. These 404 errors in the MCP server logs are harmless and can be ignored.
