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
- **macOS, Linux, or Windows with WSL**

### Step 1: Install Ollama

Ollama lets you run powerful LLMs locally, eliminating API costs and latency.

**Install Ollama:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Start the Ollama server:**
```bash
ollama serve
```

**Download the model** (mistral-nemo with tool-calling support):
```bash
ollama run mistral-nemo
```

> **Why mistral-nemo?** It's instruct-tuned with strong tool-calling capabilities, making it ideal for agentic workflows.

### Step 2: Clone the Repository

```bash
git clone https://github.com/JuanMaParraU/a2a-mcp-langgraph-agent-local.git
cd a2a-mcp-langgraph-agent-local
```

### Step 3: Set Up Python Environment

**Option A: Using `uv` (recommended)** — faster dependency resolution:
```bash
uv sync  # creates .venv and installs dependencies automatically
source .venv/bin/activate
```

**Option B: Using standard venv:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Run Your First Agent

**Start with a simple single-agent example:**
```bash
python examples/single_agent.py
```

**Expected output:**
```
🤖 Agent initialized
📊 Processing task...
✅ Task completed: [result details]
```

---

## 📚 Examples

### Example 1: Single Agent with Tool Access

```bash
python examples/single_agent.py
```

Demonstrates:
- Basic LangGraph state management
- MCP tool integration (file reading)
- Local LLM reasoning via Ollama

### Example 2: Multi-Agent Collaboration (A2A)

```bash
python examples/multi_agent_a2a.py
```

Demonstrates:
- Two agents communicating via A2A protocol
- Task delegation between agents
- Shared state management

### Example 3: Custom MCP Tool

```bash
python examples/custom_mcp_tool.py
```

Demonstrates:
- Creating your own MCP-compatible tool
- Registering tools with the agent
- Tool discovery and execution

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

## 🔧 Configuration

### Changing the Model

Edit `config.yaml` to use different Ollama models:

```yaml
model:
  name: "llama3.2"  # or mistral, codellama, etc.
  temperature: 0.7
```

Available models: `ollama list`

### Adding MCP Tools

Create a new tool in `tools/`:

```python
from mcp import Tool

class MyCustomTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    
    async def execute(self, **kwargs):
        # Your tool logic here
        return result
```

Register it in `agent_config.py`:

```python
from tools.my_tool import MyCustomTool

tools = [MyCustomTool()]
```

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

**Solution:** Download the model first:
```bash
ollama pull mistral-nemo
```

### Out of Memory

**Error:** Process killed or memory errors

**Solution:** 
- Use a smaller model: `ollama pull llama3.2:3b`
- Reduce context window in `config.yaml`
- Close other applications

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'langgraph'`

**Solution:** Ensure virtual environment is activated and dependencies installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
ruff check .
```

### Adding New Agents

1. Create agent file in `agents/`
2. Define state schema
3. Implement reasoning logic
4. Register in LangGraph

See `agents/example_agent.py` for template.

---

## 🤝 Contributing

Contributions welcome! Areas we're particularly interested in:

- 🔭 **Observability tools** — visualize agent graphs and state
- 🧩 **Advanced A2A patterns** — negotiation, consensus protocols
- ⚙️ **New MCP tools** — database access, API integrations
- 🧠 **Model benchmarks** — performance comparisons for different tasks
- 📚 **Documentation** — tutorials, examples, explanations

**How to contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Submit a Pull Request

**Questions or ideas?** [Open an issue](https://github.com/JuanMaParraU/a2a-mcp-langgraph-agent-local/issues)

---

## 📖 Learn More

- **Blog Post:** [Building Fully Local Agentic AI](https://your-blog-link.com) — Architecture and concepts explained
- **LangGraph Docs:** [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/)
- **MCP Specification:** [Anthropic Model Context Protocol](https://www.anthropic.com/news/model-context-protocol)
- **Ollama:** [ollama.ai](https://ollama.ai)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) by LangChain
- [Ollama](https://ollama.ai) for local model serving
- MCP and A2A protocol specifications

---

**Questions? Feedback?** Open an issue or reach out — I'd love to hear what you're building with this!

*Part of our exploration into accessible, open-source agentic AI infrastructure.*