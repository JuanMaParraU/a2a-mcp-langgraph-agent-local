from asyncio.log import logger
import os
import logging
from langchain_ollama import ChatOllama
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langgraph.prebuilt import create_react_agent
from typing import Any, List, Literal
from langchain_core.messages import AIMessage, ToolMessage
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from collections.abc import AsyncIterable
from langchain_mcp_adapters.client import MultiServerMCPClient

os.environ["NO_PROXY"] = "127.0.0.1,localhost"

memory = MemorySaver()

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class langG_agent:
    SYSTEM_INSTRUCTION = (
    """
        You are a smart research assistant. Use the search engine to look up information. \
        You are allowed to make multiple calls (either together or in sequence). \
        Only look up information when you are sure of what you want. \
        If you need to look up some information before asking a follow up question, you are allowed to do that! 
        Set response status to input_required if the user needs to provide more information.
        Set response status to error if there is an error while processing the request.
        Set response status to completed if the request is complete.
        """
    )

    def __init__(self):
        self.model = ChatOllama(model="mistral-nemo", temperature=0)
        self.tools = None
        self.graph = None
        self._initialized = False

    async def _initialize(self):
        """Initialize async components."""
        if not self._initialized:
            self.tools = await self._get_mcp_tools()
            self.graph = create_react_agent(
                self.model,
                tools=self.tools,
                checkpointer=memory,
                debug=True,
                prompt=self.SYSTEM_INSTRUCTION,
                response_format=ResponseFormat,
            )
            self._initialized = True    

    async def invoke(self, query, context_id):
        """Async invoke method."""
        await self._initialize()
        config: RunnableConfig = {"configurable": {"thread_id": context_id}}
        await self.graph.ainvoke({"messages": [("user", query)]}, config)
        return self.get_agent_response(config)

    """Token-by-token streaming method."""
    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        """Token-by-token streaming using astream_events."""
        await self._initialize()
        inputs = {"messages": [("user", query)]}
        config: RunnableConfig = {"configurable": {"thread_id": context_id}}

        current_tool = None
        
        try:
            async for event in self.graph.astream_events(inputs, config, version="v2"):
                kind = event["event"]
                
                # Stream individual LLM tokens
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": chunk.content,
                        }
                
                # Tool started
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    current_tool = tool_name
                    logger.info(f"Tool started: {tool_name}")
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": f"\n\n🔧 Using tool: {tool_name}\n",
                    }
                
                # Tool completed
                elif kind == "on_tool_end":
                    tool_name = event.get("name", current_tool or "unknown")
                    logger.info(f"Tool completed: {tool_name}")
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": f"✅ Tool {tool_name} completed\n\n",
                    }
                    current_tool = None
                
                # Errors
                elif kind == "on_chain_error":
                    error_msg = str(event.get("data", {}).get("error", "Unknown error"))
                    logger.error(f"Chain error: {error_msg}")
                    yield {
                        "is_task_complete": True,
                        "require_user_input": False,
                        "content": f"❌ Error: {error_msg}",
                    }
                    return
            
            yield self.get_agent_response(config)
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": f"❌ Streaming error: {str(e)}",
            }
    
    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get("structured_response")
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message,
                }
            if structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message,
                }
            if structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message,
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": (
                "We are unable to process your request at the moment. "
                "Please try again."
            ),
        }
    
    async def _get_mcp_tools(self):
        """Get tools from MCP server."""
        mcp_client = MultiServerMCPClient(
            {
                "research": {
                    "url": "http://localhost:8000/mcp/",
                    "transport": "streamable_http",
                }
            }
        )

        tools = await mcp_client.get_tools()
        print("\n🔧 Available Tools:", [tool.name for tool in tools])
        return tools