import asyncio
from urllib import response
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

async def main():
    client = MultiServerMCPClient(
        {
            "research": {
                "url": "http://localhost:8000/mcp/",  # ✅ Port matches your server
                "transport": "streamable_http",
            }
        }
    )

    tools = await client.get_tools()
    print("\n🔧 Available Tools:", [tool.name for tool in tools])
    # Use Ollama model (instruct-tuned)

    try:
        # Initialize the model
        model = ChatOllama(model="mistral-nemo")
        # Send a simple test prompt
        response = model.invoke("Hello!")
        print("✅ Model is reachable. Response:", response.content)
        model_name = response.response_metadata.get('model_name')
        print("Model name:", model_name)
        print("\n")
    except Exception as e:
        print("❌ Could not reach the model. Error:", str(e))

    # Create a React agent with the model and tools. This will allow the agent to use tools as needed. 
    # The agent will automatically handle tool calls and responses.
    # It will also handle the conversation history and context.
    # The agent will use the tools to answer the query.
    # The agent will also handle the conversation history and context.
    # It is langgraph's prebuilt React agent, which is designed to handle tool calls and responses.
    # The manual graph building and tool call handling developed in the main repo is abstracted by the create_react_agent function.
    system_prompt = """
    You are a smart research assistant that uses tools to find information. You can make multiple tool calls before answering.

    Available tools:
    - 'duckduckgo_search' — for general web search.
    - 'wikipedia_search' — for encyclopedia-style lookups.

    🚨 Tool Fallback Instructions (IMPORTANT):
    1. Always try 'duckduckgo_search' first.
    2. If it fails (e.g., "202 Ratelimit", "Network Error", or "No results"), do not give up, return ERROR fallbacking to other.
    3. Instead, rewrite the original query into a **Wikipedia-style title** and call 'wikipedia_search'.

    📘 Examples of Rewriting:
    - "top AI companies" → "Artificial intelligence companies"
    - "best telecom operator UK" → "Telecommunications in the United Kingdom"
    - "famous UK poets" → "British poets"

    4. Do NOT reuse the original query in Wikipedia.
    5. Always say which tool you used for your answer.

    🔁 You may use both tools if needed before answering.
    """
    config = {
    "configurable": {
        "thread_id": "research-session-1",  # Required
        "checkpoint_ns": "",
        "checkpoint_id": "research-session-1",  # Required
        }
    }
    agent = create_react_agent( model, 
                                tools, 
                                debug=False,
                                prompt=system_prompt, 
                                checkpointer=memory)
    query = "Use duckduckgo_search to find out what is the best telecom operator in the UK?"
    response = await agent.ainvoke({"messages": query}, config=config)
    final_ai_message = None
    for msg in reversed(response["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            final_ai_message = msg.content
        break
    print("🤖 Agent Response:\n", final_ai_message)
asyncio.run(main())


