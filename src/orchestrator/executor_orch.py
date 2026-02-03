import logging
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TaskState, TextPart
from a2a.utils.errors import ServerError
from a2a.types import InternalError, UnsupportedOperationError
from agent_orch import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

class OrchestratorExecutor(AgentExecutor):
    """Wraps the Orchestrator agent for A2A execution."""

    def __init__(self):
        self.agent = Orchestrator()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("Executor.execute() called")

        # --- Context validation ---
        logger.debug(
            "Context received: task_id=%s context_id=%s has_message=%s",
            context.task_id,
            context.context_id,
            bool(context.message),
        )

        if not context.task_id or not context.context_id:
            logger.error("Missing task_id or context_id")
            raise ValueError("task_id and context_id required")

        if not context.message:
            logger.error("Missing message in context")
            raise ValueError("message required")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        # --- Task creation ---
        if not context.current_task:
            logger.info("Submitting new task: %s", context.task_id)
            await updater.submit()
        else:
            logger.info("Task already exists: %s", context.task_id)

        await updater.start_work()
        logger.info("Task %s set to WORKING", context.task_id)

        # --- Input handling ---
        query = context.get_user_input()
        logger.info("User query: %s", query)

        try:
            # --- Agent invocation ---
            logger.info("Invoking orchestrator agent")
            result = await self.agent.invoke(query, context.context_id)
            logger.info("Agent invocation completed")

            # --- Artifact creation ---
            content = result.get("content", "")
            logger.debug("Agent output length: %d", len(content))

            parts = [Part(root=TextPart(text=content))]
            await updater.add_artifact(parts, name="orchestrator result")
            logger.info("Artifact added to task %s", context.task_id)

            # --- Task completion ---
            await updater.complete()
            logger.info("Task %s COMPLETED", context.task_id)

        except Exception as e:
            logger.exception("Execution error during task %s", context.task_id)
            raise ServerError(error=InternalError()) from e


    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
