import asyncio
from urllib import response
from fastapi import logger
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
    
    print("\n🤖 Multi-turn MCP Agent ready! Type 'quit' or 'exit' to end the conversation.")
    print("Choose streaming mode:")
    print("  1. State-based streaming (complete messages)")
    print("  2. Token-by-token streaming (real-time)")
    print()
    
    stream_mode = input("Select mode (1 or 2, default=2): ").strip() or "2"
    use_token_streaming = stream_mode == "2"
    
    print(f"\n{'✨ Token-by-token' if use_token_streaming else '📦 State-based'} streaming enabled\n")
    
    while True:
        try:
            user_input = input("🔎 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\n🤖 Agent: ", end="", flush=True)
            
            if use_token_streaming:
                # TOKEN-BY-TOKEN STREAMING using astream_events
                async for event in agent.astream_events(
                    {"messages": user_input}, 
                    config=config, 
                    version="v2"
                ):
                    kind = event["event"]
                    
                    # Stream individual tokens
                    if kind == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            print(chunk.content, end="", flush=True)
                    
                    # Tool started
                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "unknown")
                        print(f"\n\n🔧 Using tool: {tool_name}...", end="", flush=True)
                    
                    # Tool completed
                    elif kind == "on_tool_end":
                        tool_name = event.get("name", "unknown")
                        print(f" ✅\n", end="", flush=True)
                
                print("\n")  # Newline after complete response
                
            else:
                # STATE-BASED STREAMING (original approach)
                last_content = ""
                async for event in agent.astream(
                    {"messages": user_input}, 
                    config=config, 
                    stream_mode="values"
                ):
                    messages = event.get("messages", [])
                    if messages:
                        last_msg = messages[-1]
                        
                        # Tool call indicator
                        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                            tool_names = ", ".join([tc["name"] for tc in last_msg.tool_calls])
                            print(f"\n🔧 Using tool: {tool_names}", flush=True)
                        
                        # Tool message indicator
                        elif isinstance(last_msg, ToolMessage):
                            print("📊 Processing results...", flush=True)
                        
                        # AI response
                        elif isinstance(last_msg, AIMessage) and last_msg.content:
                            if last_msg.content != last_content:
                                print(f"\n{last_msg.content}", flush=True)
                                last_content = last_msg.content
                
                print("\n")
                        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            logger.exception("Detailed error:")
            continue
asyncio.run(main())


