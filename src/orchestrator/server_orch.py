import uvicorn
import logging
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
# point executor orchestratoe
from executor_orch import OrchestratorExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    skills = [
        AgentSkill(
            id="planning",
            name="Planning",
            description="Decide whether to answer directly or delegate.",
            tags=["orchestration", "multi-agent"],
            examples=["Plan how to handle a user request"]
        ),
        AgentSkill(
            id="delegation",
            name="Delegation",
            description="Delegate tasks to other agents when necessary.",
            tags=["multi-agent", "orchestration"],
            examples=["Delegate research to another agent"]
        ),
    ]
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)

    agent_card = AgentCard(
        name="Orchestrator Agent",
        description="Coordinates multiple agents via A2A",
        url="http://localhost:9990/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=skills,
        version="1.0.0",
        capabilities=capabilities,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=OrchestratorExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )

    uvicorn.run(server.build(), host="0.0.0.0", port=9990)

if __name__ == "__main__":
    main()
