import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from 2_a2a_executor import LangGraphAgentExecutor
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#A2A starlette APP/server
def main():
    skill = AgentSkill(
        id="online_search",
        name="DuckDuckGo search tool",
        description="Search the web using DuckDuckGo.",
        tags=["websearch","duckduckgo"],
        examples=["What's the current temperature in Bristol UK?"],
    )
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
#business card -> what an agent can do 
    agent_card = AgentCard(
        name="LangGraph Agent",
        description="A simple LangGraph agent that does web searchs",
        url="http://localhost:9998/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        version="1.0.0",     
        capabilities=capabilities,
        
    )

    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )

    uvicorn.run(server.build(), host="0.0.0.0", port=9998)


if __name__ == "__main__":
    main()