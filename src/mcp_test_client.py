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
        model = ChatOllama(model="mistral")  # ✅ Ensure the model is available locally
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
    system_prompt = """
    You are a smart research assistant that uses tools to find information. You can make multiple tool calls before answering.
    Use the tools to find accurate and relevant information.
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
    
    print("\n🤖 Multi-turn MCP Agent ready! Type 'quit' or 'exit' to end the conversation.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
                
            print("\nAgent: ", end="", flush=True)
            
            # Stream the agent's response
            async for event in agent.astream({"messages": user_input}, config=config, stream_mode="values"):
                messages = event.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if hasattr(last_msg, "content") and last_msg.content and isinstance(last_msg, AIMessage):
                        print(last_msg.content)
                        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue
asyncio.run(main())


