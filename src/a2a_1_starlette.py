import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a_2_executor import LangGraphAgentExecutor #invoke a2a Executor
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#A2A starlette APP/server
def main():
    skills = [
        AgentSkill(
            id="web_search",
            name="Web Search (DuckDuckGo)",
            description="Search the web using DuckDuckGo to find current information, news, and general knowledge.",
            tags=["websearch", "duckduckgo", "research", "internet"],
            examples=[
                "What's the current temperature in Bristol UK?",
                "Find recent news about quantum computing",
                "Search for the latest AI developments"
            ],
        ),
        AgentSkill(
            id="arxiv_search",
            name="Academic Paper Search (arXiv)",
            description="Search arXiv for academic papers and research publications in physics, mathematics, computer science, and related fields.",
            tags=["research", "papers", "arxiv", "academic", "science"],
            examples=[
                "Find recent papers on quantum computing",
                "Search for machine learning research from 2025",
                "What are the latest papers on neural networks?"
            ],
        ),
        AgentSkill(
            id="wikipedia_search",
            name="Wikipedia Search",
            description="Search Wikipedia for encyclopedic information, definitions, historical facts, and general knowledge on a wide range of topics.",
            tags=["wikipedia", "encyclopedia", "knowledge", "facts", "reference"],
            examples=[
                "What is quantum entanglement?",
                "Tell me about the history of the internet",
                "Explain what neural networks are"
            ],
        ),
    ]
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
#business card -> what an agent can do 
    agent_card = AgentCard(
        name="LangGraph Agent",
        description="A simple LangGraph agent that does web searchs",
        url="http://localhost:9998/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=skills,
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