import os
import logging
from langchain_ollama import ChatOllama
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langgraph.prebuilt import create_react_agent
from typing import Any, List, Literal
from langchain_core.messages import AIMessage, ToolMessage
from pydantic import BaseModel
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from collections.abc import AsyncIterable

os.environ["NO_PROXY"] = "127.0.0.1,localhost"

memory = MemorySaver()


# Define DuckDuckGo tool manually using the API wrapper

@tool(description="Search the web using DuckDuckGo.")
def duckduckgo_search(query: str) -> str:
    logging.info(f" 🔧🔧🔧 **** Called duckduckgo_search with: {query}")
    try:
        search = DuckDuckGoSearchAPIWrapper()
        results = search.run(query)
        if results:
            return {"result": results}
        else:
            return "No results found."
    except Exception as e:
        logging.error(f"Error occurred in duckduckgo_search: {str(e)}")
        return f"Error: {str(e)}"




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
        self.model = ChatOllama(model="gpt-oss", temperature= 0)
        self.tools = [duckduckgo_search]
        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            debug=True,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=ResponseFormat,
        )
    def invoke(self, query, context_id):
        config: RunnableConfig = {"configurable": {"thread_id": context_id}}
        self.graph.invoke({"messages": [("user", query)]}, config)
        return self.get_agent_response(config)
    
    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config: RunnableConfig = {"configurable": {"thread_id": context_id}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Trying to use the tool...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing the response from tool...",
                }

        yield self.get_agent_response(config)
    
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