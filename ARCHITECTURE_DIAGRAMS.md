# Architecture Diagrams

## 1. Project Architecture Overview

```mermaid
%%{init: {'theme': 'dark'}}%%
graph TB
    subgraph User["👤 User"]
        Terminal["Terminal / CLI"]
    end

    subgraph Client["📱 Client Layer"]
        ClientPy["client.py<br/>Interactive A2A Client<br/>Port: connects to 9990"]
    end

    subgraph Orchestrator["🧭 Orchestrator Agent (Port 9990)"]
        O1["o1_server.py<br/>Starlette HTTP Server<br/>+ Metrics Middleware"]
        O2["o2_executor.py<br/>Task Executor<br/>Lifecycle Management"]
        O3["o3_agent.py<br/>LangGraph StateGraph<br/>Plan → Delegate/Synthesize"]
    end

    subgraph Research["🔬 Research Agent (Port 9991)"]
        A1["a2a_1_starlette.py<br/>Starlette HTTP Server<br/>A2A Protocol"]
        A2["a2a_2_executor.py<br/>Task Executor<br/>Streaming Support"]
        A3["a2a_3_agent.py<br/>LangGraph ReAct Agent<br/>Reasoning + Tool Use"]
    end

    subgraph MCP["🔌 MCP Server (Port 8000)"]
        MCPServer["mcp_server.py<br/>FastMCP Server<br/>Streamable HTTP"]
        subgraph Tools["⚙️ Research Tools"]
            DDG["🔍 DuckDuckGo<br/>Web Search"]
            Wiki["📖 Wikipedia<br/>Encyclopedia"]
            Arxiv["📚 arXiv<br/>Academic Papers"]
        end
    end

    subgraph LLM["🧠 Ollama LLM Server (Port 11434)"]
        Mistral["mistral-nemo<br/>12.2B params<br/>Research & Reasoning"]
        Qwen["qwen3:4b<br/>4.0B params<br/>Routing & Direct Answers"]
    end

    Terminal -->|"user input"| ClientPy
    ClientPy -->|"A2A POST /send_message"| O1
    O1 --> O2
    O2 --> O3
    O3 -->|"Direct Answer"| Qwen
    O3 -->|"A2A Delegation"| A1
    A1 --> A2
    A2 --> A3
    A3 -->|"Reasoning"| Mistral
    A3 -->|"MCP Tool Calls"| MCPServer
    MCPServer --> DDG
    MCPServer --> Wiki
    MCPServer --> Arxiv

    style User fill:#37474f,stroke:#90a4ae,color:#eceff1
    style Orchestrator fill:#1a237e,stroke:#5c6bc0,color:#e8eaf6
    style Research fill:#1b5e20,stroke:#66bb6a,color:#e8f5e9
    style MCP fill:#e65100,stroke:#ffb74d,color:#fff3e0
    style LLM fill:#880e4f,stroke:#f06292,color:#fce4ec
```

---

## 2. Request Flow — Direct Answer

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant U as 👤 User
    participant C as Client (client.py)
    participant O as Orchestrator (9990)
    participant Q as Qwen3:4b (LLM)

    U->>C: "What is quantum computing?"
    C->>O: A2A POST /send_message
    O->>O: Plan: No keywords match → Answer directly
    O->>Q: ainvoke("What is quantum computing?")
    Q-->>O: Response text
    O-->>C: Artifact: final answer
    C-->>U: Display answer
```

---

## 3. Request Flow — Delegated Research

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    participant U as 👤 User
    participant C as Client (client.py)
    participant O as Orchestrator (9990)
    participant R as Research Agent (9991)
    participant M as MCP Server (8000)
    participant LLM as mistral-nemo (LLM)

    U->>C: "Search for papers on LLMs"
    C->>O: A2A POST /send_message
    O->>O: Plan: "search" keyword → Delegate
    O->>R: A2A POST /send_message
    R->>LLM: "Search for papers on LLMs"
    LLM-->>R: Tool call: arxiv_search("LLMs")
    R->>M: MCP tool call: arxiv_search
    M->>M: Query arXiv API
    M-->>R: Paper results (formatted)
    R->>LLM: Tool result + context
    LLM-->>R: Final synthesized answer
    R-->>O: Artifact: research results
    O-->>C: Artifact: "Synthesized answer: ..."
    C-->>U: Display results
```

---

## 4. Orchestrator Decision Graph

```mermaid
%%{init: {'theme': 'dark'}}%%
graph LR
    Start([User Input]) --> Plan

    subgraph StateGraph["LangGraph StateGraph"]
        Plan["🧭 Plan Node<br/>Check keywords:<br/>research, search,<br/>wikipedia, paper"]
        Delegate["📤 Delegate Node<br/>Send to Research Agent<br/>via A2A (port 9991)"]
        Synthesize["✍️ Synthesize Node<br/>Generate final response"]
    end

    Plan -->|"keywords found"| Delegate
    Plan -->|"no keywords"| Synthesize
    Delegate --> Synthesize
    Synthesize --> End([Return Response])

    style Plan fill:#1565c0,stroke:#64b5f6,color:#e3f2fd
    style Delegate fill:#2e7d32,stroke:#81c784,color:#e8f5e9
    style Synthesize fill:#f9a825,stroke:#fff176,color:#212121
    style StateGraph fill:#263238,stroke:#546e7a,color:#eceff1
```

---

## 5. Research Agent ReAct Loop

```mermaid
%%{init: {'theme': 'dark'}}%%
graph TD
    Input([User Query]) --> Agent

    subgraph ReAct["LangGraph ReAct Agent"]
        Agent["🤖 Agent<br/>mistral-nemo LLM"]
        Think["💭 Think<br/>Decide next action"]
        Act["⚡ Act<br/>Call MCP Tool"]
        Observe["👁️ Observe<br/>Process tool result"]
        Respond["📝 Respond<br/>Generate final answer"]
    end

    Agent --> Think
    Think -->|"Need more info"| Act
    Act -->|"MCP call"| ToolsNode
    ToolsNode["🔌 MCP Tools<br/>DuckDuckGo / Wikipedia / arXiv"]
    ToolsNode -->|"Result"| Observe
    Observe --> Think
    Think -->|"Have enough info"| Respond
    Respond --> Output([Final Answer])

    style ReAct fill:#1b5e20,stroke:#66bb6a,color:#e8f5e9
    style ToolsNode fill:#e65100,stroke:#ffb74d,color:#fff3e0
```

---

## 6. Changes Made for Local Execution

```mermaid
%%{init: {'theme': 'dark'}}%%
graph TB
    subgraph Original["❌ Original Configuration"]
        direction TB
        OldModel["Model: gemma3:1b<br/>(not available locally)"]
        OldProxy["NO_PROXY: 127.0.0.1,localhost<br/>(missing Ollama IP)"]
        OldSSL["SSL: Default verification<br/>(fails behind corporate proxy)"]
        OldResponse["Response: Returns all<br/>streamed content including<br/>raw tool metadata"]
        OldOS["Platform: Linux/macOS<br/>(tmux launcher only)"]
    end

    subgraph Fixed["✅ Local Configuration"]
        direction TB
        NewModel["Model: qwen3:4b<br/>(available on server,<br/>fast for routing)"]
        NewProxy["NO_PROXY: 127.0.0.1,<br/>localhost,10.215.130.20<br/>(includes Ollama server)"]
        NewSSL["SSL: Verification disabled<br/>via Session monkey-patch<br/>+ env vars"]
        NewResponse["Response: Returns only<br/>final artifact content<br/>(clean answers)"]
        NewOS["Platform: Windows<br/>(start_agents.bat added)"]
    end

    OldModel -->|"Changed"| NewModel
    OldProxy -->|"Fixed"| NewProxy
    OldSSL -->|"Patched"| NewSSL
    OldResponse -->|"Bug fixed"| NewResponse
    OldOS -->|"Added"| NewOS

    style Original fill:#b71c1c,stroke:#ef5350,color:#ffcdd2
    style Fixed fill:#1b5e20,stroke:#66bb6a,color:#c8e6c9
```

---

## 7. Network Topology — Local Setup

```mermaid
%%{init: {'theme': 'dark'}}%%
graph LR
    subgraph LocalMachine["🖥️ Local Windows Machine"]
        Client["client.py"]
        Orch["Orchestrator<br/>:9990"]
        Research["Research Agent<br/>:9991"]
        MCPSrv["MCP Server<br/>:8000"]
    end

    subgraph Remote["🖧 Remote Server (10.215.130.20)"]
        Ollama["Ollama<br/>:11434"]
        MistralModel["mistral-nemo"]
        QwenModel["qwen3:4b"]
    end

    subgraph Internet["🌐 External APIs"]
        ArxivAPI["export.arxiv.org"]
        WikiAPI["en.wikipedia.org"]
        DDGAPI["duckduckgo.com"]
    end

    subgraph Proxy["🔒 Corporate Proxy"]
        ProxyServer["SSL Intercepting<br/>Proxy"]
    end

    Client -->|"localhost"| Orch
    Orch -->|"localhost"| Research
    Research -->|"localhost"| MCPSrv
    Orch -->|"NO_PROXY bypass"| Ollama
    Research -->|"NO_PROXY bypass"| Ollama
    Ollama --- MistralModel
    Ollama --- QwenModel
    MCPSrv -->|"verify=False"| ProxyServer
    ProxyServer -->|"SSL intercept"| ArxivAPI
    ProxyServer -->|"SSL intercept"| WikiAPI
    ProxyServer -->|"SSL intercept"| DDGAPI

    style LocalMachine fill:#1a237e,stroke:#5c6bc0,color:#e8eaf6
    style Remote fill:#880e4f,stroke:#f06292,color:#fce4ec
    style Internet fill:#4a148c,stroke:#ba68c8,color:#f3e5f5
    style Proxy fill:#e65100,stroke:#ffb74d,color:#fff3e0
```

---

## 8. File Change Map

```mermaid
%%{init: {'theme': 'dark'}}%%
graph TD
    subgraph Modified["📝 Modified Files"]
        A3["src/a2a_3_agent.py<br/>• NO_PROXY updated"]
        ClientFile["src/client.py<br/>• NO_PROXY updated"]
        MCPFile["src/mcp_server.py<br/>• NO_PROXY updated<br/>• SSL verification disabled<br/>• requests.Session patched<br/>• arxiv client.verify=False"]
        O3File["src/orchestrator/o3_agent.py<br/>• Model → qwen3:4b<br/>• base_url added<br/>• NO_PROXY updated<br/>• run_a2a_with_print fixed"]
        TestClient["src/mcp_test_client.py<br/>• base_url added<br/>• Model → mistral-nemo"]
    end

    subgraph NewFiles["🆕 New Files"]
        Bat["start_agents.bat<br/>Windows launcher"]
        FileDocs["FILE_DOCUMENTATION.md<br/>Detailed file descriptions"]
        RunGuide["RUNNING_GUIDE.md<br/>Step-by-step execution"]
        Changes["CHANGES.md<br/>Change log"]
        Diagrams["ARCHITECTURE_DIAGRAMS.md<br/>Mermaid diagrams (this file)"]
    end

    style Modified fill:#f57f17,stroke:#ffee58,color:#212121
    style NewFiles fill:#1b5e20,stroke:#66bb6a,color:#c8e6c9
```

---

## Port Reference

```mermaid
%%{init: {'theme': 'dark'}}%%
graph LR
    subgraph Ports["Service Ports"]
        P8000["🔌 Port 8000<br/>MCP Server<br/>mcp_server.py"]
        P9990["🧭 Port 9990<br/>Orchestrator<br/>o1_server.py"]
        P9991["🔬 Port 9991<br/>Research Agent<br/>a2a_1_starlette.py"]
        P11434["🧠 Port 11434<br/>Ollama LLM<br/>10.215.130.20"]
    end

    P9990 -->|"delegates to"| P9991
    P9991 -->|"calls tools on"| P8000
    P9990 -->|"LLM inference"| P11434
    P9991 -->|"LLM inference"| P11434

    style P8000 fill:#e65100,stroke:#ffb74d,color:#fff3e0
    style P9990 fill:#1565c0,stroke:#64b5f6,color:#e3f2fd
    style P9991 fill:#2e7d32,stroke:#81c784,color:#e8f5e9
    style P11434 fill:#880e4f,stroke:#f06292,color:#fce4ec
    style Ports fill:#263238,stroke:#546e7a,color:#eceff1
```
