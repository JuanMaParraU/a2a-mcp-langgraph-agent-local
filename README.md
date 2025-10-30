# A2A MCP LangGraph Agent Local

> A fully local, open-source agentic AI system combining LangGraph, Model Context Protocol (MCP), and Agent-to-Agent (A2A) communication — no subscriptions, no cloud APIs, complete control.

**📖 Want to understand the architecture and concepts?** Read the [full blog post](https://your-blog-link.com)

---

## 🎯 What This Does

This project demonstrates a complete agentic AI stack running entirely on your machine:

- **🧭 LangGraph** orchestrates multi-agent workflows
- **🔌 MCP** provides standardized tool access
- **💬 A2A** enables agent-to-agent communication
- **⚙️ Ollama** serves local LLMs for reasoning

**Use cases:** Build research assistants, automated workflows, multi-agent systems, or experiment with agentic patterns — all without external API costs or data leaving your machine.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **8GB+ RAM** (16GB recommended for larger models)
- **tmux** (for running multiple services)
- **macOS, Linux, or Windows with WSL**

### Step 1: Install Dependencies

**Install tmux:**

macOS:
```bash
brew install tmux
```

Ubuntu/Debian:
```bash
sudo apt-get install tmux
```

**Install Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Start Ollama and download model:**
```bash
ollama serve
ollama run mistral-nemo
```

### Step 2: Clone and Setup

```bash
git clone https://github.com/JuanMaParraU/a2a-mcp-langgraph-agent-local.git
cd a2a-mcp-langgraph-agent-local
```

**Setup Python environment:**

Using `uv` (recommended):
```bash
uv sync
source .venv/bin/activate
```

Using standard venv:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Launch the System

```bash
chmod +x start_agents.sh
./start_agents.sh
```

This launches three services in separate tmux windows:
- **Window 0 (MCP):** MCP Server providing tools
- **Window 1 (Agent):** Agent Server with A2A + LangGraph
- **Window 2 (Client):** Interactive client for sending tasks

---

## 🎮 Managing the Session

### Switching Between Windows

```
Ctrl+b then 0  →  MCP Server
Ctrl+b then 1  →  Agent Server
Ctrl+b then 2  →  Client
```

Or cycle through:
```
Ctrl+b then n  →  Next window
Ctrl+b then p  →  Previous window
```

### Detach and Reattach

**Detach** (leave running in background):
```
Ctrl+b then d
```

**Reattach:**
```bash
tmux attach -t agentic-ai
```

### Stop the System

```bash
tmux kill-session -t agentic-ai
```

---

## 📁 Project Structure

For detailed file descriptions, customization options, and examples, see the [src/ folder documentation](src/README.md).

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         LangGraph StateGraph            │
│  ┌───────────┐      ┌───────────┐      │
│  │  Agent 1  │ ←──→ │  Agent 2  │      │
│  └─────┬─────┘      └─────┬─────┘      │
│        │ A2A Messages     │             │
└────────┼──────────────────┼─────────────┘
         │                  │
         ↓                  ↓
    ┌────────────────────────────┐
    │      MCP Tool Layer        │
    │  (File, Web, DB access)    │
    └────────────────────────────┘
              ↓
    ┌────────────────────────────┐
    │   Ollama (Local Models)    │
    │      (mistral-nemo)        │
    └────────────────────────────┘
```

**Read more:** [Blog post with detailed architecture explanation](https://your-blog-link.com)

---

## 🐛 Troubleshooting

### Ollama Connection Issues

**Error:** `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution:** Make sure Ollama is running:
```bash
ollama serve
```

### Model Not Found

**Error:** `Model 'mistral-nemo' not found`

**Solution:**
```bash
ollama pull mistral-nemo
```

### Import Errors

**Solution:** Ensure virtual environment is activated:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### tmux Session Already Exists

**Solution:**
```bash
tmux kill-session -t agentic-ai
./start_agents_tmux.sh
```

---

## 🤝 Contributing

Contributions welcome! Areas of interest:

- 🔭 **Observability tools** — visualize agent graphs and state
- 🧩 **Advanced A2A patterns** — negotiation, consensus protocols
- ⚙️ **New MCP tools** — database access, API integrations
- 🧠 **Model benchmarks** — performance comparisons
- 📚 **Documentation** — tutorials, examples, explanations

**How to contribute:**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a Pull Request

**Questions or ideas?** [Open an issue](https://github.com/JuanMaParraU/a2a-mcp-langgraph-agent-local/issues)

---

## 📖 Learn More

- **Blog Post:** [Building Fully Local Agentic AI](https://your-blog-link.com)
- **Source Code Details:** [src/ folder documentation](src/README.md)
- **LangGraph Docs:** [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/)
- **MCP Specification:** [Anthropic Model Context Protocol](https://www.anthropic.com/news/model-context-protocol)
- **Ollama:** [ollama.ai](https://ollama.ai)

---
## TODO 
- Dynamic agent skills retrieval and definition via MCP query
- Multi-agent workflows
- Multi-step workflows 

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

**Questions? Feedback?** Open an issue or reach out — I'd love to hear what you're building with this!

*Part of our exploration into accessible, open-source agentic AI infrastructure.*