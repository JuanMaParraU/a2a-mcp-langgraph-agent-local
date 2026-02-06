import uvicorn
import logging
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
# point executor orchestratoe
from o2_executor import OrchestratorExecutor
from metrics_middleware import MetricsMiddleware
from metrics import MetricsCollector
import threading
import time
import signal
import atexit
import json

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
    app = server.build()
    app.add_middleware(MetricsMiddleware)
    threading.Thread(target=log_metrics_periodically, daemon=True).start()
    # Catch Ctrl+C
    signal.signal(signal.SIGINT, lambda sig, frame: save_metrics_on_exit() or exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: save_metrics_on_exit() or exit(0))

    # Also save on normal exit
    atexit.register(save_metrics_on_exit)
    
    uvicorn.run(app, host="0.0.0.0", port=9990)
    
def log_metrics_periodically():
    metrics = MetricsCollector.get_instance()
    while True:
        time.sleep(30)
        metrics.log_summary()

def save_metrics_on_exit():
    metrics = MetricsCollector.get_instance()
    summary = metrics.summary()
    with open("metrics_log.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\n✅ Metrics saved to metrics_log.json")

if __name__ == "__main__":
    main()
